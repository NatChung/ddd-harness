#!/usr/bin/env python3
"""`harness_lint` 的測試(票 22)—— 每條規則一正一反,fixture 在 `fixtures/`。

`fixtures/clean/` 是一個全綠的 mini repo(一張祖父票、一張新票);每條規則一個同名目錄,
**疊在 clean 上**(只放會出事的那幾個檔)。新舊用 `GIT-DATES.txt` 假裝 git ——
fixture 本身的 git 首次 commit 全是同一天,分不出新舊,所以不能拿真 git 驗祖父條款;
真 git 的管線另外在 tmp repo 裡驗一次(`test_git_first_commit_*`)。

預測在 `.scratch/ddd-harness/22-PREDICTION.md`,寫在第一次對真 repo 跑之前。
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import harness_lint as hl  # noqa: E402

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
REPO = HERE.parents[1]

RULES = [name for name, _ in hl.RULES]


def _mini_repo(tmp_path: Path, overlay: str | None) -> tuple[Path, hl.DateProvider]:
    """clean 疊上 overlay;兩份 GIT-DATES.txt 串起來,後寫的蓋前面的。"""
    root = tmp_path / "repo"
    shutil.copytree(FIXTURES / "clean", root)
    dates_text = (FIXTURES / "clean" / "GIT-DATES.txt").read_text(encoding="utf-8")
    if overlay:
        src = FIXTURES / overlay
        assert src.is_dir(), f"fixture 缺 {overlay}/"
        shutil.copytree(src, root, dirs_exist_ok=True)
        extra = src / "GIT-DATES.txt"
        if extra.is_file():
            dates_text += "\n" + extra.read_text(encoding="utf-8")
    (root / "GIT-DATES.txt").write_text(dates_text, encoding="utf-8")
    return root, hl.dates_from_file(root / "GIT-DATES.txt")


def _run(tmp_path: Path, overlay: str | None) -> hl.Report:
    root, dates = _mini_repo(tmp_path, overlay)
    return hl.lint(root, dates)


def _paths(findings: list[hl.Finding], rule: str) -> set[str]:
    return {f.path for f in findings if f.rule == rule}


# ── 正:clean 全綠 ────────────────────────────────────────────────────────

def test_clean_全綠_而且真的掃到了東西(tmp_path: Path) -> None:
    report = _run(tmp_path, None)
    assert report.tickets_scanned == 2 and report.new_tickets == 1
    assert report.active() == []
    assert report.exempt() == []
    assert report.queue() == []


@pytest.mark.parametrize("rule", RULES)
def test_每條規則對clean都零命中(tmp_path: Path, rule: str) -> None:
    report = _run(tmp_path, None)
    assert _paths(report.findings, rule) == set()


# ── 反:每條規則一個 overlay,而且只有它響 ────────────────────────────────

@pytest.mark.parametrize("rule", RULES)
def test_overlay_只有自己那條規則響(tmp_path: Path, rule: str) -> None:
    report = _run(tmp_path, rule)
    others = {f.rule for f in report.findings} - {rule}
    assert others == set(), f"{rule} 的 overlay 讓別條規則也響了:{others}"
    assert _paths(report.findings, rule), f"{rule} 的 overlay 沒讓它響"


def test_ticket_filename_底線與重號都抓(tmp_path: Path) -> None:
    report = _run(tmp_path, "ticket-filename")
    got = _paths(report.active(), "ticket-filename")
    assert got == {
        ".scratch/ddd-harness/issues/03_bad_name.md",
        ".scratch/ddd-harness/issues/02-dup.md",
        ".scratch/ddd-harness/issues/02-new-ticket.md",
    }
    assert report.exempt() == [], "這條祖父=否,不該有豁免"


def test_status_vocabulary_新票resolved計入_舊票A半done豁免(tmp_path: Path) -> None:
    report = _run(tmp_path, "status-vocabulary")
    assert _paths(report.active(), "status-vocabulary") == {".scratch/ddd-harness/issues/02-new-ticket.md"}
    assert _paths(report.exempt(), "status-vocabulary") == {".scratch/ddd-harness/issues/01-old-ticket.md"}


def test_status_single_cell_兩格計入_零格豁免(tmp_path: Path) -> None:
    report = _run(tmp_path, "status-single-cell")
    assert _paths(report.active(), "status-single-cell") == {".scratch/ddd-harness/issues/02-new-ticket.md"}
    assert _paths(report.exempt(), "status-single-cell") == {".scratch/ddd-harness/issues/01-old-ticket.md"}
    msgs = {f.path: f.message for f in report.findings}
    assert "2 個" in msgs[".scratch/ddd-harness/issues/02-new-ticket.md"]
    assert "沒有" in msgs[".scratch/ddd-harness/issues/01-old-ticket.md"]


def test_prediction_before_result_沒預測檔與預測晚於結果都計入(tmp_path: Path) -> None:
    report = _run(tmp_path, "prediction-before-result")
    got = _paths(report.active(), "prediction-before-result")
    assert got == {".scratch/ddd-harness/03-RESULT.md", ".scratch/ddd-harness/01-RESULT.md"}
    assert report.exempt() == [], "這條祖父=否"


def test_prediction_before_run_新票計入_舊票豁免(tmp_path: Path) -> None:
    report = _run(tmp_path, "prediction-before-run")
    assert _paths(report.active(), "prediction-before-run") == {".scratch/ddd-harness/issues/02-new-ticket.md"}
    assert _paths(report.exempt(), "prediction-before-run") == {".scratch/ddd-harness/issues/01-old-ticket.md"}


def test_referenced_run_exists_抓不存在的目錄_不祖父(tmp_path: Path) -> None:
    report = _run(tmp_path, "referenced-run-exists")
    only = [f for f in report.active() if f.rule == "referenced-run-exists"]
    assert len(only) == 1 and "2026-09-09-nope" in only[0].message
    assert report.exempt() == []


def test_blocked_by_resolvable_新票計入_舊票豁免(tmp_path: Path) -> None:
    report = _run(tmp_path, "blocked-by-resolvable")
    assert _paths(report.active(), "blocked-by-resolvable") == {".scratch/ddd-harness/issues/02-new-ticket.md"}
    assert _paths(report.exempt(), "blocked-by-resolvable") == {".scratch/ddd-harness/issues/01-old-ticket.md"}
    assert all("票 9" in f.message or "票 09" in f.message for f in report.active())


def test_convention_undecided_是佇列_不計入離開碼(tmp_path: Path) -> None:
    root, dates = _mini_repo(tmp_path, "convention-undecided")
    report = hl.lint(root, dates)
    queue = report.queue()
    assert {f.path for f in queue} == {
        ".scratch/ddd-harness/issues/01-old-ticket.md",
        ".scratch/ddd-harness/issues/02-new-ticket.md",
    }
    assert {f.grandfathered for f in queue if "01-" in f.path} == {True}
    assert {f.grandfathered for f in queue if "02-" in f.path} == {False}
    assert report.active() == [], "佇列不是判決"


def test_convention_undecided_指了規則名或prose_only就不進佇列(tmp_path: Path) -> None:
    root, dates = _mini_repo(tmp_path, "convention-undecided")
    t02 = root / ".scratch/ddd-harness/issues/02-new-ticket.md"
    t02.write_text(t02.read_text(encoding="utf-8") + "\n由 `status-vocabulary` 守。\n", encoding="utf-8")
    t01 = root / ".scratch/ddd-harness/issues/01-old-ticket.md"
    t01.write_text(t01.read_text(encoding="utf-8") + "\nprose-only, unenforced —— 守不了。\n", encoding="utf-8")
    assert hl.lint(root, dates).queue() == []


def test_ticket_count_in_docs_總數與下一張都查_活票數不查(tmp_path: Path) -> None:
    report = _run(tmp_path, "ticket-count-in-docs")
    got = {(f.path, f.message) for f in report.active() if f.rule == "ticket-count-in-docs"}
    assert {p for p, _ in got} == {"CLAUDE.md:3", "CLAUDE.md:5"}
    assert any("3 張" in m and "實際 2 張" in m for _, m in got)
    assert any("實際到 02,下一張 03" in m for _, m in got)
    # overlay 的 CLAUDE.md 仍寫「1 張還活著」,而 clean 也是 1 —— 就算改成 9 也不會響(刻意不查)
    root, dates = _mini_repo(tmp_path / "b", None)
    doc = root / "CLAUDE.md"
    doc.write_text(doc.read_text(encoding="utf-8").replace("1 張還活著", "9 張還活著"), encoding="utf-8")
    assert hl.lint(root, dates).active() == []


# ── 離開碼 ────────────────────────────────────────────────────────────────

def test_exit_0_clean(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root, dates = _mini_repo(tmp_path, None)
    (root / "GIT-DATES.txt").unlink()
    _git_init_and_commit(root, "2026-08-19T10:00:00")     # 真 git:全部同一天進 → 全祖父
    assert hl.main(["harness_lint.py", str(root)]) == 0
    out = capsys.readouterr().out
    assert "待處理 0 筆" in out and "掃到 2 張票" in out


def test_exit_1_有待處理(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root, _ = _mini_repo(tmp_path, "referenced-run-exists")
    (root / "GIT-DATES.txt").unlink()
    _git_init_and_commit(root, "2026-08-19T10:00:00")
    assert hl.main(["harness_lint.py", str(root)]) == 1
    assert "2026-09-09-nope" in capsys.readouterr().out


def test_exit_2_吃錯目錄(tmp_path: Path) -> None:
    assert hl.main(["harness_lint.py", str(tmp_path)]) == 2
    assert hl.main(["harness_lint.py"]) == 2


def test_exit_3_一張票都沒掃到_不是通過(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / ".scratch/ddd-harness/issues").mkdir(parents=True)
    _git_init_and_commit(tmp_path, "2026-08-19T10:00:00")
    assert hl.main(["harness_lint.py", str(tmp_path)]) == 3
    assert "【不適用】" in capsys.readouterr().out


def test_佇列不動離開碼(tmp_path: Path) -> None:
    root, _ = _mini_repo(tmp_path, "convention-undecided")
    (root / "GIT-DATES.txt").unlink()
    _git_init_and_commit(root, "2026-08-19T10:00:00")
    assert hl.main(["harness_lint.py", str(root)]) == 0


# ── Status 第一個詞的解析:拿真票的寫法驗 ─────────────────────────────────

@pytest.mark.parametrize("line, word", [
    (" needs-triage", "needs-triage"),
    (" **blocked** —— ⚠️ **但解 blocked 的第一項條件**", "blocked"),
    (" reopened(2026-08-18 稍晚,第二份規格上精確度 0%)", "reopened"),
    (" **done**(2026-08-18,選項 B 落地)", "done"),
    (" **A 半 done**(2026-08-18,`domain_contract`)", "A 半 done"),
    (" **resolved**(2026-08-18,決定落成 `docs/adr/0006`)", "resolved"),
    (" done(2026-08-19)—— `harness/run_act4.sh` 已交付。", "done"),
    (" **needs-triage** —— **與票 02 併場 grill**", "needs-triage"),
    (" done-ish(不在詞表)", None),
    (" needs-triage-again", None),
    (" 完成", None),
])
def test_first_status_word(line: str, word: str | None) -> None:
    assert hl.first_status_word(line) == word


def test_run_ref_regex_不把散文當引用() -> None:
    text = "runs/ 底下、`examples/*/harness/runs/`、`runs/<name>`、`runs/2026-08-19-act4/RESULT.md`"
    assert hl.RUN_REF.findall(text) == ["2026-08-19-act4"]


# ── 真 git:首次 commit 日期,不是 mtime ───────────────────────────────────

def _git(root: Path, *args: str, date: str | None = None) -> None:
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    if date:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = date
    subprocess.run(["git", *args], cwd=root, env=env, check=True, capture_output=True)


def _git_init_and_commit(root: Path, date: str) -> None:
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init", "--allow-empty", date=date)


def test_git_first_commit_取最早那筆_而且touch不算(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("a", encoding="utf-8")
    _git_init_and_commit(tmp_path, "2026-08-19T10:00:00+08:00")
    (tmp_path / "a.md").write_text("a2", encoding="utf-8")
    _git(tmp_path, "commit", "-q", "-am", "edit", date="2026-08-30T10:00:00+08:00")
    (tmp_path / "b.md").write_text("b", encoding="utf-8")   # 沒 commit
    os.utime(tmp_path / "a.md", (0, 0))                       # mtime 亂改,不該影響
    dates = hl.git_first_commit(tmp_path)
    assert dates(tmp_path / "a.md") == "2026-08-19"
    assert dates(tmp_path / "b.md") is None


def test_git_不可用時_不標_而且印在上限(tmp_path: Path) -> None:
    root, _ = _mini_repo(tmp_path, "status-vocabulary")
    (root / "GIT-DATES.txt").unlink()
    # 不是 git repo → git log 失敗 → 祖父=是的規則全當祖父
    report = hl.lint(root)
    assert report.git_available is False
    assert report.active() == []
    assert _paths(report.exempt(), "status-vocabulary") == {
        ".scratch/ddd-harness/issues/01-old-ticket.md", ".scratch/ddd-harness/issues/02-new-ticket.md"}
    assert any("git 不可用" in lim for lim in report.limits)


def test_還沒commit的檔算新票(tmp_path: Path) -> None:
    root, _ = _mini_repo(tmp_path, None)
    (root / "GIT-DATES.txt").unlink()
    _git_init_and_commit(root, "2026-08-19T10:00:00")
    t03 = root / ".scratch/ddd-harness/issues/03-fresh.md"
    t03.write_text("# 03\n\n**Status:** resolved\n", encoding="utf-8")
    report = hl.lint(root)
    assert _paths(report.active(), "status-vocabulary") == {".scratch/ddd-harness/issues/03-fresh.md"}


# ── 完成的定義:對真 repo 跑,祖父=否的規則零命中 ─────────────────────────

def test_真repo_祖父否的規則零命中() -> None:
    report = hl.lint(REPO)
    assert report.tickets_scanned >= 27
    no_gf = [f for f in report.active() if f.rule not in hl.GRANDFATHERED_RULES]
    assert no_gf == [], "\n".join(f"[{f.rule}] {f.path}:{f.message}" for f in no_gf)
