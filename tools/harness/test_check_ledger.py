#!/usr/bin/env python3
"""`check.py`(檢查帳本 + 閘門)與三支 runner 開頭閘門的測試(票 21)。

刻意跟 `test_harness.py` 分開(票的要求)。三支 runner 都用 subprocess 真的跑 bash,
走 dry-run 那條路(`ACT2_DRY_RUN` / `ACT4_DRY_RUN`),不呼叫 claude。

最重要的一條是 `test_P1_帳本裡的3不算通過`:閘門判準是 `exit == 0`,不是 `exit != 1`。
寫成 `exit in (0, 3)` 就把「守衛靜靜不再適用」放行了 —— 預測檔第一條釘的就是它。
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

HARNESS = Path(__file__).resolve().parent
REPO = HARNESS.parents[1]
CHECK = HARNESS / "check.py"
ACT2 = HARNESS / "run_act2.sh"
ACT3 = HARNESS / "run_act3.sh"
ACT4 = HARNESS / "run_act4.sh"


def _run(*args: str, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(a) for a in args], capture_output=True, text=True, cwd=cwd,
        env={**os.environ, **(env or {})},
    )


def _py(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return _run(sys.executable, CHECK, *args, cwd=cwd)


def _stub(tmp_path: Path) -> Path:
    """一支「叫我回幾就回幾」的假檢查器 —— 只為了測包裝器,不測任何真檢查器。"""
    stub = tmp_path / "stub_checker.py"
    stub.write_text("import sys\nsys.exit(int(sys.argv[1]))\n", encoding="utf-8")
    return stub


def _entry(checker: str, code: int, *argv: str) -> dict:
    return {"checker": checker, "argv": list(argv), "exit": code,
            "ts": "2026-08-25T00:00:00+00:00", "cwd": "/x"}


def _ledger(run_dir: Path, *entries: dict) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / ck.LEDGER_NAME
    path.write_text("".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8")
    return path


def _read(run_dir: Path) -> list[dict]:
    return [json.loads(l) for l in (run_dir / ck.LEDGER_NAME).read_text(encoding="utf-8").splitlines() if l]


# ── 包裝器:記帳 ─────────────────────────────────────────────────────

def test_包裝器記五個欄位_離開碼原樣傳出(tmp_path: Path) -> None:
    stub = _stub(tmp_path)
    run_dir = tmp_path / "run"
    proc = _py("--run-dir", str(run_dir), str(stub), "3", cwd=tmp_path)
    assert proc.returncode == 3, proc.stderr
    (e,) = _read(run_dir)
    assert set(e) == {"checker", "argv", "exit", "ts", "cwd"}
    assert e["checker"] == "stub_checker"      # 模組名,不帶 .py、不帶路徑
    assert e["argv"] == ["3"]
    assert e["exit"] == 3
    assert e["cwd"] == str(tmp_path.resolve())
    assert e["ts"].endswith("+00:00")


def test_連續記帳是追加不是覆蓋(tmp_path: Path) -> None:
    stub = _stub(tmp_path)
    run_dir = tmp_path / "run"
    for code in ("1", "0", "3"):
        _py("--run-dir", str(run_dir), str(stub), code)
    assert [e["exit"] for e in _read(run_dir)] == [1, 0, 3]


def test_run_dir_從argv推_第一個存在的目錄(tmp_path: Path) -> None:
    """真檢查器:landing_check 吃一個空目錄。離開碼是多少不重要(它會說吃錯目錄或不適用),
    重要的是帳本落在**那個目錄**、記的離開碼跟實際一樣。"""
    run_dir = tmp_path / "act1"
    run_dir.mkdir()
    proc = _py("landing_check", str(run_dir))
    (e,) = _read(run_dir)
    assert e["checker"] == "landing_check"
    assert e["exit"] == proc.returncode != 0


def test_run_dir_沒有目錄參數就取第一個檔案的上層(tmp_path: Path) -> None:
    stub = _stub(tmp_path)
    run_dir = tmp_path / "act2"
    run_dir.mkdir()
    db = run_dir / "spec.db"
    db.write_text("")
    # stub 忽略第二個參數;第一個參數 0 不是路徑,第二個是檔案 → 上層 = act2
    proc = _py(str(stub), "0", str(db))
    assert proc.returncode == 0
    assert (run_dir / ck.LEDGER_NAME).exists()


def test_run_dir_推不到就是2_而且不寫帳(tmp_path: Path) -> None:
    stub = _stub(tmp_path)
    proc = _py(str(stub), "0", cwd=tmp_path)
    assert proc.returncode == 2
    assert "--run-dir" in proc.stderr
    assert not (tmp_path / ck.LEDGER_NAME).exists()   # 不退到 cwd


def test_找不到檢查器是2(tmp_path: Path) -> None:
    proc = _py("--run-dir", str(tmp_path), "no_such_checker")
    assert proc.returncode == 2
    assert not (tmp_path / ck.LEDGER_NAME).exists()


# ── 閘門:純函數 ─────────────────────────────────────────────────────

def test_P1_帳本裡的3不算通過() -> None:
    """**預測檔第一條。** 不適用 ≠ 通過:有紀錄、但那筆是 3 → 閘門回 1,不回 0。"""
    code, _ = ck.gate("act2", [_entry("landing_check", 3)])
    assert code == 1
    code, _ = ck.gate("act4", [_entry("acceptance_gwt", 3)])
    assert code == 1
    code, _ = ck.gate("act3", [
        _entry("spec_store", 3, "import"), _entry("provenance_check", 0),
        _entry("contract_triage", 0), _entry("glossary_check", 0),
    ])
    assert code == 1


def test_閘門三態_act2() -> None:
    assert ck.gate("act2", None)[0] == 3                                   # 沒帳本
    assert ck.gate("act2", [])[0] == 3                                     # 空帳本
    assert ck.gate("act2", [_entry("provenance_check", 0)])[0] == 3        # 別支的紀錄不算
    assert ck.gate("act2", [_entry("landing_check", 1)])[0] == 1
    assert ck.gate("act2", [_entry("landing_check", 2)])[0] == 1
    assert ck.gate("act2", [_entry("landing_check", 0)])[0] == 0
    # 票的字面:「有一筆 exit == 0」—— 先 1 後 0、先 0 後 1 都算過
    assert ck.gate("act2", [_entry("landing_check", 1), _entry("landing_check", 0)])[0] == 0
    assert ck.gate("act2", [_entry("landing_check", 0), _entry("landing_check", 1)])[0] == 0


def test_閘門_不適用的訊息要說出口() -> None:
    code, lines = ck.gate("act2", None)
    assert code == 3 and any("不適用" in l and "從沒被檢查過" in l for l in lines)


def test_閘門_act3_缺哪支印哪支() -> None:
    code, lines = ck.gate("act3", [_entry("spec_store", 0, "import")])
    assert code == 3
    text = "\n".join(lines)
    for name in ("provenance_check", "contract_triage", "glossary_check"):
        assert name in text
    assert "spec_store import" not in text.split("沒有這幾支的紀錄")[1].split("✅")[0]


def test_閘門_act3_分診三支只要求跑過() -> None:
    entries = [
        _entry("spec_store", 0, "import"), _entry("provenance_check", 3),
        _entry("contract_triage", 1), _entry("glossary_check", 1),
    ]
    assert ck.gate("act3", entries)[0] == 0


def test_閘門_act3_spec_store_只認import() -> None:
    entries = [
        _entry("spec_store", 0, "export"), _entry("provenance_check", 0),
        _entry("contract_triage", 0), _entry("glossary_check", 0),
    ]
    assert ck.gate("act3", entries)[0] == 3


def test_閘門_act3_一蓋過三() -> None:
    """import 沒過 **而且** 分診沒跑 → 1(有東西壞了),不是 3。同 verify_generated。"""
    code, lines = ck.gate("act3", [_entry("spec_store", 1, "import")])
    assert code == 1
    assert any("沒跑過" in l for l in lines)


def test_閘門_不認識的幕是用法錯誤() -> None:
    with pytest.raises(ck.UsageError):
        ck.gate("act9", [])


# ── 閘門:CLI ────────────────────────────────────────────────────────

def test_閘門CLI_依序取第一個有帳本的目錄(tmp_path: Path) -> None:
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    _ledger(b, _entry("landing_check", 0))
    proc = _py("--gate", "act2", str(a), str(b))
    assert proc.returncode == 0, proc.stdout
    assert str(b / ck.LEDGER_NAME) in proc.stdout


def test_閘門CLI_都沒帳本是3(tmp_path: Path) -> None:
    proc = _py("--gate", "act2", str(tmp_path))
    assert proc.returncode == 3
    assert "不適用" in proc.stdout


def test_閘門CLI_壞掉的帳本是2(tmp_path: Path) -> None:
    (tmp_path / ck.LEDGER_NAME).write_text("{not json\n", encoding="utf-8")
    assert _py("--gate", "act2", str(tmp_path)).returncode == 2


# ── runner:run_act2.sh ───────────────────────────────────────────────

def _act1(tmp_path: Path, nested: bool = False) -> tuple[Path, Path]:
    run_dir = tmp_path / "act1"
    spec = (run_dir / "interviewer" / "SPEC-draft.md") if nested else (run_dir / "SPEC-draft.md")
    spec.parent.mkdir(parents=True)
    spec.write_text("# 規格\n", encoding="utf-8")
    return run_dir, spec


def test_act2_沒帳本_拒絕3_不動工作目錄(tmp_path: Path) -> None:
    _, spec = _act1(tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    sentinel = work / "上一跑的東西.txt"
    sentinel.write_text("x")
    proc = _run("bash", ACT2, spec, work)
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert "不適用" in proc.stdout
    assert sentinel.exists()                        # 閘門在 rm -rf 之前
    assert not (work / "prompt.txt").exists()


def test_act2_有紀錄但沒過_拒絕1(tmp_path: Path) -> None:
    run_dir, spec = _act1(tmp_path)
    _ledger(run_dir, _entry("landing_check", 1))
    proc = _run("bash", ACT2, spec, tmp_path / "work")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert not (tmp_path / "work").exists()


def test_act2_帳本裡是3_一樣拒絕1(tmp_path: Path) -> None:
    run_dir, spec = _act1(tmp_path)
    _ledger(run_dir, _entry("landing_check", 3))
    assert _run("bash", ACT2, spec, tmp_path / "work").returncode == 1


def test_act2_通過_dry_run_寫run_meta(tmp_path: Path) -> None:
    run_dir, spec = _act1(tmp_path)
    _ledger(run_dir, _entry("landing_check", 0))
    work = tmp_path / "work"
    proc = _run("bash", ACT2, spec, work, env={"ACT2_DRY_RUN": "1"})
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (work / "prompt.txt").exists() and (work / "spec/SPEC.md").exists()
    meta = json.loads((work / "run-meta.json").read_text(encoding="utf-8"))
    assert meta["gate_skipped"] is False
    assert meta["gate_skip_reason"] == ""
    assert "input_blobs" in meta                    # 原本的欄位還在
    assert not (work / "result.json").exists()      # 真的沒呼叫 claude


def test_act2_規格在interviewer子目錄_帳本在上一層也找得到(tmp_path: Path) -> None:
    run_dir, spec = _act1(tmp_path, nested=True)
    _ledger(run_dir, _entry("landing_check", 0))
    proc = _run("bash", ACT2, spec, tmp_path / "work", env={"ACT2_DRY_RUN": "1"})
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_act2_skip_沒理由是2(tmp_path: Path) -> None:
    run_dir, spec = _act1(tmp_path)
    _ledger(run_dir, _entry("landing_check", 1))
    proc = _run("bash", ACT2, spec, tmp_path / "work",
                env={"ACT_GATE_SKIP": "1", "ACT2_DRY_RUN": "1"})
    assert proc.returncode == 2
    assert "理由" in proc.stderr
    assert not (tmp_path / "work").exists()


def test_act2_skip_有理由_留痕在run_meta(tmp_path: Path) -> None:
    run_dir, spec = _act1(tmp_path)
    _ledger(run_dir, _entry("landing_check", 1))
    work = tmp_path / "work"
    reason = '幕一是真人訪談,帳本沒有 "landing_check"'
    proc = _run("bash", ACT2, spec, work,
                env={"ACT_GATE_SKIP": "1", "ACT_GATE_SKIP_REASON": reason, "ACT2_DRY_RUN": "1"})
    assert proc.returncode == 0, proc.stdout + proc.stderr
    meta = json.loads((work / "run-meta.json").read_text(encoding="utf-8"))
    assert meta["gate_skipped"] is True
    assert meta["gate_skip_reason"] == reason       # 含引號也要是合法 JSON


# ── runner:run_act3.sh ───────────────────────────────────────────────

def _act2_with_db(tmp_path: Path) -> Path:
    """真的 store:凍結那份的 architecture + acceptance,兩支生成器都生得出來。"""
    run_dir = tmp_path / "act2"
    run_dir.mkdir()
    proc = _run(sys.executable, HARNESS / "spec_store.py", "import",
                REPO / "examples/shop/harness/architecture.yaml",
                REPO / "examples/shop/harness/acceptance.yaml", run_dir / "spec.db")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return run_dir


def _full_act3_ledger(run_dir: Path, import_code: int = 0) -> None:
    _ledger(run_dir, _entry("spec_store", import_code, "import"), _entry("provenance_check", 0),
            _entry("contract_triage", 1), _entry("glossary_check", 3))


def test_act3_沒帳本_拒絕3_不建輸出目錄(tmp_path: Path) -> None:
    run_dir = _act2_with_db(tmp_path)
    out = tmp_path / "out"
    proc = _run("bash", ACT3, run_dir / "spec.db", out)
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert "不適用" in proc.stdout
    assert not out.exists()


def test_act3_import沒過_拒絕1(tmp_path: Path) -> None:
    run_dir = _act2_with_db(tmp_path)
    _full_act3_ledger(run_dir, import_code=1)
    assert _run("bash", ACT3, run_dir / "spec.db", tmp_path / "out").returncode == 1


def test_act3_通過_兩支生成器都生_寫run_meta(tmp_path: Path) -> None:
    run_dir = _act2_with_db(tmp_path)
    _full_act3_ledger(run_dir)
    out = tmp_path / "out"
    proc = _run("bash", ACT3, run_dir / "spec.db", out)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (out / "ArchitectureTest.java").exists()
    assert (out / "OrderAcceptanceTest.java").exists()
    meta = json.loads((out / "run-meta.json").read_text(encoding="utf-8"))
    assert meta["gate_skipped"] is False


def test_act3_skip_留痕(tmp_path: Path) -> None:
    run_dir = _act2_with_db(tmp_path)
    out = tmp_path / "out"
    proc = _run("bash", ACT3, run_dir / "spec.db", out,
                env={"ACT_GATE_SKIP": "1", "ACT_GATE_SKIP_REASON": "測試"})
    assert proc.returncode == 0, proc.stdout + proc.stderr
    meta = json.loads((out / "run-meta.json").read_text(encoding="utf-8"))
    assert meta["gate_skipped"] is True and meta["gate_skip_reason"] == "測試"


def test_act3_生成器不適用_傳3出來(tmp_path: Path) -> None:
    """閘門過了、但 store 只有架構規則沒有情境 → gen_acceptance 3 → runner 也 3(不適用不是通過)。"""
    run_dir = tmp_path / "act2"
    run_dir.mkdir()
    proc = _run(sys.executable, HARNESS / "spec_store.py", "import",
                REPO / "examples/shop/harness/architecture.yaml", run_dir / "spec.db")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    _full_act3_ledger(run_dir)
    out = tmp_path / "out"
    proc = _run("bash", ACT3, run_dir / "spec.db", out)
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert (out / "run-meta.json").exists()         # 閘門是過了的,3 來自生成器


# ── runner:run_act4.sh ───────────────────────────────────────────────

def _skeleton(tmp_path: Path) -> tuple[Path, Path]:
    skel = tmp_path / "skeleton"
    skel.mkdir()
    (skel / "build.gradle").write_text("// 骨架\n", encoding="utf-8")
    # 票 24 合併後 dry run 也跑 order_check:三支生成測試要在基線裡,不然回 1(不是閘門的事)
    for rel in ("src/test/java/acceptance/OrderAcceptanceTest.java",
                "src/test/java/acceptance/OrderProxyAcceptanceTest.java",
                "src/test/java/architecture/ArchitectureTest.java"):
        (skel / rel).parent.mkdir(parents=True, exist_ok=True)
        (skel / rel).write_text("// 生成物(測試用假檔)\n", encoding="utf-8")
    spec = tmp_path / "SPEC.md"
    spec.write_text("# 規格\n", encoding="utf-8")
    return skel, spec


def test_act4_沒帳本_拒絕3_連dry_run都不組(tmp_path: Path) -> None:
    skel, spec = _skeleton(tmp_path)
    work = tmp_path / "work"
    proc = _run("bash", ACT4, spec, skel, work, env={"ACT4_DRY_RUN": "1"})
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert not work.exists()


def test_act4_帳本裡是3_拒絕1(tmp_path: Path) -> None:
    skel, spec = _skeleton(tmp_path)
    _ledger(skel, _entry("acceptance_gwt", 3))
    proc = _run("bash", ACT4, spec, skel, tmp_path / "work", env={"ACT4_DRY_RUN": "1"})
    assert proc.returncode == 1, proc.stdout + proc.stderr


def test_act4_通過_dry_run_寫run_meta_而骨架的帳本不帶進工作目錄(tmp_path: Path) -> None:
    skel, spec = _skeleton(tmp_path)
    _ledger(skel, _entry("acceptance_gwt", 0))
    work = tmp_path / "work"
    proc = _run("bash", ACT4, spec, skel, work, env={"ACT4_DRY_RUN": "1"})
    assert proc.returncode == 0, proc.stdout + proc.stderr
    meta = json.loads((work / "run-meta.json").read_text(encoding="utf-8"))
    assert meta["gate_skipped"] is False
    assert meta["skeleton"] == str(skel.resolve())
    assert not (work / ck.LEDGER_NAME).exists()     # 新跑新帳本
    assert (skel / ck.LEDGER_NAME).exists()         # 骨架的那份沒被動


def test_act4_skip_沒理由2_有理由留痕(tmp_path: Path) -> None:
    skel, spec = _skeleton(tmp_path)
    work = tmp_path / "work"
    proc = _run("bash", ACT4, spec, skel, work, env={"ACT4_DRY_RUN": "1", "ACT_GATE_SKIP": "1"})
    assert proc.returncode == 2 and not work.exists()
    proc = _run("bash", ACT4, spec, skel, work,
                env={"ACT4_DRY_RUN": "1", "ACT_GATE_SKIP": "1",
                     "ACT_GATE_SKIP_REASON": "acceptance_gwt 在本 repo 跑不動(4567d31 不在)"})
    assert proc.returncode == 0, proc.stdout + proc.stderr
    meta = json.loads((work / "run-meta.json").read_text(encoding="utf-8"))
    assert meta["gate_skipped"] is True and "4567d31" in meta["gate_skip_reason"]
