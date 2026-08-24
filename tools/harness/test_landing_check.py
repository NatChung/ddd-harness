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

REPO = Path(__file__).resolve().parents[2]
RUNS = REPO / "examples/shop/harness/runs"
OPUS = RUNS / "2026-08-18-act1-opus-rerun"
ROLEPLAY = RUNS / "2026-08-18-act1-haiku-roleplay/roleplay"
SMOKE = RUNS / "2026-08-18-act1-haiku-roleplay/smoke"
INTERVIEW = RUNS / "2026-08-18-act1-interview"


def _round(rep: dict, n: int) -> dict:
    return next(r for r in rep["rounds"] if r["round"] == n)


# ── 預測的四組數字(逐份釘死)────────────────────────────────────────────

def test_opus_全部有落點_而且最後一輪是不適用() -> None:
    """預測:15 通過 / 0 漏接 / R4 的 5 題不適用。

    **一個只會印非 0 的檢查跟只會印 0 的一樣沒用** —— opus 這份就是它印得出 0 的證明,
    而下面 haiku 那份同時印得出 8。
    """
    rep = lc.check(OPUS)
    assert (rep["landed_total"], rep["missing_total"]) == (15, 0)
    assert rep["comparable_rounds"] == 3 and rep["asked_total"] == 15
    assert _round(rep, 4)["status"] == "not_applicable" and rep["na_total"] == 5
    assert lc.main(["x", str(OPUS)]) == 0


def test_haiku_roleplay_漏掉整整兩輪() -> None:
    """**本票的已知陽性。** 預測:漏接 Q1–Q4、Q8–Q11(8 題),通過 Q5–Q7(3 題)。

    漏的原因不是「記錯了」,是那兩輪的下一輪**開頭連一張表都沒有**。
    """
    rep = lc.check(ROLEPLAY)
    missing = {q for r in rep["rounds"] for q in r["missing"]}
    landed = {q for r in rep["rounds"] for q in r["landed"]}
    assert missing == {1, 2, 3, 4, 8, 9, 10, 11}
    assert landed == {5, 6, 7}
    assert (rep["missing_total"], rep["landed_total"]) == (8, 3)
    assert _round(rep, 1)["rows"] == 0 and _round(rep, 3)["rows"] == 0
    assert _round(rep, 2)["rows"] > 0  # 有表的那一輪,表是真的被讀到
    assert _round(rep, 4)["status"] == "not_applicable"
    assert lc.main(["x", str(ROLEPLAY)]) == 1


def test_haiku_smoke_第一輪五題全滅() -> None:
    """預測:漏接 Q1–Q5,R2 不適用。

    smoke 這份的 `r2-questions.md` **有** markdown 表格(盤點、未答追蹤),
    但都在問題**之後** —— 那不是落點表。判準要是寫成「檔案裡有表就算」,這 5 題會假通過。
    """
    rep = lc.check(SMOKE)
    assert {q for r in rep["rounds"] for q in r["missing"]} == {1, 2, 3, 4, 5}
    assert rep["landed_total"] == 0 and rep["comparable_rounds"] == 1
    assert _round(rep, 2)["status"] == "not_applicable"
    assert lc.main(["x", str(SMOKE)]) == 1


def test_沒有逐輪提問檔_不算通過() -> None:
    """**「找不到東西所以沒問題」是最廉價的假綠燈**(票 03 的教訓)。

    `2026-08-18-act1-interview` 的 `rounds/` 只落了 answers,一個 questions 檔都沒有
    —— 報表要說「不是乾淨」,而且 exit 非 0。

    ⚠️ 離開碼 2026-08-18 稽核後從 1 改成 **3**(整份不適用),跟 `contract_triage` /
       `glossary_check` 對齊:1 = 有問題(漏接 / 掃到卻掃錯)、3 = 一輪都比不了。
       05-PREDICTION 對這份只釘了「exit ≠ 0」,沒有釘 1 —— 凍結的預測沒有被動到。
    """
    rep = lc.check(INTERVIEW)
    assert rep["comparable_rounds"] == 0 and rep["rounds"] == []
    assert lc.main(["x", str(INTERVIEW)]) == 3


# ── 「不適用」不准折進「通過」(ADR 0005 §6)────────────────────────────

def test_不適用印在最上面而且明講不是通過(capsys: pytest.CaptureFixture[str]) -> None:
    """守衛沒有壞掉,是不再適用了,而**不適用不會有人發現** —— 除非把它印在第一個。"""
    lc.main(["x", str(OPUS)])
    out = capsys.readouterr().out
    assert "【不適用】—— 不是通過,沒有被檢查過" in out
    assert out.index("【不適用】") < out.index("【漏接】") < out.index("【通過】")
    assert "不適用(未檢查)" in out
    # 不適用的題數不得被加進通過
    assert "通過 15、漏接 0" in out and "另有 5 題不適用" in out


def test_報表自己印出已知上限(capsys: pytest.CaptureFixture[str]) -> None:
    """**讀報表的人拿不到票**,所以「題號出現 ≠ 記對了」要印在報表裡。"""
    lc.main(["x", str(OPUS)])
    out = capsys.readouterr().out
    assert "題號出現 ≠ 記對了" in out
    assert "抓不到「記成別的意思」" in out
    assert "最後一輪是「不適用」,不是「通過」" in out


# ── §11 收尾表:參考,不進判定 ──────────────────────────────────────────

def test_收尾表不進判定不影響退出碼(capsys: pytest.CaptureFixture[str]) -> None:
    """§11 那張表是**訪談者自己寫的**:它宣稱 20 題全有落點,包含最後一輪那 5 題。

    要是拿它去補,最後一輪就會從「不適用」變成「通過」—— 那是被否掉的選項 C
    從後門溜回來。所以它只印、不算。
    """
    spec = OPUS / "SPEC-draft.md"
    assert lc.spec_log_questions(spec.read_text(encoding="utf-8")) == list(range(1, 21))
    assert lc.main(["x", str(OPUS), str(spec)]) == lc.main(["x", str(OPUS)]) == 0
    out = capsys.readouterr().out
    assert "【參考,不進判定】" in out and "不進計數、不影響 exit code" in out
    assert "另有 5 題不適用" in out  # 收尾表沒有把它補成通過


def test_沒有第十一節就沒有參考區塊() -> None:
    assert lc.spec_log_questions("## §9 ARCHITECTURE\n\n| a | b |\n|---|---|\n| Q3 | x |") == []


# ── 明確答「沒有 / 還沒想過」也算落點 ────────────────────────────────────

def test_答沒有也算落點() -> None:
    """Q8 的答案是「**沒有**,倉庫會計都人工處理」;Q3 是「還沒有很仔細想過」。

    這兩題**照樣通過** —— 它們該進 §4 或未答追蹤,不是消失。
    判準要是改成「有實質內容才算」,誠實回答「沒有」的那一輪反而會被記成漏接。
    """
    rep = lc.check(OPUS)
    assert 8 in _round(rep, 2)["landed"]
    assert 3 in _round(rep, 1)["landed"]


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


def test_散文提一句不算落點(tmp_path: Path) -> None:
    """haiku `r4-questions.md` 的真實開頭就是「好的,收到了 Q8 到 Q11 的回答」——
    這句話裡 Q9、Q10 **一次都沒出現**,而 Q8、Q11 出現了。

    要是判準放寬成「開頭提到就算」,同一輪會出現「Q8 通過、Q9 漏接」這種
    **由句型決定的判定** —— 那不是判準,是抽籤。
    """
    head = (ROLEPLAY / "rounds/r4-questions.md").read_text(encoding="utf-8")[:60]
    assert "Q8" in head and "Q11" in head and "Q9" not in head
    assert lc.landing_rows(head) == []  # 散文不是表 → 一列都沒有


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


def _drifted_opus(tmp_path: Path) -> Path:
    """把 opus 那份真實 run 複製一份,**只**把題號寫法 `**Qn.` 換成 `**Qn:`。

    這不是我編的形狀:訪談者換個標點就會這樣。而且破壞本身要先驗 ——
    改了幾個檔、幾處,當場斷言(不然又是一個「破壞沒生效卻以為驗過了」)。
    """
    import re as _re
    import shutil
    dst = tmp_path / "opus-drifted"
    shutil.copytree(OPUS, dst)
    files = hits = 0
    for p in sorted((dst / "rounds").glob("r*-questions.md")):
        text = p.read_text(encoding="utf-8")
        new, n = _re.subn(r"(\*\*Q\d+)\.", r"\1:", text)
        if n:
            p.write_text(new, encoding="utf-8")
            files += 1
            hits += n
    assert (files, hits) == (4, 20), f"mutated 沒生效:改到 {files} 檔 / {hits} 處"
    return dst


def test_題號寫法漂掉的run_不算通過而是整份不適用(tmp_path: Path) -> None:
    """**這是原本那條靜默綠燈。** 15 題的 run,只換一個標點:

        小計:可比對 3 輪 / 0 題;通過 0、漏接 0  ← 然後 exit 0

    修法:「一題都沒認出來」是**不適用**,不是通過;而一輪都比不了 = 整份不適用,
    離開碼 3(跟「有漏接」的 1 分得開)。
    """
    run = _drifted_opus(tmp_path)
    rep = lc.check(run)

    assert rep["asked_total"] == 0
    assert rep["comparable_rounds"] == 0          # 三輪全部掉出 compared
    for n in (1, 2, 3):
        r = _round(rep, n)
        assert r["status"] == "not_applicable" and r["na_kind"] == "no_questions"
        assert r["anomalous"]
    assert _round(rep, 4)["na_kind"] == "last_round"   # 最後一輪仍是預期之內
    assert rep["near_miss_total"] == 20                # 漂掉的寫法真的被看見了
    assert lc.main(["x", str(run)]) == 3


def test_整份不適用的離開碼跟有漏接分得開() -> None:
    """3 = 一輪都比不了;1 = 有漏接。並排跑時只看離開碼也分得出來 ——
    不然 CI 會把「什麼都沒查」讀成「全過」。"""
    assert lc.main(["x", str(INTERVIEW)]) == 3      # 一個提問檔都沒有
    assert lc.main(["x", str(SMOKE)]) == 1          # 有漏接
    assert lc.main(["x", str(OPUS)]) == 0           # 真的全過


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


def test_近似寫法在四份真實語料上不假陽性() -> None:
    """近似偵測要是對真資料亂吵,它就會被關掉 —— 先釘住它在四份真實 run 上是安靜的。"""
    for run in (OPUS, ROLEPLAY, SMOKE):
        assert lc.check(run)["near_miss_total"] == 0, run


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
