#!/usr/bin/env python3
"""drift check —— 第十二題的丙:生成物進 git,build 期檢查它沒漂。

重新從 spec 生成一次,跟 commit 的內容比。不一樣就 fail。它同時擋兩條路:

  * agent 手改生成物         → 重新生成的結果跟 commit 的不一樣 → 紅
  * agent 改 spec 想放寬檢查 → 生成物跟 spec 不一致 → 紅
                                (它改 spec 又重新生成的話,diff 會出現在 git 裡,
                                 而生成物在凍結清單內 —— 收件驗證會抓到)

**這支 script 就是檢查本體,runtime 無關**(第十一題那條鐵律)。綁法各處不同:

    Gradle   tasks.register('verifyGenerated', Exec) { commandLine 'python3', … }
    CI       跑同一行
    Claude Code / Agent SDK   Stop hook 跑同一行
    Managed Agents            custom tool 或 Outcome rubric 的一條

⚠️ 目前**沒有**綁進 examples/shop/app/build.gradle —— 那個檔案逐位元組凍結。
   在那之前它是手動/hook 綁的,也就是**綁法還住第 4 階**。已知缺口,不要當成已經接上。

⚠️ **生成器不適用 ≠ 這些檔案通過**(2026-08-18 稽核那條紀律,票 14 補上)。
   在此之前,`gen_archunit.generate` 對「沒有 architecture_rule 的 store」
   `raise SystemExit(...)`,而這支是**把它 import 進來當函式呼叫**的 ——
   整支 drift check 被打死:stdout 一行都沒印、exit 1,而且那個 1 跟「生成物漂了」
   的 1 **長得一模一樣**。後果是:任何沒有架構規則的 store 都做不了 drift check,
   生成物有沒有被手改過**量不到**(票 10 的 P4 就是這樣落空的)。

   現在生成器改丟 `NothingToGenerate`,這支把它記成**不適用**,自成一類印在最上面,
   而且**照樣去比對其他生成器的產物** —— 缺一個生成器不該讓另外兩個也停擺。

   ⚠️ **同一種病 2026-08-19 又在同一支裡找到第二個(票 18)**:`gen_archunit`
   的 `_base_package` 對「有規則、但來源 package 推不出共同前綴」也是
   `raise SystemExit` —— 一樣把這支打死(stdout 0 byte、exit 1)。現在它也走
   `NothingToGenerate`,所以下面 `except NothingToGenerate` 這一條同時接住兩種
   成因:**沒有那類資料** 與 **資料有但生成參數決定不了**。

⚠️ **不適用而 commit 裡有那個檔 = 異常,不是不適用。** 把 spec 裡的架構規則刪光、
   再手寫一份 `ArchitectureTest.java` commit 進去 —— 若「不適用」一律放行,這條路
   就是靜默綠燈。所以:不適用的檔案**只要在 commit 裡存在**,就報異常、離開碼 1。

離開碼:
    0  比對過了,而且沒漂(有生成器不適用、但它的檔案也不在 commit 裡 —— 允許)
    1  **有漂移**,或**不適用的生成物卻在 commit 裡**(沒有 spec 撐著的生成物)
    2  用法錯誤:參數個數不對 / `generated_dir` 不存在 / spec 沒過驗證
       ——「吃錯目錄」絕不准用 1,不然它會被讀成「生成物全漂了」:
       檢查根本沒跑,卻回報了它存在的理由那個結論
       (跟 `package_landing_check.scan_sources` 同一條分界)
    3  **整份不適用** —— 每一個生成器都不適用(沒東西可生成,或有東西而生成參數
       決定不了),這次一個檔都沒比對到。
       不是通過。(但若同時有「不適用卻在 commit 裡」的檔案,那是**查到東西了**,
        而且是壞消息 → 1 蓋過 3。)

用法:
    python3 verify_generated.py <generated_dir> <spec.yaml> [<spec2.yaml> …]
"""

from __future__ import annotations

import difflib
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from gen_acceptance import generate as gen_acceptance  # noqa: E402
from gen_archunit import generate as gen_archunit  # noqa: E402
from spec_store import NothingToGenerate, SpecError, build_store, load_specs  # noqa: E402

# 加新生成器就在這裡加一列 —— 否則它的生成物不會被 drift check 蓋到,
# 而「沒被蓋到的生成物」正是這支 script 存在的理由。
#
# 一個生成器可以產**多個**檔案:第一個是它的呼叫參數,其餘是兄弟檔。
# gen_acceptance 從 2026-08-18 起把代理編碼的情境分到另一個 class ——
# 那個檔案也必須被 drift check 蓋到,否則手改它不會被抓到。
GENERATORS = [
    (gen_archunit, ["ArchitectureTest.java"]),
    (gen_acceptance, ["OrderAcceptanceTest.java", "OrderProxyAcceptanceTest.java"]),
]


class UsageError(Exception):
    """呼叫方式錯了 / 目錄不見 —— **錯誤,不是不適用**(離開碼 2)。

    刻意**不**用 `SystemExit`:這支自己就是被 `SystemExit` 從函式裡炸出來害到的
    那個呼叫方,不該對它的呼叫方再做一次同樣的事。
    """


@dataclass
class Result:
    """比對結果。**三類分開裝,不准折成一類。**

    * `drift`          —— 真的比對過的檔:檔名 → diff 行(空 list = 沒漂)
    * `not_applicable` —— 生成器沒東西可生成,這些檔**這次沒有被檢查過**:檔名 → 原文理由
    * `unbacked`       —— `not_applicable` 之中**commit 裡卻有這個檔**的:異常,要紅
    """

    drift: dict[str, list[str]] = field(default_factory=dict)
    not_applicable: dict[str, str] = field(default_factory=dict)
    unbacked: list[str] = field(default_factory=list)


def verify(generated_dir: str | Path, spec_paths: list[str | Path]) -> Result:
    """重生一份到 temp,跟 `generated_dir` 裡 commit 的比。"""
    generated_dir = Path(generated_dir)
    if not generated_dir.is_dir():
        # ⚠️ 離開碼**必須是 2,不是 1**。目錄不在的時候,每個檔案都「commit 的是空的、
        #    重新生成的有內容」→ 舊版會逐檔印出滿滿的 diff 並喊「生成物漂了」,
        #    exit 1 —— **吃錯路徑偽裝成最嚴重的那個結論**。
        raise UsageError(
            f"找不到 {generated_dir} —— 這支要吃**放生成物的目錄**"
            "(例:.../src/test/java/acceptance),不是 spec 檔"
        )
    result = Result()
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "spec.db"
        build_store(db, load_specs(list(spec_paths)))
        for generator, filenames in GENERATORS:
            try:
                generator(db, Path(tmp) / filenames[0])
            except NothingToGenerate as exc:
                # 不適用:這幾個檔這一次**沒有被檢查過**。不折進通過,也不折進錯誤。
                for filename in filenames:
                    result.not_applicable[filename] = str(exc)
                    if (generated_dir / filename).exists():
                        # commit 裡有,而這份 spec 生不出來 → 這個檔沒有 spec 撐著。
                        result.unbacked.append(filename)
                continue
            for filename in filenames:
                fresh = Path(tmp) / filename
                # 該生成的沒生 = 這份 spec 沒有那類情境;committed 也該不存在。
                # (這一條是**比對過的**:生成器適用,只是這個兄弟檔是空的。)
                expected = fresh.read_text(encoding="utf-8") if fresh.exists() else ""
                committed = generated_dir / filename
                actual = committed.read_text(encoding="utf-8") if committed.exists() else ""
                result.drift[filename] = (
                    []
                    if actual == expected
                    else list(
                        difflib.unified_diff(
                            actual.splitlines(keepends=True),
                            expected.splitlines(keepends=True),
                            fromfile=f"{committed} (commit 的)",
                            tofile="重新生成的",
                        )
                    )
                )
    return result


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        res = verify(argv[1], argv[2:])
    except UsageError as exc:
        print(exc, file=sys.stderr)
        return 2
    except SpecError as exc:
        # 2 而不是 1:spec 自己沒過驗證,**這支根本沒跑起來**。跟「生成物漂了」
        # 共用 1 的話,「spec 寫壞了」看起來就會像「有人手改了生成物」。
        # (`package_landing_check` 對同一個條件也是回 2。)
        print("spec 本身沒過驗證,無從比對:", file=sys.stderr)
        for problem in exc.problems:
            print(f"  - {problem}", file=sys.stderr)
        return 2

    # ── 不適用印在最上面,自成一類(ADR 0005 §6)────────────────────────
    if res.not_applicable:
        print("【不適用】—— 不是通過,這幾個生成物這次沒有被檢查過")
        for name, reason in res.not_applicable.items():
            mark = "❌" if name in res.unbacked else "◻"
            print(f"  {mark} {name} —— {reason}")
        if res.unbacked:
            print(f"\n  ⚠️ **上面標 ❌ 的檔案在 commit 裡存在,而這份 spec 生不出它們**"
                  f"({'、'.join(res.unbacked)})——")
            print("     它們沒有 spec 撐著:可能是從別份規格繼承來的、可能是手寫的,"
                  "也可能是規格本身決定不了生成參數(理由印在上面那一行)。")
            print("     drift check 對它們**永遠不會紅**,所以這裡當場吵。")
        print()

    for name, d in res.drift.items():
        print(f"  {'❌' if d else '✅'} {name}")

    bad = {name: d for name, d in res.drift.items() if d}
    if bad:
        print("\n生成物漂了 —— 要改就改 spec 並重新生成,不要手改生成物:", file=sys.stderr)
        for name, d in bad.items():
            print(f"--- {name}", file=sys.stderr)
            sys.stderr.writelines(d[:40])
        return 1
    if res.unbacked:
        return 1
    if not res.drift:
        # 「找不到東西所以沒問題」是最廉價的假綠燈。
        print("  ❌ **一個生成物都沒比對到 —— 這不是乾淨,是每個生成器都不適用。**")
        print("     **整份不適用,不是通過**(ADR 0005 §6)—— 離開碼 3,"
              "跟「有漂移」(1)、「吃錯目錄」(2)分得開。")
        return 3
    print("ok: 生成物與 spec 一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
