#!/usr/bin/env python3
"""第一幕:兩個 agent 的訪談。我只轉述,不加工。

⚠️ **這是 2026-08-18 那次跑用的版本,已被 `tools/harness/orchestrate.py` 取代。
留在這裡是那次跑的紀錄,不要拿它來跑新的訪談。**

它的洞:問 N 輪、只轉交 N-1 輪 —— 迴圈最後一次的 `message = answers`(第 78 行)
是死碼,跑完直接進第 80 行那段寫死的「訪談到此為止」。需求方對第 4 輪的完整回答
因此從沒進到訪談者的 session。細節見同目錄 FINDING-transport-loss.md。

訪談 agent 看不到 SPEC.md;stakeholder agent 看得到,但被要求只答被問到的。
**過程隔離,不靠指示** —— 兩個目錄是分開的。

我在中間唯一做的事是原樣轉述。不摘要、不改寫、不補充 —— 一旦我加工,
量到的就是我的轉述能力,不是訪談 prompt 的能力。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).parent
ROUNDS = 4

ENV = {
    "HOME": os.environ["HOME"],
    "PATH": f"{os.environ['HOME']}/.local/bin:/opt/homebrew/bin:/usr/bin:/bin",
    "USER": os.environ.get("USER", ""),
    "TERM": "dumb",
    "LANG": "en_US.UTF-8",
}


def talk(cwd: Path, message: str, session: str, model: str, first: bool) -> str:
    cmd = [
        "claude", "-p", message, "--model", model, "--safe-mode",
        "--permission-mode", "bypassPermissions", "--output-format", "json",
    ]
    cmd += ["--session-id", session] if first else ["--resume", session]
    proc = subprocess.run(cmd, cwd=cwd, env=ENV, capture_output=True, text=True)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise SystemExit(f"{cwd.name} 掛了:{proc.stderr[-800:]}")
    return json.loads(proc.stdout)["result"]


def main() -> int:
    interviewer, stakeholder = HERE / "interviewer", HERE / "stakeholder"
    sid_i, sid_s = str(uuid.uuid4()), str(uuid.uuid4())
    transcript: list[tuple[str, str]] = []
    log = HERE / "transcript.md"
    # ⚠️ 逐輪寫檔,不要只在最後寫。2026-08-18 第一次跑就是只在最後寫,
    #    最後那步掛掉 → 四輪訪談(約 15k 字)全部沒落地,只能從
    #    ~/.claude/projects/ 的 session jsonl 撈回來。
    #    **中間產物要在產生的當下就落地,不是在流程成功時才落地。**
    (HERE / "session-ids.txt").write_text(
        f"interviewer={sid_i}\nstakeholder={sid_s}\n", encoding="utf-8"
    )

    def flush() -> None:
        log.write_text(
            "\n\n---\n\n".join(f"## {who}\n\n{text}" for who, text in transcript),
            encoding="utf-8",
        )

    # stakeholder 先就位(讀完他心裡的需求)
    talk(stakeholder, (stakeholder / "prompt.txt").read_text(encoding="utf-8"),
         sid_s, "sonnet", first=True)

    message = (interviewer / "prompt.txt").read_text(encoding="utf-8")
    first_i = True
    for rnd in range(1, ROUNDS + 1):
        questions = talk(interviewer, message, sid_i, "opus", first=first_i)
        first_i = False
        transcript.append((f"訪談者 · 第 {rnd} 輪", questions)); flush()
        print(f"[第 {rnd} 輪] 訪談者 {len(questions)} 字", flush=True)

        answers = talk(stakeholder, questions, sid_s, "sonnet", first=False)
        transcript.append((f"需求方 · 第 {rnd} 輪", answers)); flush()
        print(f"[第 {rnd} 輪] 需求方 {len(answers)} 字", flush=True)
        message = answers

    final = talk(interviewer, """訪談到此為止,不要再問了。

現在把訪談結果落成一份**散文規格**,寫到檔案 SPEC-draft.md。至少要有這三節:

## 端點
## 情境(Given-When-Then)
## 領域規則

「情境」那一節是重點:每條要有具體的前提資料(顧客、商品、數量、金額、幣別)、
單一動作、可斷言的結果 —— 能一比一翻成自動化測試。數字單位不得有歧義。

沒問到的東西不要自己填,寫進「明確不在範圍」並標「規格沉默」。""",
                 sid_i, "opus", first=False)
    transcript.append(("訪談者 · 落檔", final)); flush()
    print("\n訪談紀錄:", HERE / "transcript.md")
    draft = interviewer / "SPEC-draft.md"
    print("散文規格:", draft, "—— 存在:" , draft.exists())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
