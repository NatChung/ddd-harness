#!/usr/bin/env python3
"""`run_act3.sh` 閘門 + 生成的測試 —— 對 **shop 凍結那份 spec** 跑真的 store(票 21)。

從 `harness/test_check_ledger.py` 搬來(票 32):這幾支要 `examples/shop/harness/` 的
architecture.yaml / acceptance.yaml 才生得出兩支生成器的輸出,hub 沒有那份語料。
`_run` / `_ledger` / `_entry` 與 `ACT3` 仍是 harness 那份測試檔的,這裡只 import。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from test_check_ledger import ACT3, HARNESS, _entry, _ledger, _run  # harness/ 由 conftest 放進 sys.path

REPO = Path(__file__).resolve().parents[3]


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
