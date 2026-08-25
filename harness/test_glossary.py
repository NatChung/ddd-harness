"""詞彙表進 store + 對譯檢查(票 08-A / ADR 0005 §1、§4、§5)。

測試名字照這條線的慣例寫成「寫不進去」而不是「驗證失敗」——
那是第 1 階(schema 的 CHECK / FK / UNIQUE / TRIGGER)跟第 2 階(spec_store 的跨列
檢查)的差別,**而這張票有一條規則刻意住第 2 階**:對譯檢查是**報告**不是 FK,
因為硬擋只拿得到「匯入失敗」,拿不到「差幾個」——而這張票的價值就在那個數字。

預測寫在 `.scratch/ddd-harness/08-PREDICTION.md`,commit 在寫程式之前。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from spec_store import SpecError, build_store, load_spec

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
