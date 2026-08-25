#!/usr/bin/env python3
"""訪談 prompt 分家(2026-08-18)裡釘著凍結語料的那三條。

從 `harness/test_relay.py` 搬來(票 32):這幾支讀的是 `examples/returns/interview-prompt.md`
(凍結受測品,比 git blob)、`examples/shop/harness/act1/`(受測輸入)與
`examples/shop/spec/SPEC.md`,hub 沒有那份語料。
唯一不逐字的地方:原本每支自己算 `repo = Path(__file__).resolve().parents[2]`,
搬到這裡深度不同,改成讀模組層的 `REPO`。
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


# ── 訪談 prompt 的分家(2026-08-18)────────────────────────────────────────

def test_凍結的那份沒有被就地改到() -> None:
    """`examples/returns/interview-prompt.md` 有 run 用過,不得就地改。

    分家的整個重點就是這個:改 harness 不該動到實驗基準。
    """
    import subprocess
    repo = REPO
    blob = subprocess.run(
        ["git", "rev-parse", "HEAD:examples/returns/interview-prompt.md"],
        cwd=repo, capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert blob.startswith("71c1eb7d6eb6"), (
        f"凍結的受測 prompt 被改了(現在是 {blob[:12]});"
        "要改訪談 prompt 請改 harness/interview-prompt.md"
    )


def test_orchestrator_自己複製三份受測輸入(tmp_path: Path) -> None:
    """**三份都要機械複製,一份都不靠人記得放。**

    上次只有工作指示是手動放的,就放到凍結的受測品去了。
    只把那一份改成自動、留另外兩份手動,等於把同一個坑留著。
    """
    import orchestrate
    repo = REPO
    orchestrate.stage_inputs(tmp_path, repo / "examples/shop/harness/act1")
    assert (tmp_path / "interviewer" / "interview-prompt.md").exists()
    assert (tmp_path / "interviewer" / "prompt.txt").exists()
    assert (tmp_path / "stakeholder" / "prompt.txt").exists()
    # 需求方腦中的需求 —— 漏了不會報錯,只會產出一場空洞的訪談
    assert (tmp_path / "stakeholder" / "spec" / "SPEC.md").exists()
    # 工作指示要是 harness 的正本(含 ADR 0004 的要求),不是別處那份
    assert "wire shape" in (tmp_path / "interviewer" / "interview-prompt.md").read_text(
        encoding="utf-8")


def test_需求方拿到的就是凍結的那份_SPEC() -> None:
    """他腦中的需求必須逐位元組等於 `examples/shop/spec/SPEC.md`。

    複製一份進 template 是為了讓 `stage_inputs` 單純(整包複製),
    代價是多一份可能漂的東西 —— 所以用這條測試把它釘住。
    """
    repo = REPO
    staged = repo / "examples/shop/harness/act1/stakeholder/spec/SPEC.md"
    frozen = repo / "examples/shop/spec/SPEC.md"
    assert staged.read_bytes() == frozen.read_bytes(), (
        "需求方拿到的 SPEC 跟凍結那份不一樣 —— 受測條件變了,先前的跑就不能比"
    )
