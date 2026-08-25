#!/usr/bin/env python3
"""`na_ratio.py`(不適用比率儀表)與兩支 runner 開頭那一行的測試(票 26)。

刻意跟 `test_harness.py` / `test_check_ledger.py` 分開(票的要求)。帳本全部合成,
形狀照 `check.py` 每行五個欄位;**格式歸票 21,這裡只讀**。

最重要的三條:
* 超過門檻印 ⚠️ 但**離開碼仍是 0** —— 它是儀表不是閘門;
* 零帳本 → 3,不是 0(沒東西可統計不是乾淨);
* 讀不動的行跳過並計數,不 crash;帳本在但一筆都讀不動 → 一樣 3。

runner 那一行走 dry-run(`ACT2_DRY_RUN` / `ACT4_DRY_RUN`),掃描根用 `NA_RATIO_ROOT` 指到合成語料;
na_ratio 失敗(掃描根不存在)runner 照樣 0。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import check as ck  # noqa: E402
import exam  # noqa: E402
import na_ratio as nr  # noqa: E402

HARNESS = Path(__file__).resolve().parent
NA_RATIO = HARNESS / "na_ratio.py"
ACT2 = HARNESS / "run_act2.sh"
ACT4 = HARNESS / "run_act4.sh"


# ── 語料 ─────────────────────────────────────────────────────────────

def _entry(checker: str, code: int, day: int = 25, hour: int = 0) -> dict:
    return {"checker": checker, "argv": ["run"], "exit": code,
            "ts": f"2026-08-{day:02d}T{hour:02d}:00:00+00:00", "cwd": "/x"}


def _ledger(run_dir: Path, *entries: dict, raw_tail: str = "") -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / ck.LEDGER_NAME
    path.write_text("".join(json.dumps(e) + "\n" for e in entries) + raw_tail, encoding="utf-8")
    return path


def _old_run(run_dir: Path) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _run(*args, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([str(a) for a in args], capture_output=True, text=True, cwd=cwd,
                          env={**os.environ, **(env or {})})


def _py(*args, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return _run(sys.executable, NA_RATIO, *args, cwd=cwd)


def _over_threshold_root(tmp_path: Path) -> Path:
    """landing_check 6 跑、不適用 4 次(67%),最近連續 2 → 預設門檻下要 ⚠️。"""
    runs = tmp_path / "examples" / "demo" / "harness" / "runs"
    for day, code in enumerate((0, 3, 3, 0, 3, 3), start=20):
        _ledger(runs / f"2026-08-{day}-act1", _entry("landing_check", code, day))
    return tmp_path / "examples"


# ── 讀帳本:loss-tolerant ────────────────────────────────────────────

def test_讀不動的行跳過並計數_不crash(tmp_path: Path) -> None:
    path = _ledger(tmp_path / "run", _entry("landing_check", 0),
                   raw_tail='garbage\n{"checker": 1, "exit": 0}\n{"checker": "x", "exit": "3"}\n'
                            '{"checker": "y", "exit": true}\n[]\n\n')
    entries, bad = nr.read_ledger_lossy(path)
    assert [e.checker for e in entries] == ["landing_check"]
    assert bad == 5          # 非 JSON / checker 不是字串 / exit 是字串 / exit 是 bool / 不是 dict


def test_ts缺了當最舊_不炸(tmp_path: Path) -> None:
    e = _entry("landing_check", 3)
    del e["ts"]
    path = _ledger(tmp_path / "run", e, _entry("landing_check", 0, 26))
    entries, bad = nr.read_ledger_lossy(path)
    assert bad == 0 and entries[0].ts == ""
    s = nr.Stats("landing_check", entries)
    assert s.na_streak == 0  # 缺 ts 那筆排最前,最近那筆是 0


# ── 統計 ─────────────────────────────────────────────────────────────

def test_連續不適用依ts排_不依檔案順序(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    # 檔案順序 a → b,但 b 裡的 26(exit 0)依 ts 落在 a 的 27、28 之前:
    # 照檔案順序算會得到 0(b 的最後一筆是 25 的 3 → 1),照 ts 算是 2。
    _ledger(runs / "a", _entry("landing_check", 3, 27), _entry("landing_check", 3, 28))
    _ledger(runs / "b", _entry("landing_check", 0, 26), _entry("landing_check", 3, 25))
    r = nr.collect([tmp_path])
    s = r.stats["landing_check"]
    assert s.runs == 4 and s.count(3) == 3 and s.count(0) == 1
    assert s.na_streak == 2      # 27、28 兩筆;26 那筆 0 斷開;25 那筆不算


def test_門檻是嚴格大於_且要達min_runs() -> None:
    s = nr.Stats("x", [nr.Entry("x", c, "", "") for c in (3, 3, 0, 0, 0, 0, 0, 0)])  # 2/8 = 25%
    assert s.na_ratio == 0.25
    assert not s.over(0.25, 5)               # 剛好等於門檻,不算超過
    assert s.over(0.24, 5)
    assert not s.over(0.24, 9)               # 跑過 8 < min-runs 9
    assert nr.Stats("y", [nr.Entry("y", 3, "", "")]).over(0.25, 1)


def test_其他離開碼歸其他_不折進0或3() -> None:
    s = nr.Stats("x", [nr.Entry("x", c, "", "") for c in (2, 66, 0, 3, 1)])
    assert (s.count(0), s.count(1), s.count(3), s.other) == (1, 1, 1, 2)


def test_舊run印張數_不進分母(tmp_path: Path) -> None:
    runs = tmp_path / "examples" / "demo" / "harness" / "runs"
    _ledger(runs / "2026-08-26-act1", _entry("landing_check", 3))
    _old_run(runs / "2026-08-18-act1")
    _old_run(runs / "2026-08-19-act2")
    (tmp_path / "examples" / "demo" / "not-a-run").mkdir()   # 不在 runs/ 底下的目錄不算舊 run
    r = nr.collect([tmp_path / "examples"])
    assert len(r.ledgers) == 1 and len(r.old_runs) == 2
    assert r.stats["landing_check"].runs == 1


def test_略過點開頭與build目錄(tmp_path: Path) -> None:
    _ledger(tmp_path / ".git" / "runs" / "x", _entry("landing_check", 3))
    _ledger(tmp_path / "build" / "runs" / "y", _entry("landing_check", 3))
    _ledger(tmp_path / "runs" / "z", _entry("landing_check", 0))
    r = nr.collect([tmp_path])
    assert len(r.ledgers) == 1 and r.stats["landing_check"].count(3) == 0


def test_同一root給兩次不重複計(tmp_path: Path) -> None:
    _ledger(tmp_path / "runs" / "a", _entry("landing_check", 3))
    r = nr.collect([tmp_path, tmp_path])
    assert len(r.ledgers) == 1 and r.stats["landing_check"].runs == 1


# ── skip 欄(推斷) ────────────────────────────────────────────────────

def test_infer_act_先看skeleton_再spec_db_再spec() -> None:
    assert nr.infer_act({"skeleton": "/s", "spec": "/p", "input_blobs": {}}) == "act4"
    assert nr.infer_act({"spec_db": "/d"}) == "act3"
    assert nr.infer_act({"spec": "/p", "input_blobs": {}}) == "act2"
    assert nr.infer_act({"model": "opus"}) is None


def test_閘門跳過對到該幕要求的檢查器(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    a2 = _old_run(runs / "act2")
    (a2 / nr.META_NAME).write_text(json.dumps({"spec": "/p", "gate_skipped": True, "gate_skip_reason": "r"}))
    a3 = _old_run(runs / "act3")
    (a3 / nr.META_NAME).write_text(json.dumps({"spec_db": "/d", "gate_skipped": True, "gate_skip_reason": "r"}))
    a4 = _old_run(runs / "act4")
    (a4 / nr.META_NAME).write_text(json.dumps({"skeleton": "/s", "spec": "/p", "gate_skipped": True}))
    ok = _old_run(runs / "not-skipped")
    (ok / nr.META_NAME).write_text(json.dumps({"spec": "/p", "gate_skipped": False}))
    unk = _old_run(runs / "unknown-act")
    (unk / nr.META_NAME).write_text(json.dumps({"model": "opus", "gate_skipped": True}))
    bad = _old_run(runs / "bad-meta")
    (bad / nr.META_NAME).write_text("{not json")
    r = nr.collect([tmp_path])
    assert r.skips_total == 4 and r.skips_unmapped == 1
    assert r.stats["landing_check"].skipped == 1
    assert {c for c, _, _ in ck.GATES["act3"]} <= {n for n, s in r.stats.items() if s.skipped == 1}
    assert r.stats["acceptance_gwt"].skipped == 1
    assert r.stats["landing_check"].runs == 0     # skip 不進「跑過」


# ── CLI:離開碼只有 0 / 2 / 3 ─────────────────────────────────────────

def test_超過門檻印警告_但離開碼是0(tmp_path: Path) -> None:
    root = _over_threshold_root(tmp_path)
    proc = _py(root)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "⚠️ landing_check:6 跑裡不適用 4 次(67% > 25%" in proc.stdout
    assert "最近連續 2 次" in proc.stdout
    assert "儀表,不是閘門" in proc.stdout


def test_自訂門檻與min_runs(tmp_path: Path) -> None:
    root = _over_threshold_root(tmp_path)
    assert _py("--warn-threshold", "0.7", root).returncode == 0
    assert "⚠️ landing_check" not in _py("--warn-threshold", "0.7", root).stdout
    assert "⚠️ landing_check" not in _py("--min-runs", "7", root).stdout
    assert "⚠️ landing_check" in _py("--min-runs", "6", root).stdout


def test_零帳本是3_不是0(tmp_path: Path) -> None:
    runs = tmp_path / "examples" / "demo" / "harness" / "runs"
    _old_run(runs / "2026-08-18-act1")
    _old_run(runs / "2026-08-19-act2")
    proc = _py(tmp_path / "examples")
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert "一份 check-ledger.jsonl 都沒有 —— 整份不適用,不是通過" in proc.stdout
    assert "舊 run 2 張" in proc.stdout


def test_帳本在但一筆都讀不動_一樣3(tmp_path: Path) -> None:
    _ledger(tmp_path / "runs" / "a", raw_tail="{broken\nnope\n")
    proc = _py(tmp_path)
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert "帳本裡一筆都讀不動" in proc.stdout
    assert "讀不動 2 行" in proc.stdout


def test_用法錯誤是2(tmp_path: Path) -> None:
    assert _py().returncode == 2
    assert _py(tmp_path / "nope").returncode == 2
    assert _py("--warn-threshold", "2", tmp_path).returncode == 2
    assert _py("--min-runs", "0", tmp_path).returncode == 2
    assert _py("--what", tmp_path).returncode == 2


def test_只看一支(tmp_path: Path) -> None:
    root = _over_threshold_root(tmp_path)
    _ledger(root / "demo" / "harness" / "runs" / "2026-08-26-act2", _entry("glossary_check", 1, 26))
    out = _py("--checker", "glossary_check", root).stdout
    assert "glossary_check" in out and "landing_check" not in out.split("--- 上限")[0]
    out = _py("--checker", "nobody", root).stdout
    assert "帳本裡沒有 nobody 的紀錄" in out


# ── --brief:runner 開頭那一行 ─────────────────────────────────────────

def test_brief_一行_照票的措辭(tmp_path: Path) -> None:
    root = _over_threshold_root(tmp_path)
    proc = _py("--brief", "--checker", "landing_check", root)
    assert proc.returncode == 0
    assert proc.stdout.count("\n") == 1
    assert proc.stdout.startswith("na_ratio:⚠️ 上 6 跑 landing_check 不適用 4 次(連續 2)")


def test_brief_零帳本_一行講不適用_離開碼3(tmp_path: Path) -> None:
    _old_run(tmp_path / "runs" / "old")
    proc = _py("--brief", tmp_path)
    assert proc.returncode == 3
    assert proc.stdout.count("\n") == 1
    assert "na_ratio:不適用 —— 沒有任何 check-ledger.jsonl(舊 run 1 張沒帳本" in proc.stdout


def test_brief_用法錯誤不灌docstring(tmp_path: Path) -> None:
    proc = _py("--brief", tmp_path / "nope")
    assert proc.returncode == 2
    assert proc.stderr.count("\n") == 1 and "na_ratio:用法錯誤" in proc.stderr


# ── 考卷(票 25 的形狀) ──────────────────────────────────────────────

NA_CASES = [(c, d) for c, d in exam.discover(exam.EXAMS) if c == "na_ratio"]


def test_考卷至少三個case_蓋到0與3() -> None:
    assert len(NA_CASES) >= 3, [d.name for _, d in NA_CASES]
    exits = {json.loads((d / "expected.json").read_text(encoding="utf-8"))["exit"] for _, d in NA_CASES}
    assert {0, 3} <= exits
    names = {d.name for _, d in NA_CASES}
    assert {"normal", "over-threshold", "no-ledger"} <= names


def test_考卷指得到檢查器_不在無考卷佇列() -> None:
    assert "na_ratio" in exam.checkers()
    assert "na_ratio" not in exam.no_exam_queue(exam.EXAMS)
    assert "na_ratio" not in exam.orphan_exams(exam.EXAMS)


@pytest.mark.parametrize("checker,case_dir", NA_CASES, ids=[d.name for _, d in NA_CASES])
def test_考卷命中(checker: str, case_dir: Path) -> None:
    v = exam.run_case(checker, case_dir)
    assert v.hit, "\n".join(v.misses)


# ── runner 開頭那一行 ──────────────────────────────────────────────────

def _act1(tmp_path: Path) -> tuple[Path, Path]:
    run_dir = tmp_path / "act1"
    run_dir.mkdir()
    spec = run_dir / "SPEC-draft.md"
    spec.write_text("# 規格\n", encoding="utf-8")
    _ledger(run_dir, _entry("landing_check", 0))
    return run_dir, spec


def _skeleton(tmp_path: Path) -> tuple[Path, Path]:
    """照 test_check_ledger.py 的形狀複製(不 import 那個檔):票 24 之後 dry run 也跑 order_check。"""
    skel = tmp_path / "skeleton"
    skel.mkdir()
    (skel / "build.gradle").write_text("// 骨架\n", encoding="utf-8")
    for rel in ("src/test/java/acceptance/OrderAcceptanceTest.java",
                "src/test/java/acceptance/OrderProxyAcceptanceTest.java",
                "src/test/java/architecture/ArchitectureTest.java"):
        (skel / rel).parent.mkdir(parents=True, exist_ok=True)
        (skel / rel).write_text("// 生成物(測試用假檔)\n", encoding="utf-8")
    _ledger(skel, _entry("acceptance_gwt", 0))
    spec = tmp_path / "SPEC.md"
    spec.write_text("# 規格\n", encoding="utf-8")
    return skel, spec


def test_act2_閘門之後印一行(tmp_path: Path) -> None:
    _, spec = _act1(tmp_path)
    root = _over_threshold_root(tmp_path / "corpus")
    proc = _run("bash", ACT2, spec, tmp_path / "work",
                env={"ACT2_DRY_RUN": "1", "NA_RATIO_ROOT": str(root)})
    assert proc.returncode == 0, proc.stdout + proc.stderr
    gate = proc.stdout.index("上一幕的檢查證據齊了")
    line = proc.stdout.index("na_ratio:⚠️ 上 6 跑 landing_check 不適用 4 次")
    assert gate < line                                # 閘門判定之後才印


def test_act2_閘門跳過那條路也印(tmp_path: Path) -> None:
    _, spec = _act1(tmp_path)
    root = _over_threshold_root(tmp_path / "corpus")
    proc = _run("bash", ACT2, spec, tmp_path / "work",
                env={"ACT2_DRY_RUN": "1", "NA_RATIO_ROOT": str(root),
                     "ACT_GATE_SKIP": "1", "ACT_GATE_SKIP_REASON": "測試"})
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "na_ratio:⚠️ 上 6 跑 landing_check" in proc.stdout


def test_act2_na_ratio失敗不讓runner失敗(tmp_path: Path) -> None:
    _, spec = _act1(tmp_path)
    proc = _run("bash", ACT2, spec, tmp_path / "work",
                env={"ACT2_DRY_RUN": "1", "NA_RATIO_ROOT": str(tmp_path / "nowhere")})
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "na_ratio:用法錯誤" in proc.stderr
    assert (tmp_path / "work" / "run-meta.json").exists()


def test_act2_零帳本那行講不適用_runner照跑(tmp_path: Path) -> None:
    _, spec = _act1(tmp_path)
    corpus = tmp_path / "corpus" / "runs" / "old"
    corpus.mkdir(parents=True)
    proc = _run("bash", ACT2, spec, tmp_path / "work",
                env={"ACT2_DRY_RUN": "1", "NA_RATIO_ROOT": str(tmp_path / "corpus")})
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "na_ratio:不適用 —— 沒有任何 check-ledger.jsonl(舊 run 1 張沒帳本" in proc.stdout


def test_act2_閘門拒絕時不印(tmp_path: Path) -> None:
    """儀表在閘門之後:閘門 3 就走了,那一行不該出現。"""
    run_dir = tmp_path / "act1"
    run_dir.mkdir()
    spec = run_dir / "SPEC-draft.md"
    spec.write_text("# 規格\n", encoding="utf-8")
    root = _over_threshold_root(tmp_path / "corpus")
    proc = _run("bash", ACT2, spec, tmp_path / "work",
                env={"ACT2_DRY_RUN": "1", "NA_RATIO_ROOT": str(root)})
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert "na_ratio:" not in proc.stdout


def test_act4_閘門之後印一行_看的是acceptance_gwt(tmp_path: Path) -> None:
    skel, spec = _skeleton(tmp_path)
    corpus = tmp_path / "corpus" / "examples" / "demo" / "harness" / "runs"
    for day, code in enumerate((3, 3, 3, 3, 3), start=20):
        _ledger(corpus / f"2026-08-{day}-act4-skeleton", _entry("acceptance_gwt", code, day))
    _ledger(corpus / "2026-08-26-act1", _entry("landing_check", 3, 26))
    proc = _run("bash", ACT4, spec, skel, tmp_path / "work",
                env={"ACT4_DRY_RUN": "1", "NA_RATIO_ROOT": str(tmp_path / "corpus")})
    assert proc.returncode == 0, proc.stdout + proc.stderr
    gate = proc.stdout.index("上一幕的檢查證據齊了")
    line = proc.stdout.index("na_ratio:⚠️ 上 5 跑 acceptance_gwt 不適用 5 次(連續 5)")
    assert gate < line
    assert "landing_check" not in proc.stdout.split("na_ratio:")[1].splitlines()[0]


def test_act4_na_ratio失敗不讓runner失敗(tmp_path: Path) -> None:
    skel, spec = _skeleton(tmp_path)
    proc = _run("bash", ACT4, spec, skel, tmp_path / "work",
                env={"ACT4_DRY_RUN": "1", "NA_RATIO_ROOT": str(tmp_path / "nowhere")})
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "na_ratio:用法錯誤" in proc.stderr
