"""詞彙表進 store + 對譯檢查(票 08-A / ADR 0005 §1、§4、§5)。

測試名字照這條線的慣例寫成「寫不進去」而不是「驗證失敗」——
那是第 1 階(schema 的 CHECK / FK / UNIQUE / TRIGGER)跟第 2 階(spec_store 的跨列
檢查)的差別,**而這張票有一條規則刻意住第 2 階**:對譯檢查是**報告**不是 FK,
因為硬擋只拿得到「匯入失敗」,拿不到「差幾個」——而這張票的價值就在那個數字。

預測寫在 `.scratch/ddd-harness/08-PREDICTION.md`,commit 在寫程式之前。
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from spec_store import SpecError, build_store, load_spec, load_specs

REPO = Path(__file__).resolve().parents[2]
FROZEN_GLOSSARY = REPO / "examples/shop/harness/glossary.yaml"
FROZEN_ACCEPTANCE = REPO / "examples/shop/harness/acceptance.yaml"
ACT2_GLOSSARY = (REPO / "examples/shop/harness/runs/2026-08-18-act2-from-interview"
                 / "glossary.yaml")
ACT2_ACCEPTANCE = (REPO / "examples/shop/harness/runs/2026-08-18-act2-rerun"
                   / "agent-acceptance.yaml")
ACT1_GLOSSARY = (REPO / "examples/shop/harness/runs/2026-08-18-act1-opus-rerun"
                 / "glossary.yaml")

TERM = {
    "term": "某某編號 SomeId",
    "definition": "認出是哪一個的那組編號",
    "ddd_type": "識別碼",
    "provenance": "Qn",
    "provenance_ref": "[Q1]",
}


def glossary(terms=None, banned=None):
    spec: dict = {"glossary_terms": terms if terms is not None else [dict(TERM)]}
    if banned is not None:
        spec["banned_synonyms"] = banned
    return spec


def term(**changes):
    t = dict(TERM)
    t.update(changes)
    return t


def problems_of(tmp_path, spec) -> list[str]:
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", spec)
    return exc.value.problems


def run_check(db: Path):
    return subprocess.run(
        [sys.executable, str(Path(__file__).with_name("glossary_check.py")), str(db)],
        capture_output=True, text=True, check=False)


# ── 第 1 階:填不了就寫不進去 ──────────────────────────────────────────────

def test_自創第六格來源寫不進去(tmp_path):
    problems = problems_of(tmp_path, glossary([term(provenance="訪談推測")]))
    assert any("schema 擋下來了" in p for p in problems), problems


def test_五格來源與架構規則逐字相同(tmp_path):
    for provenance in ("Qn", "暫定", "推導自", "本案自決"):
        build_store(tmp_path / "spec.db", glossary([term(provenance=provenance)]))


def test_模板既定_在白名單為空時寫不進去(tmp_path):
    """trigger 另取名字,但擋的東西與另外三張表逐字相同。"""
    problems = problems_of(tmp_path, glossary([term(provenance="模板既定")]))
    assert any("模板既定" in p for p in problems), problems


def test_定義與DDD型態不得留空(tmp_path):
    for missing in ("definition", "ddd_type"):
        problems = problems_of(tmp_path, glossary([term(**{missing: "   "})]))
        assert any(f"缺 {missing}" in p for p in problems), problems


def test_DDD型態是自由文字不是固定清單(tmp_path):
    """鎖清單會逼下一份詞彙表把自己的詞硬塞進別人的格子 —— 那是製造假資料。"""
    for ddd_type in ("Aggregate Root", "動詞", "狀態的顯示文字", "外部規則集", "角色"):
        build_store(tmp_path / "spec.db", glossary([term(ddd_type=ddd_type)]))


def test_兩個詞宣稱同一個對外欄位名寫不進去(tmp_path):
    """UNIQUE:對譯有歧義的話,「對得到一個詞」這句話就沒有意義了。"""
    ok = glossary([term(term="甲", wire_field="someField"),
                   term(term="乙", wire_field="otherField")])
    build_store(tmp_path / "spec.db", ok)
    print("mutated ok:兩個詞各自有欄位名時匯得進去,所以下面擋的是撞名不是別的")

    problems = problems_of(tmp_path, glossary(
        [term(term="甲", wire_field="someField"),
         term(term="乙", wire_field="someField")]))
    assert any("schema 擋下來了" in p for p in problems), problems


def test_對外欄位名可以多個都是空的(tmp_path):
    """空白 = 這個詞不上線,**不是漏填** —— 而不上線的詞可以有很多個。"""
    build_store(tmp_path / "spec.db", glossary(
        [term(term="甲"), term(term="乙"), term(term="丙")]))


def test_一律改用指向不存在的詞寫不進去(tmp_path):
    """FK。叫人改用一個詞彙表裡沒定義的詞 —— 那是真的會發生的,而散文自己看不出來。"""
    ok = glossary(banned=[{"banned": "某某", "use_instead": TERM["term"],
                           "note": "逐字稿混用"}])
    build_store(tmp_path / "spec.db", ok)
    print("mutated ok:指得到的時候匯得進去,所以下面擋的是 FK 不是別的")

    problems = problems_of(tmp_path, glossary(
        banned=[{"banned": "某某", "use_instead": "詞彙表裡沒有這個詞",
                 "note": "逐字稿混用"}]))
    assert any("schema 擋下來了" in p for p in problems), problems


def test_沒有替代詞而不說理由寫不進去(tmp_path):
    """「真的沒有替代詞」與「還沒填」長得一模一樣,所以要逼出理由(同列 CHECK,第 1 階)。"""
    problems = problems_of(tmp_path, glossary(
        banned=[{"banned": "某某", "note": "這個東西在本案不存在"}]))
    assert any("schema 擋下來了" in p for p in problems), problems


def test_沒有替代詞但說了理由寫得進去(tmp_path):
    build_store(tmp_path / "spec.db", glossary(
        banned=[{"banned": "某某",
                 "no_replacement_note": "它指的東西在本案根本不存在",
                 "note": "這個東西在本案不存在"}]))


# ── 第 2 階:擋得住,但擋的是 script ────────────────────────────────────────

def test_對外欄位名填成散文註記會被擋(tmp_path):
    """散文那一格裝得下註記,而註記拿去比對**永遠不會中,而且是靜靜地不中**。"""
    for junk in ("(整個物件)", "someField[]", "見下三列", "some field"):
        problems = problems_of(tmp_path, glossary([term(wire_field=junk)]))
        assert any("不是一個欄位名" in p for p in problems), (junk, problems)


def test_同一個詞出現兩次會被擋(tmp_path):
    problems = problems_of(tmp_path, glossary([term(), term()]))
    assert any("出現兩次" in p for p in problems), problems


def test_既指了替代詞又寫了沒有替代詞的理由會被擋(tmp_path):
    problems = problems_of(tmp_path, glossary(
        banned=[{"banned": "某某", "use_instead": TERM["term"],
                 "no_replacement_note": "沒有替代詞", "note": "逐字稿混用"}]))
    assert any("只能有一個" in p for p in problems), problems


def test_有禁用同義詞卻沒有詞彙表會被擋(tmp_path):
    problems = problems_of(tmp_path, {
        "banned_synonyms": [{"banned": "某某", "no_replacement_note": "無",
                             "note": "逐字稿混用"}]})
    assert any("沒有 glossary_terms" in p for p in problems), problems


def test_未知欄位當場掛(tmp_path):
    problems = problems_of(tmp_path, glossary([term(**{"對外欄位名": "someField"})]))
    assert any("未知的 key" in p for p in problems), problems


def test_詞彙表區塊是選填的(tmp_path):
    """必填會打到 fixtures/negative-scenarios.yaml —— 那是測試在用的(ADR 0005 §6)。"""
    spec = load_spec(Path(__file__).with_name("fixtures") / "negative-scenarios.yaml")
    assert "glossary_terms" not in spec
    build_store(tmp_path / "spec.db", spec)


def test_只有詞彙表的一份檔不算空的_spec(tmp_path):
    """P3 的前提:量不到差額的那一份,連匯入都要進得去才走得到「不適用」。"""
    build_store(tmp_path / "spec.db", glossary())


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
