#!/usr/bin/env python3
"""驗收生成器的驗收 —— **兩側都要驗**,加上逐條可紅。

第一個生成器(ArchUnit)的驗收是「綠 ＋ 逐條可紅」。驗收測試不一樣:
它在**空骨架上必須是紅的**(還沒有實作),所以純粹「跑得綠」反而是壞消息。
三段:

  1. **空骨架 → 5/5 紅**   證明它不是恆真(骨架沒有實作,不該有東西會過)
  2. **OL1 實作 → 5/5 綠** 證明它可滿足(而且那份實作從沒看過生成的這一版)
  3. **逐條可紅**          在 OL1 上做最小破壞,只有對應那條該變紅

第 2 段特別值錢:OL1 是**別人寫的實作**(輪 1 分層實驗的產物),對著凍結的
那份手寫驗收跑綠。生成的這一版如果也綠,表示兩份驗收在行為上等價
—— 那比逐位元組比對 Java 有意義得多。

不動任何凍結檔:每輪都從 git 取出到 scratch 再改。

離開碼:
    0  三段都跑到了,而且都通過
    1  有項目未通過
    2  用法錯誤(參數個數不對 / 生成物裡找不到任何 `scenario_*`)
    3  **有項目不適用** —— 跑到的都通過,但至少一段沒跑。不是通過。
       (合約對不上 → 第 2、3 段不適用;有代理編碼的情境被排除在驗收之外。)

用法:
    python3 acceptance_gwt.py <generated/OrderAcceptanceTest.java> <workdir>
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TEST_REL = "examples/shop/app/src/test/java/acceptance/OrderAcceptanceTest.java"
GOOD_BRANCH = "layered/OL1-integration"
FROZEN = "4567d31"

QUERY_REPO = "src/main/java/com/shop/adapter/JdbcOrderQueryRepository.java"
CONTROLLER = "src/main/java/com/shop/adapter/OrderController.java"

# 情境 → (檔案, 找, 換, 預期變紅的集合)。每個都是最小破壞,只碰一個地方。
BREAKS: dict[str, tuple[str, str, str, set[str]]] = {
    # S1 的 201 被所有情境共用(其他情境都要先 orderIdOf 才拿得到 id,而它斷言 201)
    # —— 所以破壞它會全紅。這跟 A6 被 A1 蓋住是同一種現象,不是 bug。
    "S1": (
        CONTROLLER,
        "ResponseEntity.status(HttpStatus.CREATED)",
        "ResponseEntity.status(org.springframework.http.HttpStatus.OK)",
        {"S1", "S2", "S3", "S4", "S5"},
    ),
    "S2": (
        QUERY_REPO,
        'OrderStatus.valueOf(rs.getString("status"))',
        "OrderStatus.DRAFT",
        {"S2"},
    ),
    "S3": (
        QUERY_REPO,
        "COALESCE(c.name, o.customer_id)",
        "o.customer_id                             ",
        {"S3"},
    ),
    "S4": (
        QUERY_REPO,
        "SUM(i.quantity * i.unit_price_cents)",
        "SUM(i.unit_price_cents)             ",
        {"S4"},
    ),
    "S5": (
        QUERY_REPO,
        "placedAt == null ? null : placedAt.toLocalDate()",
        "null",
        {"S5"},
    ),
}


def stage(generated: Path, workdir: Path, label: str, branch: str) -> Path:
    """從 git 取出某個 ref 的 app/,換上生成的驗收測試。"""
    target = workdir / label
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    archive = subprocess.run(
        ["git", "archive", branch, "examples/shop/app"],
        cwd=REPO, capture_output=True, check=True,
    )
    subprocess.run(["tar", "-x"], cwd=target, input=archive.stdout, check=True)
    app = target / "examples/shop/app"
    (app / "src/test/java/acceptance/OrderAcceptanceTest.java").write_text(
        generated.read_text(encoding="utf-8"), encoding="utf-8"
    )
    # 架構測試不是這輪要驗的東西,拿掉以免干擾判讀
    arch = app / "src/test/java/architecture/ArchitectureTest.java"
    if arch.exists():
        arch.unlink()
    return app


def run_tests(app: Path, ids: list[str]) -> dict[str, str]:
    subprocess.run(
        ["./gradlew", "test", "--tests", "acceptance.OrderAcceptanceTest",
         "--offline", "--console=plain", "-q"],
        cwd=app, capture_output=True, text=True,
    )
    results: dict[str, str] = {}
    for xml in (app / "build/test-results/test").glob("TEST-*.xml"):
        root = ET.parse(xml).getroot()
        # 整個類別起不來(空骨架的 Spring context)會變成一筆 initializationError
        for case in root.iter("testcase"):
            name = (case.get("name") or "").removesuffix("()")
            failed = any(c.tag in {"failure", "error"} for c in case)
            match = re.match(r"scenario_(\w+)$", name) or re.match(r"^(\w+):", name)
            if match and match.group(1) in ids:
                results[match.group(1)] = "failed" if failed else "passed"
            elif failed:
                # 類別層級就爆了(空骨架的 Spring context)→ 每條情境都算紅
                for sid in ids:
                    results.setdefault(sid, "failed")
    return results


FROZEN_CONTRACT = "shop-frozen-v1"


def contract_of(generated: Path) -> str | None:
    """生成物綁的是哪份 wire 合約 —— 生成器把合約名寫進 helper 的註解。

    從生成物讀而不是從 store 讀,理由跟 `scenario_ids` 一樣:
    這支工具驗的是**生成物**,別人交的生成物也要驗得動。
    """
    match = re.search(r"wire 合約「(.+?)」", generated.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def scenario_ids(generated: Path) -> list[str]:
    """情境 id 從生成物讀,不寫死 —— 這樣別人交的 spec 也驗得動。"""
    return sorted(set(re.findall(r"void scenario_(\w+)\(", generated.read_text(encoding="utf-8"))))


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    generated, workdir = Path(argv[1]).resolve(), Path(argv[2]).resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    ids = scenario_ids(generated)
    if not ids:
        print("生成物裡找不到任何 scenario_* 方法", file=sys.stderr)
        return 2
    verdicts: list[tuple[str, bool | None, str]] = []

    # 代理編碼的情境在另一個 class(2026-08-18)。這支工具**只驗真情境** ——
    # 但要把排除掉幾條講出來,悶著不說跟混在一起算一樣糟:
    # 落檔 12 條、驗收只驗 8 條,那個差距就是還沒補上的動詞缺口。
    proxy_file = generated.parent / "OrderProxyAcceptanceTest.java"
    if proxy_file.exists():
        proxy_ids = sorted(set(re.findall(r"void scenario_(\w+)\(",
                                          proxy_file.read_text(encoding="utf-8"))))
        verdicts.append((
            "代理編碼(不列入驗收)", None,
            f"⏭️ {len(proxy_ids)} 條在 OrderProxyAcceptanceTest:{proxy_ids} "
            f"—— 綠了不代表原文成立,缺口見 .scratch/ddd-harness/issues/01",
        ))

    # 1. 空骨架 → 全紅
    res = run_tests(stage(generated, workdir, "skeleton", FROZEN), ids)
    reds = {k for k, v in res.items() if v == "failed"}
    verdicts.append(
        (f"空骨架 → {len(ids)}/{len(ids)} 紅", reds == set(ids), f"紅的是 {sorted(reds)}")
    )

    # 2. OL1 實作 → 全綠 —— **只有宣告同一份 wire 合約的 spec 才適用**(ADR 0004)。
    #
    # OL1 是照 shop-frozen-v1 那組欄位名寫的。別的 spec 自己宣告了別的合約,
    # 對著它跑一定全紅,而那個紅**不是失敗,是不適用**。
    # ⚠️ 這一段以前印 `❌ OL1 → 4/4 綠  綠的是 []`,讀起來像壞了 ——
    #    而壞掉的東西會被拿去修。報表把「不適用」渲染成「失敗」,跟舊的 transcript
    #    把「送掉了」渲染成「談完了」是同一種病。所以這裡要印得出第三種結果。
    contract = contract_of(generated)
    if contract != FROZEN_CONTRACT:
        verdicts.append((
            f"{GOOD_BRANCH} → 全綠",
            None,
            f"⏭️ 不適用:這份 spec 綁的是 {contract!r},OL1 實作的是 "
            f"{FROZEN_CONTRACT!r} —— 可滿足性要由第四幕證明",
        ))
    else:
        good = stage(generated, workdir, "good", GOOD_BRANCH)
        res = run_tests(good, ids)
        greens = {k for k, v in res.items() if v == "passed"}
        verdicts.append(
            (f"{GOOD_BRANCH} → {len(ids)}/{len(ids)} 綠", greens == set(ids),
             f"綠的是 {sorted(greens)}")
        )

    # 3. 逐條可紅 —— 只跑得動我們有破壞點的情境。
    # BREAKS 的 key 綁的是**凍結那份 spec 的語意**(S3 = customerName 的 join、
    # S4 = 加總、S5 = ISO 日期)。換一份 spec,S1–S5 會**撞名不撞義** ——
    # 跑出來的任何結果都不算數。所以先擋在合約上,不要產生看似有意義的數字。
    breakable = [s for s in ids if s in BREAKS] if contract == FROZEN_CONTRACT else []
    if contract != FROZEN_CONTRACT:
        verdicts.append((
            "逐條可紅", None,
            f"⏭️ 不適用:BREAKS 綁 {FROZEN_CONTRACT!r} 的情境語意,換 spec 會撞名不撞義",
        ))
    for sid in breakable:
        rel, find, replace, expected = BREAKS[sid]
        app = stage(generated, workdir, f"break-{sid}", GOOD_BRANCH)
        path = app / rel
        source = path.read_text(encoding="utf-8")
        if find not in source:
            verdicts.append((f"{sid} 破壞點", False, f"在 {rel} 找不到 {find!r}"))
            continue
        path.write_text(source.replace(find, replace, 1), encoding="utf-8")
        res = run_tests(app, ids)
        reds = {k for k, v in res.items() if v == "failed"}
        verdicts.append(
            (f"{sid} 破壞 → 紅的正好是 {sorted(expected)}", reds == expected, f"實際 {sorted(reds)}")
        )

    # 三態:過 / 沒過 / **不適用**。
    # `passed is None` = 不適用 —— 它不算失敗,也**不算通過**。
    # 結論句要把它講出來,否則「1 過 2 不適用」會被讀成「全部通過」,
    # 而那正是這輪要拿掉的那種報表。
    print("\n=== 驗收生成器的驗收 ===")
    failed = [v for v in verdicts if v[1] is False]
    skipped = [v for v in verdicts if v[1] is None]
    for name, passed, detail in verdicts:
        icon = "⏭️" if passed is None else ("✅" if passed else "❌")
        print(f"  {icon} {name:34} {detail}")
    if failed:
        print("=== 有項目未通過 ===")
        return 1
    if skipped:
        print(f"=== 跑到的都通過,但有 {len(skipped)} 項不適用 —— "
              f"**這不等於驗收通過** ===")
        # 報表分得開、離開碼分不開,等於只有讀報表的人知道 —— 自動化一律讀成綠。
        # 離開碼 3 = **有項目不適用,不是通過**(ADR 0005 §6),跟「有項目未通過」(1)、
        # 「用法錯誤」(2)分得開。
        # ⚠️ 這支的 3 是「**部分**不適用」:三段裡任何一段 ⏭️ 就回 3。
        #    `landing_check` / `verify_generated` / `package_landing_check` 的 3 是
        #    「**整份**不適用」。同一個碼、兩種粒度 —— 這支的三段各自獨立,沒有
        #    「整份」可言,所以沒有照那三支的形狀。讀離開碼的人要知道這個差別。
        return 3
    print("=== 全部通過 ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
