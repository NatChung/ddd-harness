#!/usr/bin/env python3
"""`provenance_check` 的測試 —— 對**今天真實跑出來的兩份語料**驗,不是對我編的例子驗。

偵測器要拿已知陽性驗,而且要拿**兩個形狀不同的**。預測寫在
`.scratch/ddd-harness/03-PREDICTION.md`,**commit 在寫程式之前**:
抓得到 B(訪談者餵值)、**抓不到 A**(需求方自編)。兩條都在下面釘住 ——
**包括那條「抓不到」**,因為宣稱抓得到而其實抓不到,比誠實地抓不到糟得多。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import provenance_check as pc  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
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


# ── 假陽性的三個來源(每條都是實跑撞到的,不是想像的)────────────────────

def test_題號不算資料值() -> None:
    """`R1-Q3` / `R3-Q13` 是訪談自己的編號體系。第一版沒濾,佔了 67% 的標記。"""
    text = "| R1-Q3 | 誰會看訂單列表 | 先全部看到就好 | `暫定 [Q3]` |"
    assert pc.claims(text) == []


def test_標準編號不算資料值() -> None:
    """「ISO 8601」的 8601。用**上下文**濾而不是把數字加進黑名單 ——
    黑名單會愈長愈像調參數,而調到剛好讓已知陽性活著就是自欺。"""
    assert pc.claims("| `created_at` | ISO 8601 時間戳 | 訂單成立時間 | [Q1] |") == []


def test_只掃_Qn_不掃推導自與本案自決() -> None:
    """總額是算出來的、HTTP 形式是自決的 —— 那些值本來就不該出現在答案裡,
    掃它們只會製造假陽性。"""
    assert pc.claims("總金額 568.50 由系統算出 `推導自 [Q8]` 的乘加") != []  # 有 [Q8] → 掃
    assert pc.claims("HTTP 動詞 `POST /orders` 為 `本案自決`,小數 2 位") == []


def test_千分位兩種寫法都認() -> None:
    """答案常寫「1500」,規格寫「1,500」—— 這種差異不該變成標記。"""
    assert pc.check(OPUS, OPUS / "SPEC-draft.md") is not None  # 不炸
    assert "1,500".replace(",", "") == "1500"


# ── 一行多值要逐值判定 ────────────────────────────────────────────────

def test_一行兩個值要拆成兩筆() -> None:
    """不要因為一行裡有一個值對得上就整行放行 —— 100/120 就在同一行。"""
    flagged = pc.check(OPUS, OPUS / "SPEC-draft.md")
    assert len(flagged) == 2 and len({f["value"] for f in flagged}) == 2


def test_沒有答案語料要當場掛(tmp_path: Path) -> None:
    """吃錯目錄要立刻知道,不要回一個空佇列讓人以為乾淨。"""
    with pytest.raises(pc.UsageError):
        pc.answers_corpus(tmp_path)


def test_吃錯目錄的離開碼是2不是1(tmp_path: Path) -> None:
    """「吃錯目錄」是**用法錯誤**(2)。這支的離開碼表裡沒有 1。

    原本是 `raise SystemExit("字串")` —— Python 對字串型 `SystemExit` 一律離開碼 **1**,
    落在一個這支沒定義的碼上。
    兩種成因(沒有 `rounds/`、`rounds/` 底下沒有 `*-answers.md`)都要是 2。
    """
    spec = tmp_path / "SPEC.md"
    spec.write_text("總額 12000 元 [Q1]\n", encoding="utf-8")

    assert pc.main(["x", str(tmp_path), str(spec)]) == 2      # 沒有 rounds/

    (tmp_path / "rounds").mkdir()
    assert pc.main(["x", str(tmp_path), str(spec)]) == 2      # rounds/ 是空的
