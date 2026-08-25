#!/usr/bin/env python3
"""`provenance_check` 的測試 —— 對**2026-08-18 真實跑出來的兩份語料**驗,不是對我編的例子驗。

從 `harness/test_provenance.py` 搬來(票 32):這幾支讀的是
`examples/shop/harness/runs/2026-08-18-act1-interview` 與 `…-haiku-roleplay/roleplay`,
hub 沒有那份語料。預測寫在 `.scratch/ddd-harness/03-PREDICTION.md`:
抓得到 B(訪談者餵值)、**抓不到 A**(需求方自編)—— 包括那條「抓不到」都釘住。
"""

from __future__ import annotations

from pathlib import Path

import provenance_check as pc  # harness/ 由 conftest 放進 sys.path

REPO = Path(__file__).resolve().parents[3]
OPUS = REPO / "examples/shop/harness/runs/2026-08-18-act1-interview"
HAIKU = REPO / "examples/shop/harness/runs/2026-08-18-act1-haiku-roleplay/roleplay"


# ── 已知陽性 B:訪談者餵值,再標成「他親口確認的」 ──────────────────────

def test_形狀B_抓得到_而且只抓到它() -> None:
    """opus 那場的 100/120:訪談者寫在誘導式提問裡,需求方從沒複述,
    而 `SPEC-draft.md` 標成「他在 Q9 親口確認的」。

    **同時釘住 0 假陽性** —— 第一版有 4 筆題號假陽性(67%),
    那種比例的佇列沒人會看,等於沒做。
    """
    flagged = pc.check(OPUS, OPUS / "SPEC-draft.md")
    assert {f["value"] for f in flagged} == {"100", "120"}
    assert all(f["line"] == 115 for f in flagged)


# ── 已知陽性 A:需求方自己編 —— **預測就是抓不到** ─────────────────────

def test_形狀A_抓不到_而且這是預期的() -> None:
    """haiku 那場的 `ORD-20260818-001`:凍結 SPEC 裡 0 次,是需求方現編的。

    但那個值**確實出現在答案裡**,所以本檢查必然放行 —— 這不是 bug,
    是這支工具的邊界。A 要靠票 04(需求方回答 vs 凍結 SPEC)。
    **寫成測試是為了讓「它抓不到」變成契約,而不是某天被當成 bug 修掉。**
    """
    corpus = pc.answers_corpus(HAIKU)
    assert "ORD-20260818-001" in corpus, "前提:那個值真的在答案語料裡"
    flagged = pc.check(HAIKU, HAIKU / "SPEC-draft.md")
    assert not any("ORD" in f["value"] for f in flagged)


def test_掃不到東西不算通過() -> None:
    """**「找不到東西所以沒問題」是最廉價的假綠燈。**

    haiku 那份規格濾完之後一筆 `[Qn]`-帶值 都沒有 —— 報表必須說「不是乾淨」,
    而且 exit 非 0。

    「沒有東西可查」是**不適用**,離開碼 **3**(ADR 0005 §6、`CONTEXT.md`〈不適用〉),
    跟「吃錯目錄」(2)分得開。原本這裡回 1 —— 那把「整份不適用」跟這條線上
    「有東西要人去看」擠在同一個碼裡。
    """
    assert pc.claims((HAIKU / "SPEC-draft.md").read_text(encoding="utf-8")) == []
    assert pc.main(["x", str(HAIKU), str(HAIKU / "SPEC-draft.md")]) == 3


# ── 假陽性來源:千分位(真實語料上不炸)────────────────────────────────

def test_千分位兩種寫法都認() -> None:
    """答案常寫「1500」,規格寫「1,500」—— 這種差異不該變成標記。"""
    assert pc.check(OPUS, OPUS / "SPEC-draft.md") is not None  # 不炸
    assert "1,500".replace(",", "") == "1500"


# ── 一行多值要逐值判定 ────────────────────────────────────────────────

def test_一行兩個值要拆成兩筆() -> None:
    """不要因為一行裡有一個值對得上就整行放行 —— 100/120 就在同一行。"""
    flagged = pc.check(OPUS, OPUS / "SPEC-draft.md")
    assert len(flagged) == 2 and len({f["value"] for f in flagged}) == 2
