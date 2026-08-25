"""第 0 階佔位符守衛的測試(票 23)—— 離線,只碰 spec_store。

驗的是三件事,缺一件這一階就不算接上:
  * 整格是佔位符 → 被拒,而且是**第 0 階**的訊息、列得出那一格的路徑;
  * 「含有」不等於「整格」 —— 引用式的方括號、句中的 TODO 要放行;
  * 第 0 階跟第 1 / 2 階的訊息**不折成一種**(票 14 缺陷一)。

不 import test_harness 的 fixture:那個檔本票不准動,耦合上去等於把它的形狀凍住。
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from spec_store import (
    EMPTY_ALLOWED_AT,
    PLACEHOLDER_PATTERNS,
    SpecError,
    build_store,
    check_placeholders,
    load_spec,
)
from spec_store import main as store_main

FIXTURES = Path(__file__).with_name("fixtures")

# 最小可匯入的 spec:一條架構規則,沒有情境(所以不需要 wire_contract)。
MINIMAL = {
    "authorized_templates": [],
    "architecture_rules": [
        {
            "id": "A1",
            "rule": "domain/ 不得 import 任何框架",
            "provenance": "本案自決",
            "provenance_ref": "簡潔架構相依性原則",
            "enforcement": "archunit_forbidden_dependency",
            "forbidden_dependencies": {
                "from": "com.shop.domain..",
                "to": ["org.springframework.."],
            },
        },
    ],
}


def minimal(**changes):
    s = copy.deepcopy(MINIMAL)
    s["architecture_rules"][0].update(changes)
    return s


def negative_fixture():
    """fixtures/negative-scenarios.yaml —— 真實形狀,S7 的 customer_id 就是空字串。"""
    return load_spec(FIXTURES / "negative-scenarios.yaml")


def scenario_index(spec, sid):
    return next(i for i, sc in enumerate(spec["acceptance_scenarios"]) if sc["id"] == sid)


# ── 每種佔位符各一例被拒 ──────────────────────────────────────────────

@pytest.mark.parametrize("value", [
    "",
    "TODO", "TODO: 明天補", "todo",
    "FIXME", "FIXME later",
    "???", "?",
    "[待補]", "[role]", "[]",
    "<customer id>", "<>",
])
def test_整格是佔位符_被第0階擋下_並列出那一格的路徑(tmp_path, value):
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", minimal(provenance_ref=value))
    text = str(exc.value)
    assert "第 0 階" in text
    assert "architecture_rules[0].provenance_ref" in text
    # 拒絕訊息要印清單:agent 得知道自己被什麼擋
    for label, _ in PLACEHOLDER_PATTERNS:
        assert label in text


def test_拒絕訊息不含第1階或第2階的字樣_兩種沒東西不折成一種(tmp_path):
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", minimal(rule="TODO"))
    text = str(exc.value)
    assert "第 0 階" in text
    assert "schema 擋下來了" not in text
    # 第 2 階的形狀錯誤也不該混進來:第 0 階先 raise,後面兩階根本沒跑
    assert "未知的 key" not in text


def test_第2階的拒絕訊息不含第0階字樣(tmp_path):
    """反向:一份沒有佔位符、但來源標記不合法的 spec,只有第 2 階的訊息。"""
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", minimal(provenance="未定案"))
    assert "第 0 階" not in str(exc.value)
    assert not (tmp_path / "spec.db").exists()


def test_第0階先於第2階_同一份兩種病只印第0階(tmp_path):
    s = minimal(provenance="未定案", provenance_ref="[待補]")
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", s)
    text = str(exc.value)
    assert "第 0 階" in text
    assert "未定案" not in text


def test_只有空白的格_是第1階的事_不是第0階(tmp_path):
    """階界本身寫成測試:`"   "` 由 schema 的 length(trim) > 0 擋,第 0 階只收恰好 ""。

    這條邊界不是本票發明的 —— test_harness.py::test_來源為空寫不進去 釘死了
    「空白格 = schema 擋下來了」;第 0 階再收一次就是同一條規則兩份載體。
    """
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", minimal(provenance_ref="   "))
    text = str(exc.value)
    assert "schema 擋下來了" in text
    assert "第 0 階" not in text


def test_逐格全列_不_fail_fast(tmp_path):
    s = minimal(rule="TODO", provenance_ref="[待補]")
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", s)
    text = str(exc.value)
    assert "architecture_rules[0].rule" in text
    assert "architecture_rules[0].provenance_ref" in text


def test_第0階拒絕時_db_不會留下來(tmp_path):
    db = tmp_path / "spec.db"
    with pytest.raises(SpecError):
        build_store(db, minimal(rule=""))
    assert not db.exists()


# ── 「含有」不等於「整格」 ───────────────────────────────────────────────

def test_引用式方括號_後面有本文_放行(tmp_path):
    s = minimal(provenance="推導自", provenance_ref="[Q7] 介面宣告在內層")
    assert check_placeholders(s) == []
    build_store(tmp_path / "spec.db", s)  # 不該丟


def test_整格只有_Qn_引用_放行_那是來源標記不是便條(tmp_path):
    """`[Q7]` 是這個 repo 的來源標記寫法;test_glossary / test_domain_contract 有 40 格
    拿它當合法值。`[待補]` / `[role]` 照擋(見上面的 parametrize)。"""
    s = minimal(provenance="推導自", provenance_ref="[Q7]")
    assert check_placeholders(s) == []
    build_store(tmp_path / "spec.db", s)  # 不該丟


def test_多段引用_整格不只一個方括號_放行():
    s = minimal(provenance="推導自",
                provenance_ref="[Q12] — SPEC.md L83-L88(情境 S7);C8 L185(見 L190)")
    assert check_placeholders(s) == []


def test_句中含_TODO_放行():
    s = minimal(rule="domain/ 不得 import 框架;例外要先列進 TODO 清單再談")
    assert check_placeholders(s) == []


def test_句中含尖括號_放行():
    s = minimal(rule="回應的 <orderId> 欄位不得為空")
    assert check_placeholders(s) == []


def test_只看字串值_None_數字_bool_list_都不是格():
    assert check_placeholders({"a": None, "b": 0, "c": False, "d": [], "e": {}}) == []


def test_key_不看_打錯的_key_歸_check_shape():
    assert check_placeholders({"[role]": "填了值"}) == []


# ── S7 的空 customer_id:唯一的豁免,而且只豁免空字串 ────────────────────

def test_真實_fixture_零命中_S7_空_customer_id_放行(tmp_path):
    s = negative_fixture()
    i = scenario_index(s, "S7")
    assert s["acceptance_scenarios"][i]["rejected_requests"][0]["customer_id"] == ""
    assert check_placeholders(s) == []
    build_store(tmp_path / "spec.db", s)  # 整份仍匯得進去


def test_豁免路徑常數_對得上_S7_那格的真實路徑():
    s = negative_fixture()
    path = f"acceptance_scenarios[{scenario_index(s, 'S7')}].rejected_requests[0].customer_id"
    assert any(p.match(path) for p in EMPTY_ALLOWED_AT)


def test_S7_那格寫_TODO_一樣被擋(tmp_path):
    s = negative_fixture()
    i = scenario_index(s, "S7")
    s["acceptance_scenarios"][i]["rejected_requests"][0]["customer_id"] = "TODO"
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", s)
    assert f"acceptance_scenarios[{i}].rejected_requests[0].customer_id" in str(exc.value)


def test_成功情境的空_customer_id_不在豁免內(tmp_path):
    s = negative_fixture()
    i = scenario_index(s, "S1")
    s["acceptance_scenarios"][i]["steps"][0]["customer_id"] = ""
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", s)
    text = str(exc.value)
    assert "第 0 階" in text
    assert f"acceptance_scenarios[{i}].steps[0].customer_id" in text


def test_巢在深處的格也走得到(tmp_path):
    s = negative_fixture()
    i = scenario_index(s, "S1")
    s["acceptance_scenarios"][i]["steps"][0]["items"][0]["product_id"] = "<sku>"
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", s)
    assert f"acceptance_scenarios[{i}].steps[0].items[0].product_id" in str(exc.value)


# ── CLI:JSON 路徑不需要 PyYAML,離開碼維持 1 ───────────────────────────

def test_cli_第0階_exit_1_stderr_有第0階字樣(tmp_path, capsys):
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(minimal(rule="FIXME")), encoding="utf-8")
    db = tmp_path / "spec.db"
    assert store_main(["spec_store.py", "import", str(spec_path), str(db)]) == 1
    err = capsys.readouterr().err
    assert "第 0 階" in err
    assert "architecture_rules[0].rule" in err
    assert not db.exists()
