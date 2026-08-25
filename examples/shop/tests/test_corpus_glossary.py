"""詞彙表對譯檢查 —— 對 **shop 凍結語料**(三份,三個答案,數字釘住)驗(票 08-A / ADR 0005)。

從 `harness/test_glossary.py` 搬來(票 32):這幾支讀的是 `examples/shop/harness/` 的
glossary.yaml / acceptance.yaml 與 `runs/**` 底下落檔的詞彙表和合約,hub 沒有那份語料。
`glossary` / `term` / `run_check` 仍是 harness 那份測試檔的,這裡只 import。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from spec_store import build_store, load_spec, load_specs
from test_glossary import glossary, run_check, term  # harness/ 由 conftest 放進 sys.path

REPO = Path(__file__).resolve().parents[3]
FROZEN_GLOSSARY = REPO / "examples/shop/harness/glossary.yaml"
FROZEN_ACCEPTANCE = REPO / "examples/shop/harness/acceptance.yaml"
ACT2_GLOSSARY = (REPO / "examples/shop/harness/runs/2026-08-18-act2-from-interview"
                 / "glossary.yaml")
ACT2_ACCEPTANCE = (REPO / "examples/shop/harness/runs/2026-08-18-act2-rerun"
                   / "agent-acceptance.yaml")
ACT1_GLOSSARY = (REPO / "examples/shop/harness/runs/2026-08-18-act1-opus-rerun"
                 / "glossary.yaml")


# ── 對譯檢查:不適用不算通過,而不適用有兩種 ──────────────────────────────

def test_沒有詞彙表時不適用而不是通過(tmp_path):
    db = tmp_path / "spec.db"
    build_store(db, load_spec(FROZEN_ACCEPTANCE))
    done = run_check(db)
    assert done.returncode == 3, done.stdout
    assert "不適用(不是通過)" in done.stdout


def test_有詞彙表而沒有合約時也是不適用(tmp_path):
    """ADR §6 只寫了第一種。**這一種更難看見**:詞彙表有東西,計數上什麼都不缺。"""
    db = tmp_path / "spec.db"
    build_store(db, load_spec(ACT1_GLOSSARY))
    done = run_check(db)
    assert done.returncode == 3, done.stdout
    assert "對外合約 0 份" in done.stdout


def test_三條已知上限印在報表裡(tmp_path):
    db = tmp_path / "spec.db"
    build_store(db, load_specs([FROZEN_GLOSSARY, FROZEN_ACCEPTANCE]))
    out = run_check(db).stdout
    assert "沒有唯一解" in out            # 上限三:對譯沒有唯一解
    assert "懲罰寫得好的那一方" in out    # 上限二:禁用同義詞的假陽性
    assert "一個詞可以有多個類別" in out  # 上限一:白名單比對對不上衍生名


def test_撞名要完整相等不得子字串(tmp_path):
    """子字串比對就是票 03 那種病:**懲罰寫得好的那一方**。"""
    db = tmp_path / "spec.db"
    build_store(db, dict(
        load_spec(FROZEN_ACCEPTANCE),
        **glossary([term(term="Order", definition="前綴撞得到就完了", ddd_type="測試用")])))
    out = run_check(db).stdout
    # 合約有一個欄位以這個詞為前綴。子字串比對會判它「對得到」,而那是假陽性:
    # 詞是那個東西本身,欄位是它的識別碼 —— 兩個不同的東西。
    assert "對得到 0 個" in out, out


def test_全部對得到才是離開碼零(tmp_path):
    """離開碼的第四象限:不是 3(不適用)、不是 1(有差額),而是真的過了。"""
    contract = load_spec(FROZEN_ACCEPTANCE)
    fields = contract["wire_contract"]["list_fields"]
    req = [contract["wire_contract"][k] for k in contract["wire_contract"]
           if k.startswith("req_") and contract["wire_contract"][k]]
    terms = [term(term=f"某詞{i}", wire_field=f, provenance_ref=f"[Q{i}]")
             for i, f in enumerate(dict.fromkeys(fields + req))]
    db = tmp_path / "spec.db"
    build_store(db, dict(contract, **glossary(terms)))
    done = run_check(db)
    assert done.returncode == 0, done.stdout
    assert "對不到 0 個" in done.stdout, done.stdout


def test_詞宣稱一個合約沒有的欄位也算進離開碼(tmp_path):
    """只印不算的警告 = 一個永遠 gate 不住任何東西的警告。

    **寫在該寫的地方 ≠ 接上了** —— 這條病本線量過很多次,不要在自己的報表裡再犯一次。
    """
    contract = load_spec(FROZEN_ACCEPTANCE)
    fields = contract["wire_contract"]["list_fields"]
    req = [contract["wire_contract"][k] for k in contract["wire_contract"]
           if k.startswith("req_") and contract["wire_contract"][k]]
    terms = [term(term=f"某詞{i}", wire_field=f, provenance_ref=f"[Q{i}]")
             for i, f in enumerate(dict.fromkeys(fields + req))]
    # 只加這一條:每個欄位仍然對得到,唯一的問題是這個詞宣稱了一個不存在的欄位。
    terms.append(term(term="孤兒詞", wire_field="fieldThatNoContractHas",
                      provenance_ref="[Q99]"))
    db = tmp_path / "spec.db"
    build_store(db, dict(contract, **glossary(terms)))
    done = run_check(db)
    assert "對不到 0 個" in done.stdout, done.stdout   # 破壞本身生效了:差額仍是 0
    print("mutated ok:唯一的問題是孤兒詞,對譯那一側一個都沒少")
    assert done.returncode == 1, done.stdout


# ── 真實語料:三份,三個答案,數字釘住 ────────────────────────────────────

def test_凍結那組_五個列表欄位對不到四個(tmp_path):
    """⚠️ 唯一對得到的那一個是**撞名**(詞彙表本身用英文識別字寫),不是對譯。

    這一組的意思比數字大:那份詞彙表開頭寫著「實作中的類別、方法、**欄位**命名必須
    使用這裡的詞」,而它自己那份合約的列表欄位 4/5 不在表裡 ——
    因為那份詞彙表管的是**類名**,wire 欄位是另一組詞。散文那句話把兩組講成同一組。
    """
    db = tmp_path / "spec.db"
    build_store(db, load_specs([FROZEN_GLOSSARY, FROZEN_ACCEPTANCE]))
    conn = sqlite3.connect(db)
    try:
        terms, = conn.execute("SELECT count(*) FROM glossary_term").fetchone()
        declared, = conn.execute(
            "SELECT count(*) FROM glossary_term WHERE wire_field IS NOT NULL").fetchone()
    finally:
        conn.close()
    assert (terms, declared) == (15, 0)   # 這份詞彙表沒有「對外欄位名」那一欄

    done = run_check(db)
    assert done.returncode == 1
    assert "5 個欄位:對得到 1 個、**對不到 4 個**" in done.stdout, done.stdout
    assert "6 個欄位:對得到 2 個、**對不到 4 個**" in done.stdout, done.stdout


def test_第二幕那組_七個列表欄位一個都對不到(tmp_path):
    """⚠️ **配得上的兩份**:act2-rerun 的輸入就是 act2-from-interview 的 input-SPEC.md
    (該跑的 RESULT.md 自己寫著,含 md5)。同一份規格的散文詞彙表 vs 它的落檔合約。

    ⚠️ 這個 7 **跟手算的答案不一樣**(手算說 4 個對得到)。差在哪:那 4 個是人在腦裡
    做的翻譯,規格裡沒有任何一格記著。落檔 agent 把完整的對譯寫在 yaml 的**註解**裡
    —— **做對了,而且沒有留下任何機器看得見的痕跡。** 那正是這張票要抓的東西。
    """
    db = tmp_path / "spec.db"
    build_store(db, load_specs([ACT2_GLOSSARY, ACT2_ACCEPTANCE]))
    conn = sqlite3.connect(db)
    try:
        terms, = conn.execute("SELECT count(*) FROM glossary_term").fetchone()
        declared, = conn.execute(
            "SELECT count(*) FROM glossary_term WHERE wire_field IS NOT NULL").fetchone()
        banned, = conn.execute(
            "SELECT count(*) FROM glossary_banned_synonym").fetchone()
        orphan, = conn.execute(
            "SELECT count(*) FROM glossary_banned_synonym "
            "WHERE use_instead IS NULL").fetchone()
    finally:
        conn.close()
    assert (terms, declared) == (11, 0)
    # 散文 4 列 → 子表 10 列(一列禁好幾種講法,那正是一對多)。
    # 其中 2 列指不到替代詞:散文叫人改用一個動作詞,而詞彙表只定義了狀態那個詞。
    assert (banned, orphan) == (10, 2)

    done = run_check(db)
    assert done.returncode == 1
    assert "7 個欄位:對得到 0 個、**對不到 7 個**" in done.stdout, done.stdout


def test_本輪訪談那組_唯一填了對外欄位名卻唯一量不到(tmp_path):
    """⚠️ **不跨 run 硬配對。** 這場訪談的情境本輪一份都沒落檔,runs/ 底下的 act2 產出
    是別份規格的 —— 拿它們來配就是造假,所以這一份誠實走「不適用」。
    """
    db = tmp_path / "spec.db"
    build_store(db, load_spec(ACT1_GLOSSARY))
    conn = sqlite3.connect(db)
    try:
        terms, = conn.execute("SELECT count(*) FROM glossary_term").fetchone()
        declared, = conn.execute(
            "SELECT count(*) FROM glossary_term WHERE wire_field IS NOT NULL").fetchone()
        banned, = conn.execute(
            "SELECT count(*) FROM glossary_banned_synonym").fetchone()
        orphan, = conn.execute(
            "SELECT count(*) FROM glossary_banned_synonym "
            "WHERE use_instead IS NULL").fetchone()
    finally:
        conn.close()
    # 17 個詞裡 12 格填得出欄位名、5 格空白 —— 而 5 格裡只有 3 格真的是「不上線」,
    # 另 2 格散文寫的是註記(不是欄位名)。**計數分不開這兩種。**
    assert (terms, declared) == (17, 12)
    # 散文 6 列 → 子表 15 列;其中 6 列沒有替代詞(散文寫「不得使用」)。
    assert (banned, orphan) == (15, 6)

    assert run_check(db).returncode == 3
