#!/usr/bin/env python3
"""轉交帳本 —— 讓「有東西沒被轉交」變成查得出來的事,而不是靠人發現。

2026-08-18 量到的洞:第一幕的 orchestrator 問了 4 輪、卻只轉交 3 輪的答案。
需求方對 Q16–Q20 的回答完整地存在,從沒進到訪談者的 session,而
**沒有任何一方知道**:訪談者以為訪談中止,需求方以為自己答完了,
transcript 兩側俱全、看起來完整無缺。

那不是掛掉,是**迴圈結構的 off-by-one** —— 最後一輪的 `message = answers`
是死碼,迴圈跑完直接進「訪談到此為止」。所以修法不能只是「加 try/except」。

這個模組買的是**鐵律一套用到轉交本身**:每一次發問 / 回答 / 轉交都當場記一筆,
`verify` 是 runtime 無關的執行體,綁法(hook / CI / 誰記得跑)是另一回事。

判準只有一條,而且刻意寫得很笨:

    **每一筆 answered,都必須有一筆對應的 relayed。**

笨是故意的 —— 這條若寫成「大致上都有轉交」,今天這個洞就會被形式滿足。

用法:
    python3 relay_ledger.py verify <run_dir>     # 印違規,有違規回 exit 1
    python3 relay_ledger.py show  <run_dir>      # 印逐輪對照表
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

LEDGER_NAME = "relay-ledger.jsonl"

ASKED = "asked"
ANSWERED = "answered"
RELAYED = "relayed"


class Ledger:
    """逐筆落地的帳本。**每 append 一筆就 flush 一次** —— 這個模組存在的理由
    就是「流程成功時才落地」會掉東西,所以它自己不准犯同一個錯。"""

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.rounds_dir = self.run_dir / "rounds"
        self.rounds_dir.mkdir(exist_ok=True)
        self.path = self.run_dir / LEDGER_NAME

    def _append(self, record: dict) -> None:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()

    def land(self, name: str, text: str) -> Path:
        """把內容落成獨立檔案並回傳路徑。先落檔,才記帳。"""
        path = self.rounds_dir / name
        path.write_text(text, encoding="utf-8")
        return path

    def asked(self, rnd: int, who: str, session_id: str, text: str) -> None:
        path = self.land(f"r{rnd}-questions.md", text)
        self._append({
            "event": ASKED, "round": rnd, "who": who,
            "session_id": session_id, "chars": len(text),
            "file": str(path.relative_to(self.run_dir)),
        })

    def answered(self, rnd: int, who: str, session_id: str, text: str) -> None:
        path = self.land(f"r{rnd}-answers.md", text)
        self._append({
            "event": ANSWERED, "round": rnd, "who": who,
            "session_id": session_id, "chars": len(text),
            "file": str(path.relative_to(self.run_dir)),
        })

    def relayed(self, rnd: int, src: str, dst: str, text: str) -> None:
        """轉交**成功之後**才記 —— 記在轉交前的話,這條檢查就只證明我打算轉交。"""
        self._append({
            "event": RELAYED, "round": rnd, "from": src, "to": dst,
            "chars": len(text),
        })


def read(run_dir: Path) -> list[dict]:
    path = Path(run_dir) / LEDGER_NAME
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def verify(run_dir: Path) -> list[str]:
    """回傳違規清單。空清單 = 過。

    三條檢查,全部是「存在性」而非「數量大致對」:
      1. 每筆 answered 都要有同輪的 relayed;
      2. relayed 的字數要等於 answered 的字數(轉交時被摘要 / 截斷也是掉東西);
      3. 每筆 asked / answered 指到的檔案要真的在。
    """
    records = read(run_dir)
    if not records:
        return [f"帳本不存在或是空的:{Path(run_dir) / LEDGER_NAME}"]

    problems: list[str] = []
    answered = {r["round"]: r for r in records if r["event"] == ANSWERED}
    relayed = {r["round"]: r for r in records if r["event"] == RELAYED}

    for rnd in sorted(answered):
        a = answered[rnd]
        if rnd not in relayed:
            problems.append(
                f"第 {rnd} 輪:{a['who']} 答了 {a['chars']} 字,**從來沒有被轉交**"
                f"(內容在 {a['file']},沒有任何一方知道它掉了)"
            )
            continue
        if relayed[rnd]["chars"] != a["chars"]:
            problems.append(
                f"第 {rnd} 輪:答了 {a['chars']} 字,轉交的是 {relayed[rnd]['chars']} 字"
                f" —— 中間有人加工過"
            )

    for r in records:
        if r["event"] in (ASKED, ANSWERED):
            if not (Path(run_dir) / r["file"]).exists():
                problems.append(f"第 {r['round']} 輪的 {r['event']} 指到不存在的檔:{r['file']}")

    return problems


def show(run_dir: Path) -> str:
    records = read(run_dir)
    rounds = sorted({r["round"] for r in records if "round" in r})
    lines = ["輪 | 發問 | 回答 | 轉交", "---|---|---|---"]
    by = {(r["event"], r.get("round")): r for r in records}
    for rnd in rounds:
        a = by.get((ASKED, rnd))
        n = by.get((ANSWERED, rnd))
        y = by.get((RELAYED, rnd))
        lines.append(
            f"{rnd} | {a['chars'] if a else '—'} 字 | {n['chars'] if n else '—'} 字 | "
            + (f"{y['chars']} 字 → {y['to']}" if y else "**沒有**")
        )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in {"verify", "show"}:
        print(__doc__, file=sys.stderr)
        return 2
    run_dir = Path(argv[2])
    if argv[1] == "show":
        print(show(run_dir))
        return 0
    problems = verify(run_dir)
    if problems:
        print("❌ 轉交帳本有問題:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"ok: 每一輪的回答都被完整轉交了({run_dir / LEDGER_NAME})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
