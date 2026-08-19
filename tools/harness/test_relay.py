#!/usr/bin/env python3
"""`relay_ledger` 的測試 —— 離線、對假帳本跑。

**最重要的一條是 `test_舊版的洞會被抓到`:它重演 2026-08-18 真的發生的形狀
(問 N 輪、只轉交 N-1 輪),而不是重演一個我自己編的形狀。**
偵測器要拿已知陽性驗,不是拿自己想像的失敗驗 —— 這是假驗收那輪的教訓。

順帶驗的是「綠燈證明得了什麼」:健康的帳本要過,而**每一種掉法都要各自變紅**。
只驗綠會讓這整組檢查恆真。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import relay_ledger  # noqa: E402


def build(run_dir: Path, rounds: int, relay_upto: int | None = None) -> Path:
    """造一份帳本。`relay_upto` 是「轉交到第幾輪為止」,None = 全部轉交。"""
    relay_upto = rounds if relay_upto is None else relay_upto
    ledger = relay_ledger.Ledger(run_dir)
    for rnd in range(1, rounds + 1):
        ledger.asked(rnd, "interviewer", "sid-i", f"第 {rnd} 輪的問題" * 10)
        answers = f"第 {rnd} 輪的回答" * 10
        ledger.answered(rnd, "stakeholder", "sid-s", answers)
        if rnd <= relay_upto:
            ledger.relayed(rnd, "stakeholder", "interviewer", answers)
    return run_dir


def test_健康的帳本要過(tmp_path: Path) -> None:
    assert relay_ledger.verify(build(tmp_path, 4)) == []


def test_舊版的洞會被抓到(tmp_path: Path) -> None:
    """2026-08-18 的真實形狀:問了 4 輪,只轉交 3 輪。

    當時沒有任何一方知道 —— 訪談者以為訪談中止、需求方以為自己答完了、
    transcript 兩側俱全。這條檢查就是要讓那個狀態變紅。
    """
    problems = relay_ledger.verify(build(tmp_path, 4, relay_upto=3))
    assert len(problems) == 1
    assert "第 4 輪" in problems[0]
    assert "從來沒有被轉交" in problems[0]


@pytest.mark.parametrize("rounds,upto", [(2, 1), (4, 3), (6, 5), (4, 0)])
def test_不管幾輪掉在哪都要抓到(tmp_path: Path, rounds: int, upto: int) -> None:
    """掉最後一輪只是其中一種。掉任何一輪、掉幾輪,都要逐輪點名。"""
    problems = relay_ledger.verify(build(tmp_path, rounds, relay_upto=upto))
    assert len(problems) == rounds - upto


def test_轉交時被加工也算掉東西(tmp_path: Path) -> None:
    """摘要 / 截斷跟沒轉交是同一類:送到對面的不是他說的話。

    orchestrator 的職責寫著「我只轉述,不加工」—— 這條讓那句話變成可查的。
    """
    ledger = relay_ledger.Ledger(tmp_path)
    ledger.asked(1, "interviewer", "sid-i", "問題" * 20)
    ledger.answered(1, "stakeholder", "sid-s", "完整的回答" * 20)
    ledger.relayed(1, "stakeholder", "interviewer", "摘要過的回答")
    problems = relay_ledger.verify(tmp_path)
    assert len(problems) == 1
    assert "中間有人加工過" in problems[0]


def test_帳本指到不存在的檔要紅(tmp_path: Path) -> None:
    """記了帳但檔案不在 = 記帳跟落檔脫鉤了。今天掉料的四種形狀裡有三種
    長這樣:有人以為東西在,而它不在。"""
    build(tmp_path, 2)
    (tmp_path / "rounds" / "r2-answers.md").unlink()
    problems = relay_ledger.verify(tmp_path)
    assert any("不存在的檔" in p for p in problems)


def test_沒有帳本本身就是紅的(tmp_path: Path) -> None:
    """**空的不算過。** 這條是防止檢查在「沒跑過」的目錄上印綠燈 ——
    純綠燈證明不了任何事,而「找不到東西所以沒問題」是最廉價的假綠燈。"""
    assert relay_ledger.verify(tmp_path) != []


def test_每筆記錄當場落地(tmp_path: Path) -> None:
    """帳本不准犯它要抓的那個錯:寫一筆就在檔案裡看得到一筆,
    不是等流程成功才一次寫出來。"""
    ledger = relay_ledger.Ledger(tmp_path)
    ledger.asked(1, "interviewer", "sid-i", "問題")
    assert len(relay_ledger.read(tmp_path)) == 1
    ledger.answered(1, "stakeholder", "sid-s", "回答")
    assert len(relay_ledger.read(tmp_path)) == 2


def test_show_把沒轉交的那輪標出來(tmp_path: Path) -> None:
    table = relay_ledger.show(build(tmp_path, 4, relay_upto=3))
    assert "**沒有**" in table
    assert table.count("→ interviewer") == 3


def test_final_message_一定帶著最後一輪的答案() -> None:
    """舊版最後那段指示是寫死的文字,把最後一輪的答案蓋掉了。
    這條釘住修法本身:收尾指示與最後一輪的答案是同一則訊息。"""
    import orchestrate
    answers = "第十六,訂單要不要編號:要,系統會給一個單號"
    msg = orchestrate.final_message(answers)
    assert answers in msg
    assert "訪談到此為止" in msg
    assert msg.index(answers) < msg.index("訪談到此為止")


# ── 訪談 prompt 的分家(2026-08-18)────────────────────────────────────────

def test_訪談_prompt_的正本在_harness_底下() -> None:
    """第一幕實際讀的那份 prompt,必須是 harness 擁有、改得動的那份。

    2026-08-18 查到:當時讀的是 `examples/returns/interview-prompt.md`
    —— 跨模型實驗的**凍結受測品**(blob `71c1eb7d6eb6`)。於是
    ADR 0004 的 wire shape 要求寫進了 skill,卻**流不進訪談**。
    """
    canonical = Path(__file__).parent / "interview-prompt.md"
    assert canonical.exists(), "訪談 prompt 的正本要在 tools/harness/ 底下"
    text = canonical.read_text(encoding="utf-8")
    # ADR 0004 的要求要真的在裡面,不是只在 skill 裡
    assert "wire shape" in text
    assert "逐欄寫明" in text
    # 掛牌:別人來找的時候要看得到不要去拿凍結那份
    assert "凍結受測品" in text


def test_凍結的那份沒有被就地改到() -> None:
    """`examples/returns/interview-prompt.md` 有 run 用過,不得就地改。

    分家的整個重點就是這個:改 harness 不該動到實驗基準。
    """
    import subprocess
    repo = Path(__file__).resolve().parents[2]
    blob = subprocess.run(
        ["git", "rev-parse", "HEAD:examples/returns/interview-prompt.md"],
        cwd=repo, capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert blob.startswith("71c1eb7d6eb6"), (
        f"凍結的受測 prompt 被改了(現在是 {blob[:12]});"
        "要改訪談 prompt 請改 tools/harness/interview-prompt.md"
    )


def test_orchestrator_自己複製三份受測輸入(tmp_path: Path) -> None:
    """**三份都要機械複製,一份都不靠人記得放。**

    上次只有工作指示是手動放的,就放到凍結的受測品去了。
    只把那一份改成自動、留另外兩份手動,等於把同一個坑留著。
    """
    import orchestrate
    repo = Path(__file__).resolve().parents[2]
    orchestrate.stage_inputs(tmp_path, repo / "examples/shop/harness/act1")
    assert (tmp_path / "interviewer" / "interview-prompt.md").exists()
    assert (tmp_path / "interviewer" / "prompt.txt").exists()
    assert (tmp_path / "stakeholder" / "prompt.txt").exists()
    # 需求方腦中的需求 —— 漏了不會報錯,只會產出一場空洞的訪談
    assert (tmp_path / "stakeholder" / "spec" / "SPEC.md").exists()
    # 工作指示要是 harness 的正本(含 ADR 0004 的要求),不是別處那份
    assert "wire shape" in (tmp_path / "interviewer" / "interview-prompt.md").read_text(
        encoding="utf-8")


def test_受測輸入缺一份就直接掛掉(tmp_path: Path) -> None:
    """缺檔要當場掛,不要跑到一半才發現餵錯東西 —— 那時已經花掉一次 live run 的錢。"""
    import orchestrate
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(SystemExit) as exc:
        orchestrate.stage_inputs(tmp_path / "run", empty)
    assert "找不到受測輸入" in str(exc.value)


def test_需求方拿到的就是凍結的那份_SPEC() -> None:
    """他腦中的需求必須逐位元組等於 `examples/shop/spec/SPEC.md`。

    複製一份進 template 是為了讓 `stage_inputs` 單純(整包複製),
    代價是多一份可能漂的東西 —— 所以用這條測試把它釘住。
    """
    repo = Path(__file__).resolve().parents[2]
    staged = repo / "examples/shop/harness/act1/stakeholder/spec/SPEC.md"
    frozen = repo / "examples/shop/spec/SPEC.md"
    assert staged.read_bytes() == frozen.read_bytes(), (
        "需求方拿到的 SPEC 跟凍結那份不一樣 —— 受測條件變了,先前的跑就不能比"
    )
