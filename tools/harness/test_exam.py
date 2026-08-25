"""`exam.py` 的測試(票 25)—— 考卷本身要全部命中,而考卷的機制也要有人守。

兩層:

1. **每個 case 一支測試**(parametrize 自 `fixtures/exams/`):落空的 case 逐個翻紅,
   不是一支大測試紅了再去翻表。
2. **機制**:零 case 是 3 不是 0;落空真的會回 1(閘門不是無條件回 0);「無考卷」佇列
   真的列得出沒考卷的檢查器;四支第一批的檢查器各自蓋到 0 / 1 / 3 三個離開碼
   (`provenance_check` 沒有 1 —— 它的離開碼表裡沒有那個碼,考卷不替它發明一個)。

預測寫在 `.scratch/ddd-harness/25-PREDICTION.md`,對答案在 `25-RESULT.md`。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import exam  # noqa: E402

CASES = exam.discover(exam.EXAMS)
FIRST_BATCH = ("landing_check", "provenance_check", "glossary_check", "contract_triage")


# ── 每個 case 一支 ────────────────────────────────────────────────────────

@pytest.mark.parametrize("checker,case_dir", CASES,
                         ids=[f"{c}/{d.name}" for c, d in CASES])
def test_case_命中(checker: str, case_dir: Path) -> None:
    v = exam.run_case(checker, case_dir)
    assert v.hit, "\n".join(v.misses)


def test_有考卷可跑() -> None:
    """零 case 的測試套件會靜靜地全綠 —— 先釘住「真的有東西被跑到」。"""
    assert len(CASES) >= 12, [f"{c}/{d.name}" for c, d in CASES]


def test_第一批四支各自蓋到三個離開碼() -> None:
    exits: dict[str, set[int]] = {}
    for checker, case_dir in CASES:
        exp = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))
        exits.setdefault(checker, set()).add(exp["exit"])
    for checker in FIRST_BATCH:
        assert checker in exits, f"{checker} 沒有考卷"
        assert {0, 3} <= exits[checker], (checker, exits[checker])   # clean + 不適用
    # 已知陽性:三支是 1;provenance 的離開碼表沒有 1,它的陽性是 0 + 印出指定值。
    for checker in ("landing_check", "glossary_check", "contract_triage"):
        assert 1 in exits[checker], (checker, exits[checker])
    assert 1 not in exits["provenance_check"]


def test_題號寫法漂掉那個case必須在() -> None:
    """PIPELINE 幕一 2026-08-18 的實測:`**Q1.` 改成 `**Q1:` 之後整份靜靜地變 0 題。"""
    names = {d.name for c, d in CASES if c == "landing_check"}
    assert "question-mark-drift" in names
    r1 = (exam.EXAMS / "landing_check/question-mark-drift/run/rounds/r1-questions.md"
          ).read_text(encoding="utf-8")
    assert "**Q1:" in r1 and "**Q1." not in r1


# ── 機制 ─────────────────────────────────────────────────────────────────

def test_整份跑完是零() -> None:
    assert exam.main(["exam.py"]) == 0


def test_零case是不適用不是通過(tmp_path: Path, capsys) -> None:
    (tmp_path / "landing_check").mkdir()          # 有目錄、沒有任何 expected.json
    assert exam.main(["exam.py", str(tmp_path)]) == 3
    out = capsys.readouterr().out
    assert "一個 case 都沒有" in out
    assert "整份不適用,不是通過" in out


def test_落空真的會回1(tmp_path: Path, capsys) -> None:
    """閘門不是無條件回 0:一個預期 0、實際 2 的 case 要讓整份回 1,而且表裡寫得出是哪一項。"""
    case = tmp_path / "landing_check" / "wrong-expectation"
    case.mkdir(parents=True)
    (case / "expected.json").write_text(json.dumps({
        "args": ["nowhere"], "exit": 0,
        "must_print": ["這句話檢查器不會印"], "must_not_print": ["找不到"],
    }), encoding="utf-8")
    assert exam.main(["exam.py", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "離開碼:預期 0、實際 2" in out
    assert "該印沒印(漏抓)" in out
    assert "不該印卻印了" in out


def test_已知假陽性不見了也算落空(tmp_path: Path) -> None:
    """`false_positives` 釘的是「今天會印」。它消失 = 行為變了 = 要人去改 expected,不是靜靜地過。"""
    case = tmp_path / "provenance_check" / "fp-gone"
    case.mkdir(parents=True)
    (case / "SPEC.md").write_text("總額 12000 元 [Q1]\n", encoding="utf-8")
    (case / "run" / "rounds").mkdir(parents=True)
    (case / "run" / "rounds" / "r1-answers.md").write_text("總額 12000 元\n", encoding="utf-8")
    (case / "expected.json").write_text(json.dumps({
        "args": ["run", "SPEC.md"], "exit": 0,
        "false_positives": ["值 '12000' 沒出現在需求方的任何回答裡"],
    }), encoding="utf-8")
    v = exam.run_case("provenance_check", case)
    assert not v.hit and any("已知假陽性不見了" in m for m in v.misses), v.misses


def test_壞掉的expected是落空不是炸掉(tmp_path: Path) -> None:
    case = tmp_path / "landing_check" / "broken"
    case.mkdir(parents=True)
    (case / "expected.json").write_text("{not json", encoding="utf-8")
    v = exam.run_case("landing_check", case)
    assert not v.hit and "讀不出來" in v.misses[0]


def test_無考卷佇列列的是沒考卷的檢查器() -> None:
    queue = exam.no_exam_queue(exam.EXAMS)
    for checker in FIRST_BATCH:
        assert checker not in queue
    # 今天唯一沒考卷的 `*_check.py`。它有考卷的那天這條要改 —— 那是好事,不是這支壞了。
    assert "package_landing_check" in queue


def test_考卷指不到檢查器算落空(tmp_path: Path) -> None:
    case = tmp_path / "renamed_check" / "any"
    case.mkdir(parents=True)
    (case / "expected.json").write_text(json.dumps({"args": [], "exit": 0}), encoding="utf-8")
    assert exam.orphan_exams(tmp_path) == ["renamed_check"]
    v = exam.run_case("renamed_check", case)
    assert not v.hit and "指不到檢查器" in v.misses[0]


def test_找不到考卷根目錄是用法錯誤(tmp_path: Path) -> None:
    assert exam.main(["exam.py", str(tmp_path / "nope")]) == 2
