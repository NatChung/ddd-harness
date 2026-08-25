#!/usr/bin/env python3
"""檢查帳本 —— 讓「上一幕檢查過了沒」變成 runner 查得到的事,而不是靠人記得(票 21)。

`PIPELINE.md` 用文字說「幕三之後才幕四」「跑 `run_act4.sh` 之前先 `acceptance_gwt`
確認空骨架全紅」。2026-08-25 之前沒有任何東西擋:可以直接 `run_act4.sh` 而空骨架從沒
驗過紅,可以 `gen_acceptance.py` 而 `provenance_check` 從沒跑過。順序靠自律。

這支做兩件事,**一支檢查器的本體都不改**(刻意的,避免跟票 25 / 26 撞檔):

1. **包裝器**:用 subprocess 跑指定的檢查器,把
   `{"checker", "argv", "exit", "ts", "cwd"}` 追加進 `<run_dir>/check-ledger.jsonl`,
   檢查器的離開碼**原樣**傳出去。append-only jsonl,跟幕一的 `relay-ledger.jsonl` 同一種形狀。
2. **閘門**:runner 開工前呼叫 `--gate <act>`,讀帳本,回答「上一幕的檢查證據齊了沒」。

閘門判準(**這是本票最容易寫錯的一行**):

    通過 = 該檢查器**有一筆 `exit == 0`**。

    離開碼 3 是「不適用」—— 守衛靜靜地不再適用了,**不是通過**(ADR 0005 §6,
    `CONTEXT.md` 的「不適用」詞條)。寫成 `exit in (0, 3)` 就把它放行了。

閘門的離開碼:
    0  證據齊了
    1  有紀錄,但要求要過的那支沒有一筆 `exit == 0`(1 蓋過 3,同 `verify_generated`)
    2  用法錯誤
    3  **不適用**:帳本沒有那一幕的任何紀錄 —— 上一幕從沒被檢查過

各幕要什麼(`GATES`):
    act2  landing_check 有一筆 0
    act3  spec_store import 有一筆 0;provenance_check / contract_triage / glossary_check
          各**至少跑過一筆**(離開碼不拘 —— 那三支交的是分診佇列,不是判決)
    act4  acceptance_gwt 有一筆 0

帳本查的是「跑過且過了」,**不查「跑完之後東西有沒有再動」** —— 檢查完再改 SPEC,
帳本不會知道。那是另一張票的事。

`run_dir` 從 argv 推:第一個存在的**目錄**參數;沒有的話,第一個存在的**檔案**的上層目錄;
都推不到就離開碼 2,**不會退到 cwd**(記錯地方比沒記更糟 —— 下一幕的閘門會讀不到)。
兩支要明給 `--run-dir`:`provenance_check` 的目錄參數是幕一的 run,而幕三的閘門讀幕二的帳本;
`acceptance_gwt` 的 workdir 在跑之前可能還不存在,而幕四的閘門讀骨架目錄的帳本。

用法:
    python3 check.py [--run-dir <dir>] <checker> [args…]
        <checker> 是 harness 底下的模組名(landing_check、spec_store …),
        或一個 .py 的路徑(測試用)。
    python3 check.py --gate <act2|act3|act4> <dir> [<dir>…]
        依序找第一個有 check-ledger.jsonl 的目錄;一個都沒有 → 3。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HARNESS = Path(__file__).resolve().parent
LEDGER_NAME = "check-ledger.jsonl"

# (檢查器名, argv 第一個參數必須是什麼或 None, 必須有一筆 exit == 0 嗎)
GATES: dict[str, list[tuple[str, str | None, bool]]] = {
    "act2": [("landing_check", None, True)],
    "act3": [
        ("spec_store", "import", True),
        ("provenance_check", None, False),
        ("contract_triage", None, False),
        ("glossary_check", None, False),
    ],
    "act4": [("acceptance_gwt", None, True)],
}


class UsageError(Exception):
    pass


# ── 帳本 ─────────────────────────────────────────────────────────────


def ledger_path(run_dir: Path) -> Path:
    return run_dir / LEDGER_NAME


def append_entry(run_dir: Path, entry: dict) -> None:
    """一筆一行,寫完 flush —— 檢查器炸了帳本也要在。"""
    run_dir.mkdir(parents=True, exist_ok=True)
    with ledger_path(run_dir).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        fh.flush()


def read_ledger(run_dir: Path) -> list[dict] | None:
    """沒有帳本回 None(跟「帳本是空的」分開 —— 兩個都是不適用,但印的話不一樣)。"""
    path = ledger_path(run_dir)
    if not path.exists():
        return None
    entries: list[dict] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise UsageError(f"{path}:{lineno} 不是合法的 JSON:{exc}") from exc
    return entries


# ── 包裝器 ───────────────────────────────────────────────────────────


def resolve_checker(name: str) -> tuple[Path, str]:
    """回 (檔案路徑, 記進帳本的名字)。名字一律是模組名,不帶 .py。"""
    candidate = Path(name)
    if name.endswith(".py") and candidate.exists():
        return candidate.resolve(), candidate.stem
    path = HARNESS / f"{name.removesuffix('.py')}.py"
    if path.exists():
        return path, path.stem
    raise UsageError(f"找不到檢查器:{name}(harness 底下沒有 {path.name},也不是一個存在的 .py 路徑)")


def infer_run_dir(args: list[str]) -> Path | None:
    for arg in args:
        if Path(arg).is_dir():
            return Path(arg).resolve()
    for arg in args:
        if Path(arg).is_file():
            return Path(arg).resolve().parent
    return None


def run_checker(name: str, args: list[str], run_dir: Path | None) -> int:
    script, stem = resolve_checker(name)
    target = run_dir or infer_run_dir(args)
    if target is None:
        raise UsageError(
            f"推不出 run_dir:{stem} 的參數裡沒有存在的目錄或檔案 —— 用 --run-dir 明給"
        )
    proc = subprocess.run([sys.executable, str(script), *args])
    append_entry(target, {
        "checker": stem,
        "argv": list(args),
        "exit": proc.returncode,
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cwd": str(Path.cwd()),
    })
    print(f"check-ledger:{stem} exit {proc.returncode} → {ledger_path(target)}", file=sys.stderr)
    return proc.returncode


# ── 閘門 ─────────────────────────────────────────────────────────────


def gate(act: str, entries: list[dict] | None) -> tuple[int, list[str]]:
    """純函數:回 (離開碼, 要印的行)。`entries is None` = 沒有帳本。"""
    if act not in GATES:
        raise UsageError(f"不認識的幕:{act}(只有 {', '.join(GATES)})")
    if entries is None:
        return 3, ["不適用:上一幕從沒被檢查過(沒有 check-ledger.jsonl)"]

    lines: list[str] = []
    missing: list[str] = []
    failed: list[str] = []
    for checker, first_arg, must_pass in GATES[act]:
        label = checker if first_arg is None else f"{checker} {first_arg}"
        mine = [
            e for e in entries
            if e.get("checker") == checker
            and (first_arg is None or (e.get("argv") or [None])[0] == first_arg)
        ]
        if not mine:
            missing.append(label)
            continue
        codes = [e.get("exit") for e in mine]
        ok = [e for e in mine if e.get("exit") == 0]
        if must_pass and not ok:
            failed.append(f"{label}:{len(mine)} 筆,離開碼 {codes},沒有一筆是 0")
            continue
        if must_pass:
            lines.append(f"  ✅ {label} exit 0({ok[-1].get('ts')})")
        else:
            lines.append(f"  ✅ {label} 跑過 {len(mine)} 筆(離開碼 {codes};佇列不是判決,只要求跑過)")

    if failed:
        return 1, ["上一幕的檢查沒過:", *(f"  ❌ {f}" for f in failed),
                   *(f"  ⏭️ 沒跑過:{m}" for m in missing)]
    if missing:
        return 3, ["不適用:上一幕從沒被檢查過 —— 帳本裡沒有這幾支的紀錄:",
                   *(f"  ⏭️ {m}" for m in missing), *lines]
    return 0, ["上一幕的檢查證據齊了:", *lines]


def find_ledger_dir(candidates: list[str]) -> Path | None:
    for c in candidates:
        if ledger_path(Path(c)).exists():
            return Path(c).resolve()
    return None


def run_gate(act: str, candidates: list[str]) -> int:
    if not candidates:
        raise UsageError("--gate 要給至少一個目錄")
    run_dir = find_ledger_dir(candidates)
    entries = read_ledger(run_dir) if run_dir is not None else None
    code, lines = gate(act, entries)
    where = str(ledger_path(run_dir)) if run_dir is not None else "、".join(candidates)
    print(f"閘門({act})讀 {where}")
    for line in lines:
        print(line)
    return code


# ── CLI ──────────────────────────────────────────────────────────────


def main(argv: list[str]) -> int:
    args = argv[1:]
    try:
        if not args:
            raise UsageError("沒有參數")
        if args[0] == "--gate":
            if len(args) < 2:
                raise UsageError("--gate 後面要接幕名")
            return run_gate(args[1], args[2:])
        run_dir: Path | None = None
        if args[0] == "--run-dir":
            if len(args) < 3:
                raise UsageError("--run-dir 後面要接目錄與檢查器")
            run_dir, args = Path(args[1]).resolve(), args[2:]
        return run_checker(args[0], args[1:], run_dir)
    except UsageError as exc:
        print(f"用法錯誤:{exc}", file=sys.stderr)
        print(__doc__, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
