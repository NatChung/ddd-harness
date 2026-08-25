#!/usr/bin/env python3
"""`landing_check` 的測試 —— 對**四份今天真實跑出來的 run** 驗,不是對我編的例子驗。

預測寫在 `.scratch/ddd-harness/05-PREDICTION.md`,**commit 在寫程式之前**(`2aa7c30`),
四份語料的數字逐份寫死。下面把那四組數字釘成契約。

已知陽性是 haiku 那兩份:`r2-questions.md` / `r4-questions.md` **開頭根本沒有落點表**,
第一輪的 4 題、第三輪的 4 題就這樣滑過去了 —— 而 `relay_ledger.verify` 全綠
(答案都有被轉交)。**轉交了 ≠ 記下來了**,這支就是量那個差額的。

合成測試只用在**真實語料驗不到、但錯的方向是假通過**的那幾條(題號邊界、表格位置、
散文提及、輪次數字排序)。其餘一律用真資料。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import landing_check as lc  # noqa: E402


def _round(rep: dict, n: int) -> dict:
    return next(r for r in rep["rounds"] if r["round"] == n)


# ── §11 收尾表:參考,不進判定 ──────────────────────────────────────────


def test_沒有第十一節就沒有參考區塊() -> None:
    assert lc.spec_log_questions("## §9 ARCHITECTURE\n\n| a | b |\n|---|---|\n| Q3 | x |") == []


# ── 假通過的四個來源(真實語料驗不到,但錯的方向是假綠燈)──────────────

def _mkrun(tmp_path: Path, files: dict[str, str]) -> Path:
    rounds = tmp_path / "rounds"
    rounds.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (rounds / name).write_text(text, encoding="utf-8")
    return tmp_path


def test_Q1不准被Q11滿足(tmp_path: Path) -> None:
    """**這支最容易寫出來的 bug**,而且錯的方向是假通過。

    現有語料驗不到 —— opus 的 Q1 和 Q11 都有落點,子字串比對在那份資料上看起來全對。
    """
    run = _mkrun(tmp_path, {
        "r1-questions.md": "**Q1.** 訂單裝了什麼?\n",
        "r2-questions.md": "| 他說的 | 我記成 | 來源 |\n|---|---|---|\n| 上限 100 | C3 | `[Q11]` |\n\n**Q2.** 下一題\n",
    })
    assert lc.check(run)["rounds"][0]["missing"] == [1]


def test_表在問題之後不算落點表(tmp_path: Path) -> None:
    """`盤點` / `未答追蹤` 也是 markdown 表 —— 它們記的是**尚未落地**的東西。
    算進來就等於承認「我打算之後再處理」也是落點。"""
    run = _mkrun(tmp_path, {
        "r1-questions.md": "**Q1.** 甲\n",
        "r2-questions.md": "先問下一輪。\n\n**Q2.** 乙\n\n## 盤點\n\n| 尺度 | 狀態 |\n|---|---|\n| Q1 已收到 | 有落點 |\n",
    })
    assert lc.check(run)["rounds"][0]["missing"] == [1]


def test_輪次用數字排不是字典序(tmp_path: Path) -> None:
    """`r10` 的下一輪是 `r11` 不是 `r2`。跑到第 10 輪才炸的 bug 最難查。"""
    run = _mkrun(tmp_path, {
        "r9-questions.md": "**Q9.** 甲\n",
        "r10-questions.md": "| a | b |\n|---|---|\n| 甲 | `[Q9]` |\n\n**Q10.** 乙\n",
        "r11-questions.md": "| a | b |\n|---|---|\n| 乙 | `[Q10]` |\n\n**Q11.** 丙\n",
    })
    rep = lc.check(run)
    assert [r["round"] for r in rep["rounds"]] == [9, 10, 11]
    assert rep["missing_total"] == 0 and rep["landed_total"] == 2
    assert _round(rep, 11)["status"] == "not_applicable"


def test_引用形式不算問出去(tmp_path: Path) -> None:
    """`[Q7]` 是「提到」,`**Q7.` 才是「問出去」。把引用也算成提問,
    會讓「這一輪問了幾題」隨著訪談者的行文習慣浮動。"""
    assert lc.asked("`[Q7]` 你只用兩種狀態 → 推導自[Q7][Q13]") == []
    assert lc.asked("**Q11.**(第二輪欠的,原樣重問)界線在哪?") == [11]


def test_吃錯目錄要當場掛(tmp_path: Path) -> None:
    """沒有 `rounds/` 就是餵錯東西,要立刻知道,不要回一個空報表讓人以為乾淨。"""
    with pytest.raises(lc.UsageError):
        lc.check(tmp_path)


def test_吃錯目錄的離開碼是2不是1(tmp_path: Path) -> None:
    """docstring 的離開碼表寫著「2 用法錯誤(吃錯目錄)」,行為要真的是 2。

    原本這裡是 `raise SystemExit("字串")` —— Python 對字串型 `SystemExit` 一律
    離開碼 **1**,於是「吃錯目錄」跟「有漏接」撞在同一個碼上,而報表寫的是 2。
    **文件承諾 2、實測回 1** 就是這條測試釘住的東西。
    """
    assert lc.main(["x", str(tmp_path)]) == 2


# ── 掃到卻掃錯:靜默綠燈那條路(2026-08-18 稽核 §二.A)────────────────────
#
# 原本的守衛是 `if comparable_rounds == 0: return 1`,擋的是**沒有成對的 rN/rN+1 檔**,
# **不是「一題都沒比對到」**。檔案成對而題號一個都沒認出來,那一輪照樣算 compared、
# asked = 0、漏接 0 —— 一份 15 題的 run 靜靜地變成綠燈。下面把那條路釘死。


def test_一輪認不出題號_混在正常輪裡也要吵(tmp_path: Path) -> None:
    """**只認出 1 題而實際好幾題** —— 整份不會掉到 0,所以 exit 3 那條救不了它。
    這種混合形狀要靠逐輪的「異常不適用」把離開碼頂成 1。"""
    run = _mkrun(tmp_path, {
        "r1-questions.md": "**Q1.** 甲\n",
        "r2-questions.md": "| a | b |\n|---|---|\n| 甲 | `[Q1]` |\n\n**Q2:** 乙\n",
        "r3-questions.md": "| a | b |\n|---|---|\n| 乙 | `[Q2]` |\n\n**Q3.** 丙\n",
    })
    rep = lc.check(run)
    assert _round(rep, 1)["status"] == "compared" and rep["missing_total"] == 0
    r2 = _round(rep, 2)
    assert r2["status"] == "not_applicable" and r2["na_kind"] == "no_questions"
    assert r2["near_miss"] == [2]
    # 漏接 0,但**不准是綠燈** —— 第 2 輪根本沒被查過。
    assert lc.main(["x", str(run)]) == 1


def test_近似寫法混在認得出來的輪裡也吵得出來(tmp_path: Path) -> None:
    """同一輪裡 `**Q1.` 與 `**Q2:` 併存:第 1 題查得到,第 2 題**靜靜地不存在**。
    集合相減會漏掉這種,所以近似比的是**位置**。"""
    run = _mkrun(tmp_path, {
        "r1-questions.md": "**Q1.** 甲\n\n**Q2:** 乙\n",
        "r2-questions.md": "| a | b |\n|---|---|\n| 甲 | `[Q1]` |\n\n**Q3.** 丙\n",
    })
    rep = lc.check(run)
    assert _round(rep, 1)["asked"] == [1] and _round(rep, 1)["near_miss"] == [2]
    assert rep["missing_total"] == 0        # 查得到的那一題確實通過
    assert lc.main(["x", str(run)]) == 1    # 但認不出來的那一題要吵


def test_異常摘要不准把比對過的輪講成不適用(tmp_path: Path,
                                          capsys: pytest.CaptureFixture[str]) -> None:
    """第 1 輪**比對過而且通過了**,只是同一輪另有一個認不出來的寫法。

    小計那句「其中 N 輪是異常的不適用」要是把它也算進去,就是又寫了一次**假理由**
    —— 而假理由正是這一輪要修的東西(稽核 §三.2)。近似那件事印在
    【題號寫法可能漂了】,不混進不適用的摘要;離開碼那邊照樣算進去。
    """
    run = _mkrun(tmp_path, {
        "r1-questions.md": "**Q1.** 甲\n\n**Q2:** 乙\n",
        "r2-questions.md": "| a | b |\n|---|---|\n| 甲 | `[Q1]` |\n\n**Q3.** 丙\n",
    })
    assert lc.main(["x", str(run)]) == 1
    out = capsys.readouterr().out
    assert "異常的不適用" not in out          # 一輪不適用都沒有 —— 這句根本不該出現
    assert "【題號寫法可能漂了】" in out       # 但近似要吵得出來
    assert "涵蓋 1 輪" in out                  # 不適用的只有最後那一輪(r2)


def test_引用形式不算近似寫法() -> None:
    """`[Q7]`、散文裡的 `Q7` 都不是**粗體**題號 —— 近似只認粗體,不然整份語料都會亮。"""
    assert lc.near_misses("`[Q7]` 你只用兩種狀態 → 推導自[Q7][Q13];Q9 也提過") == []
    assert lc.near_misses("**Q7:** 這才是") == [7]
    assert lc.near_misses("**Q11.** 這個認得出來,不算近似") == []


# ── 輪次斷號:理由字串要說實話(2026-08-18 稽核 §三.2)──────────────────

def test_輪次斷號的不適用_理由不准謊稱是最後一輪(tmp_path: Path) -> None:
    """只有 r1、r3、r4 時,第 1 輪比不了 —— 但它**顯然不是最後一輪**。

    原本印的是「沒有 r2-questions.md(最後一輪)」:分類沒錯、沒折進通過,
    **但理由是假的**,而讀報表的人拿不到票。
    """
    run = _mkrun(tmp_path, {
        "r1-questions.md": "**Q1.** 甲\n",
        "r3-questions.md": "**Q3.** 丙\n",
        "r4-questions.md": "| a | b |\n|---|---|\n| 丙 | `[Q3]` |\n\n**Q4.** 丁\n",
    })
    rep = lc.check(run)
    r1 = _round(rep, 1)
    assert r1["na_kind"] == "gap" and r1["anomalous"]
    assert "最後一輪" not in r1["reason"] and "輪次斷號" in r1["reason"]
    assert _round(rep, 4)["na_kind"] == "last_round"   # 這一輪才是真的最後一輪
    assert lc.main(["x", str(run)]) == 1                # 有洞就不准是綠燈
