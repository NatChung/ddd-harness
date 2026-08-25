#!/usr/bin/env python3
"""`landing_check` 的測試 —— 對**四份 2026-08-18 真實跑出來的 run** 驗,不是對我編的例子驗。

從 `harness/test_landing_check.py` 搬來(票 32):這幾支讀的是
`examples/shop/harness/runs/2026-08-18-act1-*` 四份真實語料,hub 沒有那份語料。
預測寫在 `.scratch/ddd-harness/05-PREDICTION.md`,四份語料的數字逐份寫死。
`_round` 仍是 harness 那份測試檔的,這裡只 import;合成語料的那些測試留在 harness。
"""

from __future__ import annotations

from pathlib import Path

import pytest

import landing_check as lc  # harness/ 由 conftest 放進 sys.path
from test_landing_check import _round

REPO = Path(__file__).resolve().parents[3]
RUNS = REPO / "examples/shop/harness/runs"
OPUS = RUNS / "2026-08-18-act1-opus-rerun"
ROLEPLAY = RUNS / "2026-08-18-act1-haiku-roleplay/roleplay"
SMOKE = RUNS / "2026-08-18-act1-haiku-roleplay/smoke"
INTERVIEW = RUNS / "2026-08-18-act1-interview"


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


# ── 明確答「沒有 / 還沒想過」也算落點 ────────────────────────────────────

def test_答沒有也算落點() -> None:
    """Q8 的答案是「**沒有**,倉庫會計都人工處理」;Q3 是「還沒有很仔細想過」。

    這兩題**照樣通過** —— 它們該進 §4 或未答追蹤,不是消失。
    判準要是改成「有實質內容才算」,誠實回答「沒有」的那一輪反而會被記成漏接。
    """
    rep = lc.check(OPUS)
    assert 8 in _round(rep, 2)["landed"]
    assert 3 in _round(rep, 1)["landed"]


# ── 散文提一句不算落點(真實語料驗得到的那一條)──────────────────────────

def test_散文提一句不算落點(tmp_path: Path) -> None:
    """haiku `r4-questions.md` 的真實開頭就是「好的,收到了 Q8 到 Q11 的回答」——
    這句話裡 Q9、Q10 **一次都沒出現**,而 Q8、Q11 出現了。

    要是判準放寬成「開頭提到就算」,同一輪會出現「Q8 通過、Q9 漏接」這種
    **由句型決定的判定** —— 那不是判準,是抽籤。
    """
    head = (ROLEPLAY / "rounds/r4-questions.md").read_text(encoding="utf-8")[:60]
    assert "Q8" in head and "Q11" in head and "Q9" not in head
    assert lc.landing_rows(head) == []  # 散文不是表 → 一列都沒有


# ── 掃到卻掃錯:靜默綠燈那條路(2026-08-18 稽核 §二.A)────────────────────

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


# ── 近似偵測在真實語料上要安靜 ─────────────────────────────────────────

def test_近似寫法在四份真實語料上不假陽性() -> None:
    """近似偵測要是對真資料亂吵,它就會被關掉 —— 先釘住它在四份真實 run 上是安靜的。"""
    for run in (OPUS, ROLEPLAY, SMOKE):
        assert lc.check(run)["near_miss_total"] == 0, run
