#!/usr/bin/env python3
"""第一幕:兩個 agent 的訪談。我只轉述,不加工。

訪談 agent 看不到 SPEC.md;stakeholder agent 看得到,但被要求只答被問到的。
**過程隔離,不靠指示** —— 兩個目錄是分開的。

我在中間唯一做的事是原樣轉述。不摘要、不改寫、不補充 —— 一旦我加工,
量到的就是我的轉述能力,不是訪談 prompt 的能力。

用法:
    python3 orchestrate.py <run_dir> <template_dir> [rounds]

model 由環境變數指定(預設 訪談者 opus / 需求方 sonnet):

    INTERVIEWER_MODEL=haiku STAKEHOLDER_MODEL=haiku python3 orchestrate.py … 2

⚠️ **便宜的模型只驗得了管線,驗不了訪談品質。** 拿 haiku 跑完就說「第一幕通了」
是錯的 —— 它證明的是三份輸入有被複製、帳本逐輪記了、verify 綠、檔案落地。
**紅了要先問是管線紅還是模型紅**(第十三題那條歸因邏輯)。
用了哪個 model 會記進 `run-meta.json`,不要事後靠記憶。

`template_dir` 要有 `interviewer/prompt.txt` 與 `stakeholder/prompt.txt`
(shop 這條線是 `examples/shop/harness/act1`)。**這支 script 自己複製**,
run_dir 不用先準備任何東西 —— 手動放檔案就是上次接到凍結受測品去的原因。

---

## 2026-08-18 修掉的那個洞(讀這段再改這個檔)

舊版問了 N 輪、**只轉交 N-1 輪的答案**:迴圈最後一次的 `message = answers`
是死碼,跑完直接進「訪談到此為止」。於是需求方對第 4 輪的完整回答存在、
落了檔、進了 transcript,**卻從沒進到訪談者的 session**。

後果不是少一段內容,是**一條假阻斷**:訪談者誠實地把那五題標成「未答」,
其中一條標成「阻斷級,不得實作」,而需求方實際答的是「不用擋」。
**假阻斷比漏一條規格貴** —— 下游會停著等一個已經到了的裁決。

而**沒有任何一方知道**:訪談者以為訪談中止,需求方以為自己答完了,
transcript 兩側俱全看起來完整無缺。所以修法有三段,缺一不可:

1. **最後一輪的答案要先轉交,再收尾** —— 收尾的 prompt 由 `final_message()`
   把答案帶進去,不是另外寫一段把它蓋掉;
2. **每一次發問 / 回答 / 轉交都當場記帳**(`relay_ledger`),
   而且**轉交成功之後才記** —— 記在轉交前只證明我打算轉交;
3. **transcript 記 session 邊界**。舊的救援稿把兩側都標成
   `[user]`/`[assistant]`,而那正好抹掉了「這一段在誰的 session 裡」——
   要發現掉料只能靠去數段落。格式擋住了發現。

檢查本體是 `relay_ledger.verify`,跑完自己會叫它;它是 runtime 無關的,
綁法(hook / CI / 誰記得跑)是另一層的事。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import relay_ledger  # noqa: E402

INTERVIEWER_MODEL = os.environ.get("INTERVIEWER_MODEL", "opus")
STAKEHOLDER_MODEL = os.environ.get("STAKEHOLDER_MODEL", "sonnet")

ENV = {
    "HOME": os.environ["HOME"],
    "PATH": f"{os.environ['HOME']}/.local/bin:/opt/homebrew/bin:/usr/bin:/bin",
    "USER": os.environ.get("USER", ""),
    "TERM": "dumb",
    "LANG": "en_US.UTF-8",
}


def final_message(last_answers: str) -> str:
    """收尾的指示 —— **把最後一輪的答案帶進去**。

    舊版這裡是一段寫死的文字,於是最後一輪的答案被它蓋掉。
    帶進去之後,「轉交」與「收尾」是同一則訊息,結構上不可能再漏。
    """
    return f"""以下是需求方對你上一輪提問的回答,原樣轉給你:

{last_answers}

---

訪談到此為止,不要再問了。

現在把訪談結果落成一份**散文規格**,寫到檔案 SPEC-draft.md。至少要有這三節:

## 端點
## 情境(Given-When-Then)
## 領域規則

「端點」那一節要**逐欄寫明對外的 JSON 欄位名**(請求的每個欄位、回應與列表一列的
每個欄位)。他不懂技術、你沒問過他這個,所以標 `本案自決` —— 但**自決完要寫成合約**,
不能只寫「HTTP 形式本案自決」。沒寫的話下游只能自己取名,而不同的實作會各取各的。

「情境」那一節是重點:每條要有具體的前提資料(顧客、商品、數量、金額、幣別)、
單一動作、可斷言的結果 —— 能一比一翻成自動化測試。數字單位不得有歧義。

沒問到的東西不要自己填,寫進「明確不在範圍」並標「規格沉默」。"""


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


def write_transcript(path: Path, entries: list[dict]) -> None:
    """transcript **記 session 邊界**:每一段都標是誰、在哪個 session、第幾輪。

    舊的救援稿標的是 `[user]` / `[assistant]`,兩側同一組標籤 ——
    需求方的回答與訪談者的發言長得一模一樣,於是「送掉了」被渲染成「談完了」。

    ⚠️ 結構標題用 `#` 不是 `##`:agent 自己的輸出裡就有一堆 `##`
    (「## 盤點」「## 未答追蹤」),同層的話 grep 結構會混進內容。
    """
    blocks = []
    for e in entries:
        blocks.append(
            f"# {e['who']} · {e['label']}\n"
            f"\n"
            f"> session `{e['session_id']}` · {len(e['text'])} 字"
            f" · 轉交給:{e['relayed_to'] or '**沒有轉交**'}\n\n"
            f"{e['text']}"
        )
    path.write_text("\n\n---\n\n".join(blocks), encoding="utf-8")


def stage_inputs(here: Path, template_dir: Path) -> None:
    """把受測輸入複製進 run 目錄。**一份都不靠人記得放。**

    2026-08-18 查到:第一幕實際讀的工作指示是 `examples/returns/interview-prompt.md`
    —— 跨模型實驗的**凍結受測品**。原因很單純:當時是手動放的,而那是唯一存在的一份。
    **手動的接線就是會接錯。**

    ⚠️ 一開始只列了三份,漏掉需求方的 `spec/SPEC.md`(他腦中的需求就是那份)——
    漏了的話他無話可答,而那**不會報錯,只會產出一場空洞的訪談**。所以改成
    **整包複製 template_dir**,再對必要清單逐項確認:未來多一份輸入會自動被帶進去,
    不用改這裡。
    """
    required = [
        Path("interviewer/prompt.txt"),
        Path("stakeholder/prompt.txt"),
        Path("stakeholder/spec/SPEC.md"),
    ]
    missing = [str(template_dir / r) for r in required if not (template_dir / r).exists()]
    canonical = Path(__file__).with_name("interview-prompt.md")
    if not canonical.exists():
        missing.append(str(canonical))
    if missing:
        raise SystemExit("找不到受測輸入:\n  " + "\n  ".join(missing))

    for src in template_dir.rglob("*"):
        if src.is_file() and src.name != "README.md":
            dst = here / src.relative_to(template_dir)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    dst = here / "interviewer" / "interview-prompt.md"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(canonical.read_text(encoding="utf-8"), encoding="utf-8")


def input_blobs(template_dir: Path) -> dict[str, str]:
    """三份受測輸入的 git blob。認不出來就寫 unknown —— 不要猜。"""
    files = {
        "interview-prompt.md": Path(__file__).with_name("interview-prompt.md"),
        "interviewer/prompt.txt": template_dir / "interviewer" / "prompt.txt",
        "stakeholder/prompt.txt": template_dir / "stakeholder" / "prompt.txt",
    }
    out = {}
    for name, path in files.items():
        try:
            out[name] = subprocess.run(
                ["git", "hash-object", str(path)],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
        except Exception:
            out[name] = "unknown"
    return out


def main(argv: list[str]) -> int:
    if not 3 <= len(argv) <= 4:
        print(__doc__, file=sys.stderr)
        return 2
    here = Path(argv[1]).resolve()
    template_dir = Path(argv[2]).resolve()
    rounds = int(argv[3]) if len(argv) == 4 else 4

    interviewer, stakeholder = here / "interviewer", here / "stakeholder"
    stage_inputs(here, template_dir)
    sid_i, sid_s = str(uuid.uuid4()), str(uuid.uuid4())
    ledger = relay_ledger.Ledger(here)
    entries: list[dict] = []
    log = here / "transcript.md"

    (here / "session-ids.txt").write_text(
        f"interviewer={sid_i}\nstakeholder={sid_s}\n", encoding="utf-8"
    )
    # 受測輸入的 blob + 用了哪個 model,**跑之前就寫**。
    # 本 repo 對受測品的標準是逐 blob 對得上;事後靠記憶對不起來。
    (here / "run-meta.json").write_text(json.dumps({
        "rounds": rounds,
        "interviewer_model": INTERVIEWER_MODEL,
        "stakeholder_model": STAKEHOLDER_MODEL,
        "template_dir": str(template_dir),
        "input_blobs": input_blobs(template_dir),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    def record(who: str, label: str, sid: str, text: str, relayed_to: str | None) -> None:
        entries.append({"who": who, "label": label, "session_id": sid,
                        "text": text, "relayed_to": relayed_to})
        write_transcript(log, entries)

    # stakeholder 先就位(讀完他心裡的需求)
    talk(stakeholder, (stakeholder / "prompt.txt").read_text(encoding="utf-8"),
         sid_s, STAKEHOLDER_MODEL, first=True)

    message = (interviewer / "prompt.txt").read_text(encoding="utf-8")
    first_i = True
    answers = ""
    answer_entry: dict | None = None

    def mark_relayed(rnd: int, text: str, entry: dict | None) -> None:
        """轉交**成功之後**才記。這個函式的每個呼叫點,都緊接在
        真的把 text 送出去、而且對方回話了的那一刻之後。"""
        ledger.relayed(rnd, "stakeholder", "interviewer", text)
        if entry is not None:
            entry["relayed_to"] = "訪談者"
            write_transcript(log, entries)

    for rnd in range(1, rounds + 1):
        # 這一次 talk 把「第 rnd-1 輪的答案」當輸入送進訪談者 —— 它回話了,
        # 就代表那一輪的轉交成立。
        questions = talk(interviewer, message, sid_i, INTERVIEWER_MODEL, first=first_i)
        if not first_i:
            mark_relayed(rnd - 1, message, answer_entry)
        first_i = False
        ledger.asked(rnd, "interviewer", sid_i, questions)
        record("訪談者", f"第 {rnd} 輪發問", sid_i, questions, None)
        print(f"[第 {rnd} 輪] 訪談者 {len(questions)} 字", flush=True)

        answers = talk(stakeholder, questions, sid_s, STAKEHOLDER_MODEL, first=False)
        ledger.answered(rnd, "stakeholder", sid_s, answers)
        record("需求方", f"第 {rnd} 輪回答", sid_s, answers, None)
        answer_entry = entries[-1]
        print(f"[第 {rnd} 輪] 需求方 {len(answers)} 字", flush=True)
        message = answers

    # ⚠️ 舊版就是掉在這一行之前:迴圈結束,最後一輪的 answers 直接被丟掉。
    #    現在它由 final_message() 帶進收尾指示 —— 轉交與收尾是同一則訊息,
    #    結構上不可能再漏掉一輪。
    final = talk(interviewer, final_message(answers), sid_i, INTERVIEWER_MODEL, first=False)
    mark_relayed(rounds, answers, answer_entry)
    record("訪談者", "落檔", sid_i, final, None)

    problems = relay_ledger.verify(here)
    print("\n訪談紀錄:", log)
    print(relay_ledger.show(here))
    draft = interviewer / "SPEC-draft.md"
    print("散文規格:", draft, "—— 存在:", draft.exists())
    if problems:
        print("\n❌ 轉交帳本有問題:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\n✅ 每一輪的回答都被完整轉交了")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
