#!/usr/bin/env python3
"""檢查器的考卷 —— 已知陽性 + 已知陰性的固定語料,改了檢查器之後自動再比一次。

`PIPELINE.md` 每支檢查器的「驗過沒有」寫的是「對 N 份真實 run 驗過」—— 那是一次性的
手動比對,改了檢查器之後**沒有東西會自動再比一次**。幕五的定義「改了但沒重跑 = 沒閉環」,
對檢查器本身在這支之前做不到(票 25)。

考卷住 `fixtures/exams/<checker>/<case>/`:每個 case 一份輸入 + `expected.json`。
**已知陽性從真實 run 抽最小片段**,不複製整個 run 目錄;`expected.json` 釘**離開碼與字串**:

    {
      "args": ["run", "SPEC.md"],          # 傳給檢查器的參數,相對於 case 目錄;"{db}" 見下
      "store": ["glossary.yaml", "a.yaml"],  # 選填:先 spec_store import 成 store,填進 "{db}"
      "exit": 1,
      "must_print": ["…"],                 # 沒印 = 落空(漏抓)
      "must_not_print": ["…"],             # 印了 = 落空(不該標的標了)
      "false_positives": ["…"]             # 選填:**已知假陽性**,釘成「今天會印」——
                                           #   它印了才算命中,但報表把它單獨列成「假陽性」。
                                           #   修好那天這條會翻紅,到時改 expected,不是靜靜地過。
    }

三種結果,**不合併計數**:

* 命中 —— 離開碼對、該印的都印了、不該印的都沒印;
* 落空 —— 任何一項不符(報表逐條寫是哪一項);
* 假陽性 —— `false_positives` 裡今天仍然印得出來的那幾筆。它們**算命中**(考卷釘的是
  今天的行為),但單獨印、單獨數 —— 不然「52/60 標記、真陽性 0」那種佇列會被讀成綠燈。

「無考卷」佇列(ADR 0007 的那一半):`tools/harness/*_check.py` / `*_triage.py` 裡**沒有**
`fixtures/exams/<name>/` 的,列在最上面。**是佇列不是判決** —— 沒考卷不等於檢查器是錯的,
只是它改了之後沒有東西會替它再比一次。

離開碼:
    0  全部命中
    1  有落空(逐條印在表裡)
    2  用法錯誤(考卷根目錄不存在)
    3  **一個 case 都沒有** —— 不適用,不是通過(ADR 0005 §6)

用法:
    python3 exam.py [<exams_dir>]      # 預設 fixtures/exams
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXAMS = HERE / "fixtures" / "exams"
SPEC_STORE = HERE / "spec_store.py"

# 哪些 script 算「檢查器」——跟 PIPELINE.md 離開碼表的那一排對齊:`*_check.py` 與 `*_triage.py`。
# `acceptance_gwt.py` / `vacuous_tests.py` / `verify_generated.py` 也是檢查,但名字不在這個
# 形狀裡,這一版**不掃**;要納入就是改這一行,而改了這一行它們會出現在「無考卷」佇列。
CHECKER_GLOBS = ("*_check.py", "*_triage.py")


@dataclass
class Verdict:
    checker: str
    case: str
    expected_exit: int | None
    actual_exit: int | None
    misses: list[str] = field(default_factory=list)      # 落空的理由,逐條
    false_positives: list[str] = field(default_factory=list)  # 今天仍印得出來的已知假陽性

    @property
    def hit(self) -> bool:
        return not self.misses


def checkers(harness_dir: Path = HERE) -> list[str]:
    """`*_check.py` / `*_triage.py`,**扣掉測試檔** —— `test_landing_check.py` 也長這個形狀,
    第一次跑就把它列進「無考卷」佇列(25-RESULT.md)。"""
    names: set[str] = set()
    for pattern in CHECKER_GLOBS:
        names.update(p.stem for p in harness_dir.glob(pattern)
                     if not p.name.startswith("test_"))
    return sorted(names)


def discover(exams_dir: Path) -> list[tuple[str, Path]]:
    """(checker 名, case 目錄) 逐一,依名字排。只認有 `expected.json` 的目錄。"""
    out: list[tuple[str, Path]] = []
    if not exams_dir.is_dir():
        return out
    for checker_dir in sorted(p for p in exams_dir.iterdir() if p.is_dir()):
        for case_dir in sorted(p for p in checker_dir.iterdir() if p.is_dir()):
            if (case_dir / "expected.json").is_file():
                out.append((checker_dir.name, case_dir))
    return out


def no_exam_queue(exams_dir: Path, harness_dir: Path = HERE) -> list[str]:
    """有檢查器、沒考卷的。**佇列不是判決。**"""
    covered = {c for c, _ in discover(exams_dir)}
    return [c for c in checkers(harness_dir) if c not in covered]


def orphan_exams(exams_dir: Path, harness_dir: Path = HERE) -> list[str]:
    """有考卷、指不到檢查器的(script 改名 / 刪了,考卷還在)。這一種**是**落空。"""
    known = set(checkers(harness_dir))
    return sorted({c for c, _ in discover(exams_dir) if c not in known})


def _build_store(case_dir: Path, files: list[str], workdir: Path) -> tuple[Path | None, str]:
    db = workdir / "spec.db"
    cmd = [sys.executable, str(SPEC_STORE), "import",
           *(str(case_dir / f) for f in files), str(db)]
    done = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=False)
    if done.returncode != 0:
        return None, (done.stdout + done.stderr).strip()
    return db, ""


def run_case(checker: str, case_dir: Path, harness_dir: Path = HERE) -> Verdict:
    """跑一個 case。任何形狀不對的 expected.json 都記成落空,不炸 —— 炸了整張表就沒了。"""
    v = Verdict(checker, case_dir.name, None, None)
    try:
        exp = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        v.misses.append(f"expected.json 讀不出來:{exc}")
        return v
    if not isinstance(exp, dict) or not isinstance(exp.get("exit"), int) \
            or not isinstance(exp.get("args"), list):
        v.misses.append("expected.json 缺 exit(整數)或 args(list)")
        return v
    v.expected_exit = exp["exit"]

    script = harness_dir / f"{checker}.py"
    if not script.is_file():
        v.misses.append(f"考卷指不到檢查器:{script.name} 不存在")
        return v

    with tempfile.TemporaryDirectory() as tmp:
        db_path = None
        if exp.get("store"):
            db_path, err = _build_store(case_dir, exp["store"], Path(tmp))
            if db_path is None:
                v.misses.append(f"store 匯不進去(這是 fixture 壞了,不是檢查器落空):{err[:200]}")
                return v
        args = []
        for a in exp["args"]:
            if a == "{db}":
                if db_path is None:
                    v.misses.append("args 用了 {db} 但 expected.json 沒有 store")
                    return v
                args.append(str(db_path))
            else:
                args.append(str(case_dir / a))
        try:
            done = subprocess.run([sys.executable, str(script), *args], capture_output=True,
                                  text=True, encoding="utf-8", timeout=120, check=False)
        except subprocess.TimeoutExpired:
            v.misses.append("檢查器 120 秒沒回來")
            return v

    v.actual_exit = done.returncode
    out = done.stdout + done.stderr   # 用法錯誤只印在 stderr,兩邊一起比
    if done.returncode != exp["exit"]:
        v.misses.append(f"離開碼:預期 {exp['exit']}、實際 {done.returncode}")
    for s in exp.get("must_print", []):
        if s not in out:
            v.misses.append(f"該印沒印(漏抓):{s!r}")
    for s in exp.get("must_not_print", []):
        if s in out:
            v.misses.append(f"不該印卻印了:{s!r}")
    for s in exp.get("false_positives", []):
        if s in out:
            v.false_positives.append(s)
        else:
            v.misses.append(f"已知假陽性不見了(行為變了,去改 expected):{s!r}")
    return v


def run_all(exams_dir: Path = EXAMS, harness_dir: Path = HERE) -> list[Verdict]:
    return [run_case(c, d, harness_dir) for c, d in discover(exams_dir)]


def _fmt_exit(code: int | None) -> str:
    return "—" if code is None else str(code)


def main(argv: list[str]) -> int:
    if len(argv) > 2:
        print(__doc__, file=sys.stderr)
        return 2
    exams_dir = Path(argv[1]) if len(argv) == 2 else EXAMS
    if not exams_dir.is_dir():
        print(f"找不到考卷根目錄:{exams_dir}", file=sys.stderr)
        return 2

    print(f"\n=== 檢查器考卷:{exams_dir} ===")

    # ── 佇列印在最上面:有檢查器、沒考卷 ──────────────────────────────────
    queue = no_exam_queue(exams_dir, HERE)
    print(f"\n【無考卷】—— 佇列不是判決:改了它,沒有東西會替它再比一次(共 {len(queue)} 支)")
    for name in queue:
        print(f"  · {name}.py  → 缺 {exams_dir.name}/{name}/")
    if not queue:
        print("  (無)")

    verdicts = run_all(exams_dir, HERE)
    for name in orphan_exams(exams_dir, HERE):
        # 考卷指不到 script:run_case 對每個 case 已經記成落空,這裡只點名。
        print(f"\n  ❌ 考卷 {name}/ 指不到任何 {name}.py —— script 改名或刪了,考卷還在")

    if not verdicts:
        print("\n  ❌ **一個 case 都沒有 —— 這不是乾淨,是沒有考卷可跑。**")
        print("     **整份不適用,不是通過**(ADR 0005 §6)—— 離開碼 3。")
        return 3

    # ── 表:checker / case / 預期 / 實際 / 命中 ───────────────────────────
    cw = max(len("checker"), *(len(v.checker) for v in verdicts))
    kw = max(len("case"), *(len(v.case) for v in verdicts))
    print(f"\n{'checker':<{cw}}  {'case':<{kw}}  預期  實際  命中")
    print(f"{'-' * cw}  {'-' * kw}  ----  ----  ----")
    for v in verdicts:
        mark = "✅" if v.hit else "❌"
        fp = f"  (假陽性 {len(v.false_positives)} 筆,已知、釘住)" if v.false_positives else ""
        print(f"{v.checker:<{cw}}  {v.case:<{kw}}  {_fmt_exit(v.expected_exit):>4}  "
              f"{_fmt_exit(v.actual_exit):>4}  {mark}{fp}")
        for m in v.misses:
            print(f"{'':<{cw}}  {'':<{kw}}        ↳ 落空:{m}")

    hits = sum(1 for v in verdicts if v.hit)
    misses = len(verdicts) - hits
    fps = sum(len(v.false_positives) for v in verdicts)
    per_checker = {}
    for v in verdicts:
        per_checker.setdefault(v.checker, [0, 0])
        per_checker[v.checker][0 if v.hit else 1] += 1
    print(f"\n小計:{len(verdicts)} case;命中 {hits}、落空 {misses};"
          f"已知假陽性 {fps} 筆(釘住的,不是新發現)")
    for name, (h, m) in per_checker.items():
        print(f"  · {name}:{h + m} case,命中 {h}、落空 {m}")

    print("""
--- 這張考卷的上限(讀結論之前先看)---
* **命中 = 跟 expected.json 一樣**,不是「檢查器是對的」。已知假陽性是釘成「今天會印」的,
  它們命中只表示行為沒變 —— 表裡另外數,讀的人不要把那一欄算進乾淨。
* **字串比對釘的是報表措辭。** 檢查器改個說法、意思沒變,這裡也會紅 —— 那是要人去看的紅,
  不是檢查器壞了;確認之後改 expected.json。
* **考卷只有被抽進來的那幾個片段。** 真實 run 裡沒被抽的失效形狀,這裡量不到;
  「全部命中」不等於「四份真實 run 重跑也會一樣」。""")
    return 1 if misses else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
