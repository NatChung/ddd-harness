#!/usr/bin/env python3
"""負面情境(ADR 0003)的測試 —— 離線,對 `fixtures/negative-scenarios.yaml` 跑。

那份 fixture 就是第五幕的驗收套件:2026-08-18 量到的「12 條進去、4 條出來」裡,
落不了檔的 5 條(S3–S7)。**它們 import 得進去,才算這一輪做完。**

`test_五條全部落得了檔` 是綠燈那半;底下每一條 `test_..._要紅` 是「逐條可紅」那半。
只有綠的話,把 `_check_shape` 改成 `return []` 也會全過 —— 那正是這個 repo
反覆踩到的假驗收。
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent))
import spec_store  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "negative-scenarios.yaml"


@pytest.fixture
def spec() -> dict:
    return yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))


def scenario(spec: dict, sid: str) -> dict:
    return next(s for s in spec["acceptance_scenarios"] if s["id"] == sid)


# ── 綠燈那半 ──────────────────────────────────────────────────────────────

def test_五條全部落得了檔(spec: dict) -> None:
    """S3–S7 是 2026-08-18 落不了檔的那五條。這條測試就是那一輪的驗收。"""
    assert spec_store._check_shape(spec) == []
    assert {s["id"] for s in spec["acceptance_scenarios"]} >= {"S3", "S4", "S5", "S6", "S7"}


def test_違法的值真的寫得進資料庫(spec: dict, tmp_path: Path) -> None:
    """光是形狀檢查過不算 —— schema 的 CHECK 才是最後一關。
    數量 0、數量 -1、空明細、空的下單者,四種都要真的落進 SQLite。"""
    import sqlite3
    db = tmp_path / "neg.db"
    spec_store.build_store(db, spec)
    conn = sqlite3.connect(db)
    quantities = {r[0] for r in conn.execute("SELECT quantity FROM rejected_request_item")}
    assert {0, -1} <= quantities, "數量 0 / -1 應該寫得進負面請求的明細"
    # S4 空單:有請求、但一筆明細都沒有
    empty = conn.execute(
        "SELECT COUNT(*) FROM rejected_request_item WHERE scenario_id = 'S4'").fetchone()[0]
    assert empty == 0
    assert conn.execute(
        "SELECT COUNT(*) FROM rejected_request WHERE scenario_id = 'S4'").fetchone()[0] == 1
    # S7 未登入:空的 customer_id
    assert conn.execute(
        "SELECT customer_id FROM rejected_request WHERE scenario_id = 'S7'").fetchone()[0] == ""


def test_正面情境的表照舊擋得住違法值(spec: dict, tmp_path: Path) -> None:
    """**放寬只發生在負面那組表。** 這條盯著沒有走火 ——
    `step_item` 的 CHECK 還在,不然這輪就是把守衛拆了而不是搬了。"""
    import sqlite3
    bad = copy.deepcopy(spec)
    scenario(bad, "S1")["steps"][0]["items"][0]["quantity"] = 0
    with pytest.raises((spec_store.SpecError, sqlite3.IntegrityError)):
        spec_store.build_store(tmp_path / "x.db", bad)


# ── 逐條可紅那半 ──────────────────────────────────────────────────────────

def test_只斷言狀態碼要紅(spec: dict) -> None:
    """「回了 400 但還是寫了一筆」是這條規則存在要擋的失效。
    少了 list_no_row_for_customer,這條驗收就只測了 HTTP 狀態碼。"""
    scenario(spec, "S5")["rejected_assertions"] = [
        {"kind": "status_is", "target": "zeroQty", "expected_number": 400}
    ]
    assert any("list_no_row_for_customer" in p for p in spec_store._check_shape(spec))


def test_拒絕情境借用成功情境的客人要紅(spec: dict) -> None:
    """驗收共用一個資料庫、不重置。客人編號撞了,
    `list_no_row_for_customer` 會被別的情境建的列弄成假紅,而且**順序一換就時紅時綠**。"""
    scenario(spec, "S4")["rejected_requests"][0]["customer_id"] = "C-001"  # S1 用的
    assert any("也出現在預期成功的情境" in p for p in spec_store._check_shape(spec))


def test_違法_fixture_沒標_expects_rejection_要紅(spec: dict) -> None:
    scenario(spec, "S5")["expects_rejection"] = False
    assert any("expects_rejection" in p for p in spec_store._check_shape(spec))


def test_夾帶值等於算出來的要紅(spec: dict) -> None:
    """S3 要證明「指定值被忽略」。夾帶值若等於算出來的,
    「被忽略」與「被採用」的結果一模一樣 —— 這條情境證明不了任何事。"""
    step = scenario(spec, "S3")["steps"][0]
    step["claimed_total_cents"] = 8950  # = 1 × 8950
    assert any("斷言不了" in p for p in spec_store._check_shape(spec))


def test_斷言指向不存在的_alias_要紅(spec: dict) -> None:
    """負面斷言另開一張表就是為了保住這個守衛 —— 打字錯會被擋下。"""
    scenario(spec, "S6")["rejected_assertions"][0]["target"] = "typo"
    assert any("不是這個情境的 alias" in p for p in spec_store._check_shape(spec))


def test_拒絕情境混用_steps_要紅(spec: dict) -> None:
    """混用表示作者沒想清楚這個情境預期成功還是預期被拒。"""
    scenario(spec, "S7")["steps"] = [{
        "alias": "x", "customer_id": "C-9",
        "items": [{"product_id": "p", "quantity": 1,
                   "unit_price_cents": 1, "currency": "TWD"}],
    }]
    assert any("不得有 steps" in p for p in spec_store._check_shape(spec))


def test_schema_擋得住掛錯情境的違法請求(tmp_path: Path) -> None:
    """ADR 0003 的核心那條 FK,直接對 SQLite 驗 —— 不透過 importer。

    importer 的檢查是**第二道**;第一道是「預期成功的情境物理上掛不上違法請求」。
    這條若鬆了,ADR 0003 選 D 而不選 A 的理由就沒了。
    """
    import sqlite3
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript((Path(__file__).parent / "schema.sql").read_text(encoding="utf-8"))
    conn.execute(
        "INSERT INTO acceptance_scenario (id, given_when, then_expect, provenance, "
        "provenance_ref, expects_rejection) VALUES ('S1','g','t','Qn','ref',0)")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO rejected_request (scenario_id, expects_rejection, alias, seq, "
            "customer_id) VALUES ('S1', 1, 'x', 0, 'C-1')")


def test_換個欄位名總額不變式仍然會檢查(spec: dict) -> None:
    """**守衛的認人方式要跟著合約走。**

    這條檢查原本寫死比對字串 `"totalCents"`。欄位名改歸合約擁有之後,
    規格只要取別的名字(訪談那份取了 `total_cents`),那條不變式就
    **靜靜地永遠不再檢查** —— 守衛沒有壞掉,是不再適用,而不適用沒有人會發現。
    """
    for old, new in (("totalCents", "total_cents"),):
        spec["wire_contract"]["res_total_field"] = new
        spec["wire_contract"]["list_fields"] = [
            new if f == old else f for f in spec["wire_contract"]["list_fields"]]
        for sc in spec["acceptance_scenarios"]:
            for a in sc.get("assertions") or []:
                if a.get("field") == old:
                    a["field"] = new
    assert spec_store._check_shape(spec) == []
    # 總額寫錯 → 即使欄位叫 total_cents,也要被抓到
    scenario(spec, "S3")["assertions"][-1]["expected_number"] = 9999
    assert any("期望 9999" in p for p in spec_store._check_shape(spec))


def test_沒宣告總額欄位卻斷言數字要紅(spec: dict) -> None:
    """不適用要講出來。悶著的話,那條不變式就從驗收裡消失了。"""
    spec["wire_contract"]["res_total_field"] = None
    assert any("res_total_field" in p for p in spec_store._check_shape(spec))


def test_夾帶總金額但合約沒有那個欄位要紅(spec: dict) -> None:
    """沒宣告 req_total_field 卻填了值,生成器會產出 `"None":5000` ——
    import 過、Java 編得起來、跑起來測的是一個不存在的欄位。"""
    spec["wire_contract"]["req_total_field"] = None
    assert any("req_total_field" in p for p in spec_store._check_shape(spec))


def test_proxy_for_是可查詢的欄位不是註解(tmp_path: Path) -> None:
    """代理編碼的自白要能 SELECT 得出來 —— 那就是分診佇列。
    **它不是偵測器**,擋不住存心不填的;買的是「誠實的情況查得到」。"""
    import sqlite3
    spec = {
        "wire_contract": {
            "name": "t", "req_customer_field": "customerId", "req_items_field": "items",
            "req_product_field": "productId", "req_quantity_field": "quantity",
            "req_price_field": "unitPriceCents", "req_currency_field": "currency",
            "res_order_id_field": "orderId", "list_fields": ["orderId"],
        },
        "acceptance_scenarios": [{
            "id": "S10", "given_when": "商品事後調價", "then_expect": "舊單金額不動",
            "provenance": "Qn", "provenance_ref": "[Q9] L105",
            "proxy_for": "schema 沒有「調整商品單價」這個動作,改用同商品的第二筆訂單近似",
            "steps": [{"alias": "before", "customer_id": "C-007",
                       "items": [{"product_id": "mug", "quantity": 1,
                                  "unit_price_cents": 10000, "currency": "TWD"}]}],
            "assertions": [{"kind": "status_is", "target": "before", "expected_number": 201}],
        }]
    }
    db = tmp_path / "p.db"
    spec_store.build_store(db, spec)
    rows = list(sqlite3.connect(db).execute(
        "SELECT id, proxy_for FROM acceptance_scenario WHERE proxy_for IS NOT NULL"))
    assert len(rows) == 1 and rows[0][0] == "S10"


# ── 代理編碼分 class(2026-08-18,Nat 拍板)──────────────────────────────

def test_代理編碼生到另一個_class(spec: dict, tmp_path: Path) -> None:
    """真情境與代理編碼**不得混在同一份綠燈裡**。

    2026-08-18 重跑量到:12 條落檔裡 4 條是代理編碼,而落檔率(12/12)
    完全看不出真實覆蓋只有 8。分 class 是為了讓那個差距在**跑測試**時就看得見。
    """
    import gen_acceptance
    scenario(spec, "S1")["proxy_for"] = "schema 沒有那個動作,用別的東西近似"
    db = tmp_path / "p.db"
    spec_store.build_store(db, spec)
    main = tmp_path / "OrderAcceptanceTest.java"
    names = gen_acceptance.generate(db, main)
    proxy = tmp_path / "OrderProxyAcceptanceTest.java"

    assert proxy.exists()
    assert "OrderProxyAcceptanceTest.scenario_S1" in names
    assert "scenario_S1" not in main.read_text(encoding="utf-8")
    assert "scenario_S1" in proxy.read_text(encoding="utf-8")
    # 自白要走到讀 Java 的人面前 —— 存在 store 裡不算
    assert "代理編碼" in proxy.read_text(encoding="utf-8")
    assert "綠了" in proxy.read_text(encoding="utf-8")


def test_沒有代理編碼就不留下空的_proxy_class(spec: dict, tmp_path: Path) -> None:
    """留著舊檔會讓 drift check 拿舊的比新的 —— 又一個「不適用被讀成通過」。"""
    import gen_acceptance
    db = tmp_path / "p.db"
    spec_store.build_store(db, spec)
    proxy = tmp_path / "OrderProxyAcceptanceTest.java"
    proxy.write_text("殘留的舊檔", encoding="utf-8")
    gen_acceptance.generate(db, tmp_path / "OrderAcceptanceTest.java")
    assert not proxy.exists()
