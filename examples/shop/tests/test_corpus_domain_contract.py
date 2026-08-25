"""領域契約:真實轉寫匯得進去、分診數字釘住(票 06-A / ADR 0005)。

從 `harness/test_domain_contract.py` 搬來(票 32):這兩支讀的是
`examples/shop/harness/runs/2026-08-18-act1-opus-rerun/contracts.yaml` 那份真實轉寫,
hub 沒有那份語料。`_triage` 仍是 harness 那份測試檔的,這裡只 import。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from spec_store import build_store, load_spec
from test_domain_contract import _triage  # harness/ 由 conftest 放進 sys.path

REPO = Path(__file__).resolve().parents[3]
TRANSCRIPT = (REPO / "examples/shop/harness/runs/2026-08-18-act1-opus-rerun"
              / "contracts.yaml")


# ── 真實轉寫:數字釘住,分診跑得出來 ──────────────────────────────────────

def test_真實轉寫匯得進去而且分診數字釘住(tmp_path):
    db = tmp_path / "contracts.db"
    build_store(db, load_spec(TRANSCRIPT))
    conn = sqlite3.connect(db)
    try:
        total, = conn.execute("SELECT count(*) FROM domain_contract").fetchone()
        crossing = [r[0] for r in conn.execute(
            "SELECT id FROM domain_contract WHERE crosses_aggregate = 1 ORDER BY id")]
        with_test, = conn.execute(
            "SELECT count(DISTINCT contract_id) FROM contract_named_test").fetchone()
        enforced, = conn.execute(
            "SELECT count(*) FROM domain_contract WHERE enforcement <> 'none'").fetchone()
    finally:
        conn.close()

    assert total == 20                       # C1–C19 加上 C3b
    assert crossing == ["C12", "C13", "C14"]  # 忠實照散文的 ⚠️,不重判
    # ⚠️ 這個 0 是**語料逼出來的**:這場訪談的情境本輪一份都沒落檔。
    #    不是「契約沒指名」——散文 20 條裡有 19 條指名了。
    assert with_test == 0
    # ⚠️ 這個 0 是 **CHECK 逼出來的**(值域只有 none),不是量出來的發現。
    assert enforced == 0


# ── 報表的閘門:exit 1 那條路(2026-08-18 稽核 §二.B)────────────────────

def test_有分診項目時離開碼是1而且逐條印得出來(tmp_path):
    """exit 1 那條路(20 條契約、3 條守不住、20 條指不出測試)以前沒被斷言過。

    **一個只會回 0 的閘門跟沒有閘門一樣** —— 這支釘住它真的會回 1,
    而且佇列的內容真的印得出來(不是只回一個數字)。
    """
    db = tmp_path / "contracts.db"
    build_store(db, load_spec(TRANSCRIPT))
    out = _triage(db)

    assert out.returncode == 1, (out.returncode, out.stdout)
    assert "契約:20 條" in out.stdout
    assert "有指名測試的:0 條;指不出任何測試的:20 條" in out.stdout
    assert "在自己那個物件內守不住的(跨聚合根):3 條" in out.stdout
    # 佇列一逐條印,不是只印數量 —— 分診要能直接拿去看。
    for cid in ("C12", "C13", "C14"):
        assert f"⚠️ {cid}(precondition)守在:" in out.stdout, cid
    # 上限也要印在報表裡(讀報表的人拿不到票)。
    assert "「有指名測試」不等於「有機械檢查」" in out.stdout
