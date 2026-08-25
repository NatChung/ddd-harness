#!/usr/bin/env python3
"""不適用比率儀表 —— 「守衛靜靜不再適用」要有人在看,這支就是那個人(票 26)。

五支檢查器各自誠實印「不適用」(離開碼 3),但連續十跑都不適用,今天沒人會注意:
「不適用」被看見的前提是有人在看。這支讀各 run 的 `check-ledger.jsonl`(票 21 的
`check.py` 寫的),按檢查器跨跑統計,超過門檻印 ⚠️。

**它是儀表,不是閘門。** 離開碼只有 0 / 2 / 3,門檻超過只印警告、不回 1;升成閘門要另開票。

輸入:`<root>` 底下所有 `check-ledger.jsonl`(遞迴,略過 `.` 開頭與 `build/` 目錄)。
`runs/<name>` 形狀的目錄裡**沒有**帳本的,是票 21 之前的舊 run:只印張數,不進分母。
帳本每行照 `check.py` 的形狀讀 `{"checker","argv","exit","ts","cwd"}`;**格式歸票 21,
這裡只讀**。讀不動的行(不是 JSON / 缺 checker / exit 不是整數)跳過並計數印出,不 crash。

表:列 = 檢查器,欄 =
    跑過    帳本裡這支的筆數
    0/1/3   離開碼各幾筆(其他碼 —— 2 用法錯誤、炸掉的 66 之類 —— 歸「其他」)
    skip    **推斷**:`run-meta.json` 有 `gate_skipped: true` 的跑,依那跑是哪一幕
            (`skeleton` → act4、`spec_db` → act3、`spec` → act2,從欄位形狀推)對到
            `check.GATES` 裡該幕要求的檢查器。分不出哪一幕的另外計數印出。
    不適用率  3 ÷ 跑過
    連續不適用  依 `ts` 排序後,最近的一段連續 exit 3 有幾筆

門檻:`--warn-threshold 0.25 --min-runs 5`(預設)—— 跑過 ≥ min-runs 且不適用率 **>** 門檻
才印 ⚠️。形狀抄 Harmonist 的 `PROTOCOL-SKIP`(survey §3 第 17 條,只讀 README 的宣稱),
門檻沒量過,是起手值。

離開碼:
    0  有帳本、算完了(⚠️ 也是 0 —— 儀表不擋)
    2  用法錯誤(沒給 root / root 不是目錄 / 參數壞)
    3  **不適用**:一份帳本都沒有,或帳本裡一筆都讀不動 —— 沒東西可統計,不是乾淨

用法:
    python3 na_ratio.py [--brief] [--checker <name>] [--warn-threshold 0.25] [--min-runs 5] <root> [<root>…]
        --brief     只印一行(runner 開頭用):「上 N 跑 landing_check 不適用 M 次」
        --checker   只看這一支(runner 各幕只關心自己閘門那支)
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check import GATES, LEDGER_NAME  # noqa: E402  只借常數:帳本檔名、各幕要哪幾支

META_NAME = "run-meta.json"
DEFAULT_THRESHOLD = 0.25
DEFAULT_MIN_RUNS = 5
SKIP_DIRS = ("build",)


class UsageError(Exception):
    pass


@dataclass
class Entry:
    checker: str
    exit: int
    ts: str
    source: str  # 哪份帳本(印用)


@dataclass
class Stats:
    checker: str
    entries: list[Entry] = field(default_factory=list)
    skipped: int = 0  # 推斷:閘門被 ACT_GATE_SKIP 跳過、而那幕要求這支

    @property
    def runs(self) -> int:
        return len(self.entries)

    def count(self, code: int) -> int:
        return sum(1 for e in self.entries if e.exit == code)

    @property
    def other(self) -> int:
        return sum(1 for e in self.entries if e.exit not in (0, 1, 3))

    @property
    def na_ratio(self) -> float:
        return self.count(3) / self.runs if self.runs else 0.0

    @property
    def na_streak(self) -> int:
        """最近的一段連續不適用。`ts` 缺的排最前(當最舊),同 ts 保檔案順序。"""
        ordered = sorted(self.entries, key=lambda e: e.ts)
        n = 0
        for e in reversed(ordered):
            if e.exit != 3:
                break
            n += 1
        return n

    def over(self, threshold: float, min_runs: int) -> bool:
        return self.runs >= min_runs and self.na_ratio > threshold


@dataclass
class Report:
    ledgers: list[Path] = field(default_factory=list)
    old_runs: list[Path] = field(default_factory=list)        # runs/<name> 沒帳本
    stats: dict[str, Stats] = field(default_factory=dict)
    unreadable: dict[str, int] = field(default_factory=dict)  # 帳本路徑 → 讀不動幾行
    skips_unmapped: int = 0                                   # gate_skipped 但分不出哪一幕
    skips_total: int = 0

    @property
    def entries(self) -> int:
        return sum(s.runs for s in self.stats.values())

    @property
    def unreadable_total(self) -> int:
        return sum(self.unreadable.values())


# ── 掃 ───────────────────────────────────────────────────────────────


def _walk(root: Path):
    """遞迴列目錄,略過 `.` 開頭與 SKIP_DIRS。回傳目錄本身(含 root)。"""
    stack = [root]
    while stack:
        d = stack.pop()
        yield d
        try:
            children = sorted(p for p in d.iterdir() if p.is_dir())
        except OSError:
            continue
        for c in children:
            if c.name.startswith(".") or c.name in SKIP_DIRS:
                continue
            stack.append(c)


def find_ledgers(root: Path) -> tuple[list[Path], list[Path]]:
    """回 (帳本路徑, 沒帳本的 runs/<name> 目錄)。兩邊都排好序。"""
    ledgers: list[Path] = []
    old: list[Path] = []
    for d in _walk(root):
        if (d / LEDGER_NAME).is_file():
            ledgers.append(d / LEDGER_NAME)
        elif d.parent.name == "runs":
            old.append(d)
    return sorted(ledgers), sorted(old)


def read_ledger_lossy(path: Path) -> tuple[list[Entry], int]:
    """照 check.py 的形狀讀;讀不動的行跳過並計數。整個檔讀不到 = 全部算讀不動(1 筆)。"""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return [], 1
    out: list[Entry] = []
    bad = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            bad += 1
            continue
        if not isinstance(obj, dict) or not isinstance(obj.get("checker"), str) \
                or isinstance(obj.get("exit"), bool) or not isinstance(obj.get("exit"), int):
            bad += 1
            continue
        ts = obj.get("ts")
        out.append(Entry(obj["checker"], obj["exit"], ts if isinstance(ts, str) else "", str(path)))
    return out, bad


def infer_act(meta: dict) -> str | None:
    """從 run-meta.json 的欄位形狀推這跑是哪一幕。**推斷**:runner 沒寫 act 欄位。
    先看 skeleton(act4 也有 spec + input_blobs),再 spec_db(act3),最後 spec(act2)。"""
    if "skeleton" in meta:
        return "act4"
    if "spec_db" in meta:
        return "act3"
    if "spec" in meta:
        return "act2"
    return None


def read_skips(ledger_dir_parent: Path) -> tuple[list[str], int]:
    """這個 run 目錄的 run-meta.json 若 gate_skipped: true,回被跳過那幕要求的檢查器名。
    回 (檢查器名清單, 分不出幕的數量 0/1)。讀不到 / 不是 JSON / 沒標 = 沒跳。"""
    path = ledger_dir_parent / META_NAME
    if not path.is_file():
        return [], 0
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return [], 0
    if not isinstance(meta, dict) or meta.get("gate_skipped") is not True:
        return [], 0
    act = infer_act(meta)
    if act is None:
        return [], 1
    return [checker for checker, _first, _must in GATES[act]], 0


def collect(roots: list[Path]) -> Report:
    r = Report()
    seen_dirs: set[Path] = set()
    for root in roots:
        ledgers, old = find_ledgers(root)
        r.ledgers.extend(l for l in ledgers if l.parent not in seen_dirs)
        r.old_runs.extend(o for o in old if o not in seen_dirs)
        seen_dirs.update(l.parent for l in ledgers)
        seen_dirs.update(old)
    for ledger in r.ledgers:
        entries, bad = read_ledger_lossy(ledger)
        if bad:
            r.unreadable[str(ledger)] = bad
        for e in entries:
            r.stats.setdefault(e.checker, Stats(e.checker)).entries.append(e)
    # skip(推斷):有帳本的跑與舊跑都看 —— 跳閘門的那跑自己可能一筆檢查都沒記
    for d in sorted(set(l.parent for l in r.ledgers) | set(r.old_runs)):
        names, unmapped = read_skips(d)
        if names or unmapped:
            r.skips_total += 1
        r.skips_unmapped += unmapped
        for name in names:
            r.stats.setdefault(name, Stats(name)).skipped += 1
    return r


# ── 印 ───────────────────────────────────────────────────────────────


def _selected(r: Report, checker: str | None) -> list[Stats]:
    rows = [s for s in r.stats.values() if s.runs or s.skipped]
    if checker is not None:
        rows = [s for s in rows if s.checker == checker]
    return sorted(rows, key=lambda s: s.checker)


def warnings(r: Report, threshold: float, min_runs: int, checker: str | None = None) -> list[str]:
    out = []
    for s in _selected(r, checker):
        if s.over(threshold, min_runs):
            out.append(f"⚠️ {s.checker}:{s.runs} 跑裡不適用 {s.count(3)} 次"
                       f"({s.na_ratio:.0%} > {threshold:.0%},門檻 ≥ {min_runs} 跑才算)"
                       f",最近連續 {s.na_streak} 次 —— 守衛可能已經靜靜不再適用")
    return out


def brief_line(r: Report, threshold: float, min_runs: int, checker: str | None) -> str:
    """一行,runner 開頭印。沒帳本也要講清楚是「不適用」,不是乾淨。"""
    n_old = len(r.old_runs)
    if not r.ledgers or not r.entries:
        why = "沒有任何 check-ledger.jsonl" if not r.ledgers else \
              f"{len(r.ledgers)} 份帳本一筆都讀不動"
        return f"na_ratio:不適用 —— {why}(舊 run {n_old} 張沒帳本,不進分母)"
    rows = _selected(r, checker)
    if not rows:
        return (f"na_ratio:上 {len(r.ledgers)} 跑沒有 {checker} 的紀錄"
                f"(帳本 {len(r.ledgers)} 份;舊 run {n_old} 張沒帳本)")
    parts = []
    for s in rows:
        mark = "⚠️ " if s.over(threshold, min_runs) else ""
        skip = f",閘門跳過 {s.skipped} 次(推斷)" if s.skipped else ""
        parts.append(f"{mark}上 {s.runs} 跑 {s.checker} 不適用 {s.count(3)} 次"
                     f"(連續 {s.na_streak}{skip})")
    tail = f";舊 run {n_old} 張沒帳本" if n_old else ""
    bad = f";讀不動 {r.unreadable_total} 行" if r.unreadable_total else ""
    return "na_ratio:" + ";".join(parts) + tail + bad


def render_table(r: Report, threshold: float, min_runs: int, checker: str | None) -> list[str]:
    rows = _selected(r, checker)
    lines = []
    cw = max([len("檢查器")] + [len(s.checker) for s in rows])
    head = f"{'檢查器':<{cw}}  跑過    0    1    3  其他  skip  不適用率  連續不適用"
    lines.append(head)
    lines.append(f"{'-' * cw}  ----  ---  ---  ---  ----  ----  --------  ----------")
    for s in rows:
        mark = " ⚠️" if s.over(threshold, min_runs) else ""
        ratio = f"{s.na_ratio:>7.0%}" if s.runs else "      —"
        lines.append(f"{s.checker:<{cw}}  {s.runs:>4}  {s.count(0):>3}  {s.count(1):>3}  "
                     f"{s.count(3):>3}  {s.other:>4}  {s.skipped:>4}  {ratio}   "
                     f"{s.na_streak:>9}{mark}")
    if not rows:
        lines.append(f"(帳本裡沒有 {checker} 的紀錄)" if checker else "(沒有紀錄)")
    return lines


def render(r: Report, threshold: float, min_runs: int, checker: str | None) -> list[str]:
    lines = ["", "=== 不適用比率(儀表,不是閘門)==="]
    lines.append(f"帳本 {len(r.ledgers)} 份、{r.entries} 筆;舊 run(沒帳本){len(r.old_runs)} 張,"
                 f"**不進分母**;讀不動 {r.unreadable_total} 行")
    for path, n in sorted(r.unreadable.items()):
        lines.append(f"  · 讀不動 {n} 行:{path}")
    if r.skips_total:
        lines.append(f"閘門跳過(run-meta.json `gate_skipped: true`){r.skips_total} 跑"
                     f"(幕別是從欄位形狀**推斷**的;分不出哪一幕 {r.skips_unmapped} 跑)")
    lines.append("")
    lines.extend(render_table(r, threshold, min_runs, checker))
    lines.append("")
    warns = warnings(r, threshold, min_runs, checker)
    if warns:
        lines.extend(warns)
    else:
        lines.append(f"沒有超過門檻的(不適用率 > {threshold:.0%} 且跑過 ≥ {min_runs})。"
                     "⚠️ 這不代表守衛都還適用 —— 未達 min-runs 的那幾支這裡看不出來。")
    lines.append("")
    lines.append("--- 上限(讀結論之前先看)---")
    lines.append("* 只讀 check.py 記的帳本:直接跑檢查器、沒走 check.py 的,這裡一筆都沒有。")
    lines.append("* 舊 run(沒帳本)只印張數:它們當年是不是不適用,這裡量不到。")
    lines.append("* skip 欄是推斷:run-meta.json 沒寫 act,幕別是從欄位形狀猜的。")
    lines.append("* 門檻 0.25 / 5 是抄 Harmonist 形狀的起手值,沒在本 repo 量過。")
    return lines


# ── CLI ──────────────────────────────────────────────────────────────


def parse(argv: list[str]) -> tuple[bool, str | None, float, int, list[Path]]:
    brief = False
    checker: str | None = None
    threshold = DEFAULT_THRESHOLD
    min_runs = DEFAULT_MIN_RUNS
    roots: list[Path] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--brief":
            brief = True
        elif a in ("--checker", "--warn-threshold", "--min-runs"):
            if i + 1 >= len(argv):
                raise UsageError(f"{a} 後面要接值")
            v = argv[i + 1]
            i += 1
            try:
                if a == "--checker":
                    checker = v
                elif a == "--warn-threshold":
                    threshold = float(v)
                    if not 0.0 <= threshold <= 1.0:
                        raise ValueError
                else:
                    min_runs = int(v)
                    if min_runs < 1:
                        raise ValueError
            except ValueError:
                raise UsageError(f"{a} 的值壞了:{v!r}") from None
        elif a.startswith("-"):
            raise UsageError(f"不認識的參數:{a}")
        else:
            roots.append(Path(a))
        i += 1
    if not roots:
        raise UsageError("要給至少一個 root 目錄")
    for root in roots:
        if not root.is_dir():
            raise UsageError(f"找不到目錄:{root}")
    return brief, checker, threshold, min_runs, roots


def main(argv: list[str]) -> int:
    try:
        brief, checker, threshold, min_runs, roots = parse(argv[1:])
    except UsageError as exc:
        print(f"na_ratio:用法錯誤 —— {exc}", file=sys.stderr)
        if "--brief" not in argv:   # runner 開頭那一行不要把整份 docstring 灌進 log
            print(__doc__, file=sys.stderr)
        return 2
    r = collect(roots)
    applicable = bool(r.ledgers) and r.entries > 0
    if brief:
        print(brief_line(r, threshold, min_runs, checker))
        return 0 if applicable else 3
    for line in render(r, threshold, min_runs, checker):
        print(line)
    if not applicable:
        why = "一份 check-ledger.jsonl 都沒有" if not r.ledgers else "帳本裡一筆都讀不動"
        print(f"❌ **{why} —— 整份不適用,不是通過**(ADR 0005 §6)—— 離開碼 3。"
              f"舊 run {len(r.old_runs)} 張是票 21 之前的,本來就沒帳本。")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
