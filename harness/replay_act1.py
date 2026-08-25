#!/usr/bin/env python3
"""第一幕訪談的**重現播放器** —— 給現場講課用。

它不跑任何模型、不產生任何東西。它只做一件事:**照帳本的順序,把當時真的
發生過的檔案念出來**,一段一停,等你按 Enter 才往下。

為什麼是重現而不是重跑:重跑要十幾分鐘、可能失敗,而且台下沒辦法分辨新跑的
跟事先準備的有什麼差別。重現的每一個字都指得出檔案,**投影上按 Enter 之前
你就可以先說下一格會出現什麼** —— 那本身就是最強的證明。

順序的來源是 `relay-ledger.jsonl`(帳本),不是我在腳本裡寫死的順序。
帳本記三種事件:

    asked     訪談者問出去(chars = 問題的字數,file = 落檔位置)
    answered  需求方回答
    relayed   轉交(chars 必須等於 answered 的 chars —— 這是帳本的第 2 條檢查)

⚠️ **這支不驗證任何東西。** 帳本的檢查在 `relay_ledger.py`,不在這裡。
   這支只負責播,播不出來就是檔案不見了,它會直接說哪個檔不見。

用法:
    python3 harness/replay_act1.py <run-dir>
    python3 harness/replay_act1.py <run-dir> --round 3     只播第 3 輪
    python3 harness/replay_act1.py <run-dir> --round 3,4,5 播這三輪(現場建議)
    python3 harness/replay_act1.py <run-dir> --clear       每停一次清一次螢幕
    python3 harness/replay_act1.py <run-dir> --raw         「(補:…)」不換行
    python3 harness/replay_act1.py <run-dir> --no-ansi     **粗體** 直接去掉星號
    python3 harness/replay_act1.py <run-dir> --type        一個字一個字打出來(現場用)
    python3 harness/replay_act1.py <run-dir> --type --cps 60   打快一點
    python3 harness/replay_act1.py <run-dir> --no-pause    不停,一次印完

離開碼:
    0  播完
    2  用法錯誤 / run-dir 不存在 / 帳本不見
    3  帳本在,但它指的某個檔不見了
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

LEDGER = "relay-ledger.jsonl"

# 現場投影用:粗一點的分隔線比顏色可靠(有人的終端機不吃 ANSI)
RULE = "─" * 72
THICK = "━" * 72

# 打字速度(字/秒)。訪談者打字快(它是機器),需求方慢(他在想)。
# 這個差本身就在講一件事:**慢的那一邊才是瓶頸**。
CPS_ASK = 55.0
CPS_ANSWER = 16.0


def typewrite(text: str, cps: float, enabled: bool) -> None:
    """一個字一個字印出來。

    非 tty(管線 / 測試)一律直接整段印 —— 逐字寫進管線只是把同樣的字寫慢一點,
    沒有任何人在看,而且會讓測試變慢。
    """
    if not enabled or not sys.stdout.isatty() or cps <= 0:
        print(text)
        return
    delay = 1.0 / cps
    try:
        for ch in text:
            sys.stdout.write(ch)
            sys.stdout.flush()
            # 標點後多停一下,像人講話換氣
            time.sleep(delay * (6 if ch in "。?!:;\n" else 1))
    except KeyboardInterrupt:
        # Ctrl-C 不是中斷 demo,是「這段別打了,直接顯示完」
        sys.stdout.write(text[text.index(ch) + 1 :] if ch in text else "")
        sys.stdout.flush()
    print()


def load_ledger(run_dir: Path) -> list[dict]:
    """讀帳本。回傳原始順序的事件清單 —— 順序就是當時發生的順序,不重排。"""
    path = run_dir / LEDGER
    if not path.exists():
        raise FileNotFoundError(f"找不到帳本:{path}")
    events = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{LEDGER} 第 {lineno} 行不是合法 JSON:{exc}") from exc
    return events


def rounds_from(events: list[dict]) -> list[dict]:
    """把帳本折成每一輪一格:{round, asked, answered, relayed}。

    刻意**不容錯**:帳本裡沒有的東西就是 None,播的時候會印「(帳本沒有這一格)」。
    補一個看起來合理的預設值,等於把帳本的缺口蓋掉,而那正是帳本存在的理由。
    """
    by_round: dict[int, dict] = {}
    for ev in events:
        rnd = ev.get("round")
        if rnd is None:
            continue
        slot = by_round.setdefault(rnd, {"round": rnd, "asked": None, "answered": None, "relayed": None})
        kind = ev.get("event")
        if kind in slot:
            slot[kind] = ev
    return [by_round[k] for k in sorted(by_round)]


# 每一題結尾的「(補:…)」正是鐵律第 3 條的證據 —— 但它擠在長句尾巴,投影上會被略過。
# 預設把它拆到自己一行、縮排。這是**排版**不是改內容:整段字一個都沒動、沒有刪。
_SUPPLEMENT = re.compile(r"(?<=\S)(\(補:[^)]*\))\s*$")

# 逐字稿是 markdown,訪談者會用 **粗體** 強調(例:Q26 逼裁決「**總價**」指哪一個)。
# 終端機不吃 markdown,原樣印就是一堆星號 —— 而那題是全場最重要的一題。
# 接 tty 時轉 ANSI 粗體(粗體不是顏色,支援度比顏色高);不是 tty(管線、測試)就去掉星號,
# 這樣輸出是決定性的,測試不用去比對逸出序列。
_BOLD = re.compile(r"\*\*(.+?)\*\*")


def render_bold(text: str, ansi: bool) -> str:
    return _BOLD.sub(lambda m: f"\033[1m{m.group(1)}\033[0m" if ansi else m.group(1), text)


def unfold_supplements(text: str) -> str:
    out = []
    for line in text.splitlines():
        m = _SUPPLEMENT.search(line)
        if m:
            out.append(line[: m.start()].rstrip())
            out.append(f"      ↳ {m.group(1)}")
        else:
            out.append(line)
    return "\n".join(out)


def read_file(run_dir: Path, rel: str | None) -> str:
    if not rel:
        return "(帳本沒有記這一格的檔名)"
    path = run_dir / rel
    if not path.exists():
        raise FileNotFoundError(f"帳本指向 {rel},但檔案不存在:{path}")
    return path.read_text(encoding="utf-8").rstrip("\n")


def pause(enabled: bool, hint: str, clear: bool = False) -> None:
    if not enabled:
        return
    try:
        input(f"\n    [Enter] {hint}")
        if clear:
            print("\033[2J\033[H", end="")
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)


def play(run_dir: Path, only_rounds: list[int] | None, do_pause: bool,
         clear: bool = False, raw: bool = False, ansi: bool | None = None,
         typing: bool = False, cps: float | None = None) -> int:
    if ansi is None:
        ansi = sys.stdout.isatty()
    events = load_ledger(run_dir)
    rounds = rounds_from(events)
    total_rounds = len(rounds)
    if only_rounds is not None:
        rounds = [r for r in rounds if r["round"] in only_rounds]
        if not rounds:
            want = ",".join(str(n) for n in only_rounds)
            print(f"帳本裡沒有第 {want} 輪", file=sys.stderr)
            return 2

    meta_path = run_dir / "run-meta.json"
    print(THICK)
    print(f"  第一幕訪談 —— 重現播放   {run_dir.name}")
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("stakeholder"):
            print(f"  需求方:{meta['stakeholder']}　訪談者:{meta.get('interviewer_model', '?')}")
    if len(rounds) == total_rounds:
        shown = f"{total_rounds} 輪"
    else:
        picked = ",".join(str(r["round"]) for r in rounds)
        shown = f"第 {picked} 輪(全 {total_rounds} 輪)"
    print(f"  共 {shown}　來源:{LEDGER}(順序照帳本,不是腳本寫死的)")
    print(THICK)

    for r in rounds:
        asked, answered, relayed = r["asked"], r["answered"], r["relayed"]

        pause(do_pause, f"第 {r['round']} 輪:訪談者問了什麼", clear)
        print(f"\n{RULE}\n  第 {r['round']} 輪 · 訪談者問出去"
              f"({asked['chars'] if asked else '?'} 字 · {asked['file'] if asked else '?'})\n{RULE}")
        body = read_file(run_dir, asked.get("file") if asked else None)
        typewrite(render_bold(body if raw else unfold_supplements(body), ansi),
                  cps if cps is not None else CPS_ASK, typing)

        pause(do_pause, f"第 {r['round']} 輪:需求方怎麼答", clear)
        print(f"\n{RULE}\n  第 {r['round']} 輪 · 需求方回答"
              f"({answered['chars'] if answered else '?'} 字 · {answered['file'] if answered else '?'})\n{RULE}")
        typewrite(render_bold(read_file(run_dir, answered.get("file") if answered else None), ansi),
                  cps if cps is not None else CPS_ANSWER, typing)

        # 帳本的重點在這一行:轉交的字數必須跟回答的字數一樣。
        # 不一樣 = 有人在轉交途中改了字(2026-08-19 真的發生過:全形箭頭被正規化,五輪少 39 字)。
        if answered and relayed:
            same = answered.get("chars") == relayed.get("chars")
            mark = "✓ 一致" if same else "✗ 不一致 —— 轉交途中被改過"
            print(f"\n    帳本:回答 {answered.get('chars')} 字 → 轉交 {relayed.get('chars')} 字　{mark}")

    print(f"\n{THICK}\n  播完。下一步開 SPEC-draft.md —— 這 {total_rounds} 輪最後落成那份規格。\n{THICK}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="第一幕訪談的重現播放器(不跑模型)")
    ap.add_argument("run_dir", help="訪談那一跑的目錄(裡面要有 relay-ledger.jsonl)")
    ap.add_argument("--round", default=None,
                    help="只播某幾輪,逗號分隔(例:3 或 3,4,5)")
    ap.add_argument("--clear", action="store_true", help="每停一次清一次螢幕(投影用)")
    ap.add_argument("--raw", action="store_true", help="「(補:…)」不拆行,照原檔印")
    ap.add_argument("--no-ansi", action="store_true", help="**粗體** 直接去星號,不轉 ANSI")
    ap.add_argument("--type", dest="typing", action="store_true",
                    help="一個字一個字打出來(現場用;Ctrl-C 跳過當前這段)")
    ap.add_argument("--cps", type=float, default=None,
                    help="打字速度,字/秒(預設:問 55、答 16)")
    ap.add_argument("--no-pause", action="store_true", help="不停,一次印完")
    args = ap.parse_args(argv)

    only_rounds = None
    if args.round is not None:
        try:
            only_rounds = [int(x) for x in args.round.split(",") if x.strip()]
        except ValueError:
            print(f"--round 只吃數字或逗號分隔的數字,收到:{args.round}", file=sys.stderr)
            return 2
        if not only_rounds:
            print("--round 是空的", file=sys.stderr)
            return 2

    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        print(f"不是目錄:{run_dir}", file=sys.stderr)
        return 2
    try:
        ansi = False if args.no_ansi else None
        return play(run_dir, only_rounds, not args.no_pause, args.clear, args.raw, ansi,
                    args.typing, args.cps)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 3 if LEDGER not in str(exc) else 2
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
