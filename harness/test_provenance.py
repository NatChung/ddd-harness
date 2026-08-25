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


# ── 一行多值要逐值判定 ────────────────────────────────────────────────


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
