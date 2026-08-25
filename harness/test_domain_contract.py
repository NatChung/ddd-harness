"""領域契約進 store(票 06-A / ADR 0005)。

測試名字照這條線的慣例寫成「寫不進去」而不是「驗證失敗」——
那是第 1 階(schema 的 CHECK / FK / TRIGGER)跟第 2 階(spec_store 的跨列檢查)的差別,
**而這張票有一條規則刻意住第 2 階**:「指不出任何測試時必須說出理由」要跨表數列,
SQLite 的 CHECK 寫不出來。下面把那條也釘住,並釘住它住在哪一階。

預測寫在 `.scratch/ddd-harness/06-PREDICTION.md`,commit 在寫程式之前。
"""

from __future__ import annotations

import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from spec_store import SCHEMA_PATH, SpecError, build_store, load_spec

CONTRACT = {
    "id": "C1",
    "kind": "invariant",
    "statement": "總額等於各明細的乘加",
    "provenance": "Qn",
    "provenance_ref": "[Q1]",
    "guarded_in": "訂單 Order(自足)",
    "enforcement": "none",
    "ladder_note": "算術型,今天的驗收詞彙表達不出來",
    "no_named_test_reason": "本輪這場訪談的情境還沒落檔",
}


def contract(**changes):
    c = dict(CONTRACT)
    c.update(changes)
    return {"domain_contracts": [c]}


def problems_of(tmp_path, spec) -> list[str]:
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", spec)
    return exc.value.problems


# ── 第 1 階:填不了就寫不進去 ──────────────────────────────────────────────

def test_自創第六格來源寫不進去(tmp_path):
    problems = problems_of(tmp_path, contract(provenance="訪談推測"))
    assert any("schema 擋下來了" in p for p in problems), problems


PROVENANCE_CHECK = re.compile(
    r"provenance[^,]*?IN\s*\((\s*'[^)]*?)\)", re.S)


def test_五格來源與架構規則逐字相同(tmp_path):
    """名字說「逐字相同」,那就真的去比 —— 不然這個名字是空頭支票。

    ⚠️ 原本這支只驗「這 4 個值匯得進去」,**跟 `architecture_rule` 一個字都沒比**。
       實測(2026-08-18 稽核 §三.3 的疑點,補驗成立):給 `domain_contract` 的值域
       偷加第六格 `'訪談者判斷'`,**194 支測試全綠** —— 只有 `'訪談推測'` 那一個
       字串被 `test_自創第六格來源寫不進去` 撞到,換個字就整條漂走。
       ADR 0005 §1「不得為新表發明第六格或改寫格名」因此沒有守衛。
    """
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    clauses = PROVENANCE_CHECK.findall(schema)
    # 四張表都掛 provenance:architecture_rule / acceptance_scenario /
    # domain_contract / glossary_term。少一張就是有人新增表時漏掛,也要吵。
    assert len(clauses) == 4, f"provenance 值域宣告數 {len(clauses)},預期 4 張表"
    normalised = {" ".join(c.split()) for c in clauses}
    assert normalised == {"'Qn', '暫定', '推導自', '模板既定', '本案自決'"}, normalised

    for provenance in ("Qn", "暫定", "推導自", "本案自決"):
        build_store(tmp_path / "spec.db", contract(provenance=provenance))


def test_模板既定_在白名單為空時寫不進去(tmp_path):
    problems = problems_of(tmp_path, contract(provenance="模板既定"))
    assert any("模板既定" in p for p in problems), problems


def test_契約型態只有三種(tmp_path):
    problems = problems_of(tmp_path, contract(kind="business_rule"))
    assert any("schema 擋下來了" in p for p in problems), problems


def test_守在哪個物件內不得留空(tmp_path):
    problems = problems_of(tmp_path, contract(guarded_in="   "))
    assert any("缺 guarded_in" in p or "schema 擋下來了" in p for p in problems), problems


def test_跨聚合根而沒寫處置會被擋_兩階都擋得住(tmp_path):
    """⚠️ 名字寫「會被擋」不寫「寫不進去」:**先擋下來的是第 2 階**。

    第 2 階先跑,所以匯入路徑拿到的是看得懂的訊息;而 schema 的 CHECK 也真的擋得住
    —— 兩半分開驗,不然那條 CHECK 沒有任何直接覆蓋,哪天被刪掉也不會有人發現。
    """
    problems = problems_of(tmp_path, contract(crosses_aggregate=1))
    assert any("必須寫 disposition" in p for p in problems), problems

    # 繞過第 2 階,直接餵給 schema:這一半驗的是第 1 階那條 CHECK 自己。
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO domain_contract (id, kind, statement, provenance, "
                "provenance_ref, guarded_in, crosses_aggregate, enforcement, ladder_note) "
                "VALUES ('C1','precondition','x','Qn','[Q1]','訂單',1,'none','n')"
            )
    finally:
        conn.close()


def test_指名測試指向不存在的情境寫不進去(tmp_path):
    """FK 指 acceptance_scenario —— 打字錯成一個不存在的編號,第 1 階就擋下來。

    這條**刻意只有 FK 一份載體**:在 spec_store 再擋一次,同一條規則就有兩份會漂。
    """
    spec = contract(named_tests=["S99"], no_named_test_reason=None)
    problems = problems_of(tmp_path, spec)
    assert any("schema 擋下來了" in p for p in problems), problems


def test_指名測試指得到的情境寫得進去(tmp_path):
    spec = load_spec(Path(__file__).with_name("fixtures") / "negative-scenarios.yaml")
    spec["domain_contracts"] = [dict(CONTRACT, named_tests=["S4"],
                                     no_named_test_reason=None)]
    db = tmp_path / "spec.db"
    build_store(db, spec)
    conn = sqlite3.connect(db)
    try:
        assert conn.execute("SELECT scenario_id FROM contract_named_test").fetchall() \
            == [("S4",)]
    finally:
        conn.close()


def test_模板既定的洞在驗收情境上也補起來了(tmp_path):
    """trigger 原本只掛在 architecture_rule —— acceptance_scenario 漏掛(schema.sql:59)。"""
    spec = load_spec(Path(__file__).with_name("fixtures") / "negative-scenarios.yaml")
    spec["acceptance_scenarios"][0]["provenance"] = "模板既定"
    problems = problems_of(tmp_path, spec)
    assert any("模板既定" in p for p in problems), problems


# ── 第 2 階:擋得住,但擋的是 script ────────────────────────────────────────

def test_零列而沒說理由會被擋_而且這條住第2階(tmp_path):
    """「零列時必填」要跨表數 contract_named_test 的列數 —— CHECK 寫不出來。

    釘住它住在第 2 階:schema 單獨吃得下這一列,是 spec_store 擋的。
    """
    spec = contract(no_named_test_reason=None)
    problems = problems_of(tmp_path, spec)
    assert any("no_named_test_reason" in p for p in problems), problems
    assert not any("schema 擋下來了" in p for p in problems), problems

    # 同一列直接塞進 schema:第 1 階放行 —— 這就是「住第 2 階」的意思。
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO domain_contract (id, kind, statement, provenance, "
            "provenance_ref, guarded_in, enforcement, ladder_note) "
            "VALUES ('C1','invariant','x','Qn','[Q1]','訂單','none','n')"
        )
    finally:
        conn.close()


def test_既有指名測試又寫理由會被擋(tmp_path):
    spec = contract(named_tests=["S4"], no_named_test_reason="規格沉默")
    problems = problems_of(tmp_path, spec)
    assert any("兩者只能有一個" in p for p in problems), problems


def test_處置寫成指標會被擋(tmp_path):
    """處置存本文,不存「見某節」—— 指過去了而下游沒有任何一步會讀那一節。

    ⚠️ 後三個是 2026-08-18 稽核 §二.D 補的:原本的規則**只錨行首**,
       所以「整格就是一個指標」的 `處置:見 §9` 只因為前面多了兩個字就過關 ——
       ADR §3 要的是「存本文」,買到的卻是「開頭不是『見』」。
    """
    for pointer in ("見 §9", "詳見 §9-A9", "同上",
                    "處置:見 §9", "處置: 見 §9", "理由:見上"):
        spec = contract(crosses_aggregate=1, disposition=pointer)
        problems = problems_of(tmp_path, spec)
        assert any("寫成了指標" in p for p in problems), (pointer, problems)


def test_處置寫本文就過(tmp_path):
    """另一邊的界線:**擋的是「整格就是一個指標」,不是「出現了指標字」。**

    正當的處置本文裡本來就會出現「見」;擋過頭會把真的處置逼成假的,
    那跟擋不住一樣糟。這幾條全部要放行。
    """
    for body in (
        "不新增聚合根,檢查移到 application 層,在建構聚合之前完成。",
        "處置:不新增聚合根,檢查移到 application 層。",   # 掛了標籤,但後面有本文
        "殘留風險見下段說明,處置是不新增聚合根。",         # 「見」不在開頭
        "同 C12 的處置,見上",                              # 指了,但也說了是哪一條
    ):
        build_store(tmp_path / "spec.db",
                    contract(crosses_aggregate=1, disposition=body))


def test_沒跨聚合根卻填處置會被擋(tmp_path):
    problems = problems_of(tmp_path, contract(disposition="移到 application 層"))
    assert any("那一欄是給" in p for p in problems), problems


def test_宣稱有機械檢查會被擋(tmp_path):
    """今天沒有任何生成器讀 domain_contract —— 宣稱有就是空頭支票。

    ⚠️ 這是對 ADR 0005 §2「三欄照抄」的解讀:照抄的是**語意**不是值域清單。
       值域會在結構型契約的生成器落地時擴。
    """
    problems = problems_of(tmp_path, contract(enforcement="archunit_forbidden_dependency"))
    assert any("enforcement 只能是" in p for p in problems), problems


def test_無機械檢查而沒寫階梯說明會被擋(tmp_path):
    problems = problems_of(tmp_path, contract(ladder_note=None))
    assert any("ladder_note" in p for p in problems), problems


def test_agent_不得自己寫由誰強制(tmp_path):
    problems = problems_of(tmp_path, dict(contract(), **{
        "domain_contracts": [dict(CONTRACT, enforced_by="OrderTest.c1")]}))
    assert any("enforced_by 不得由 spec 提供" in p for p in problems), problems


def test_未知欄位當場掛(tmp_path):
    problems = problems_of(tmp_path, contract(**{"守在哪個聚合根內": "訂單"}))
    assert any("未知的 key" in p for p in problems), problems


def test_契約區塊是選填的(tmp_path):
    """必填會打到 fixtures/negative-scenarios.yaml —— 那是測試在用的(ADR 0005 §6)。"""
    spec = load_spec(Path(__file__).with_name("fixtures") / "negative-scenarios.yaml")
    assert "domain_contracts" not in spec
    build_store(tmp_path / "spec.db", spec)


def test_只有契約的一份檔不算空的_spec(tmp_path):
    build_store(tmp_path / "spec.db", contract())


# ── PRAGMA foreign_keys 的行為測試(ADR 0005 §7)────────────────────────────
#
# 驗的是**行為**(FK 真的擋得住),不是「那一行還在」。
# ⚠️ 兩份載體(schema.sql 的 PRAGMA 與 spec_store 匯入時那句)**任一份單獨存在
#    就足以讓 FK 生效** —— 所以一支測試不可能兩份都覆蓋,要兩支各自隔離。
#    每一支都先確認「破壞本身生效了」,不然會拿到假通過。

PRAGMA_LINE = "PRAGMA foreign_keys = ON;"


def _schema_without_pragma() -> str:
    """拿掉 schema.sql 那份載體 —— **並且證明真的拿掉了**。

    ⚠️ 原本兩支測試各自寫 `assert PRAGMA_LINE not in stripped`,那是**恆真形狀**:
       `PRAGMA_LINE` 一旦跟 `schema.sql` 對不上(空白、換行、大小寫),`replace` 是
       no-op,而 `X not in stripped` **恰好因此空洞地成立**。實測過:把 schema.sql 的
       `= ON;` 改成語意完全相同的 `=ON;`,載體二那支照樣綠 —— 而它此刻驗的是載體一。
       (2026-08-18 稽核 §二.C。)

    改成驗**破壞本身**:那一行原本在(不然常數漂了,要當場吵),而且拿掉之後
    字串**真的不一樣了**。
    """
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    assert PRAGMA_LINE in schema, (
        f"mutated 沒生效:schema.sql 裡找不到 {PRAGMA_LINE!r} —— "
        "常數跟 schema 漂開了(改了空白也算),這支測試已經不知道自己在驗什麼"
    )
    stripped = schema.replace(PRAGMA_LINE, "")
    assert stripped != schema, "mutated 沒生效:replace 是 no-op"
    assert PRAGMA_LINE not in stripped, "mutated 沒生效:那一行沒被拿乾淨"
    return stripped


def _violating_insert(conn) -> None:
    conn.execute(
        "INSERT INTO contract_named_test (contract_id, scenario_id, seq) "
        "VALUES ('C-nope', 'S-nope', 0)"
    )


def test_載體一_schema裡那句PRAGMA自己就擋得住(tmp_path):
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    # 破壞本身要先生效:拿掉那一行之後,FK 靜靜地不再擋 —— 這一半證明它承重。
    stripped = _schema_without_pragma()
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(stripped)
        _violating_insert(conn)      # 不該擋 —— 擋了表示這支測試根本沒隔離到
        print("mutated ok:拿掉 schema.sql 的 PRAGMA 之後,違規列真的寫得進去")
    finally:
        conn.close()

    # 原樣的 schema:只靠這一句,FK 就擋得住。
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(schema)
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            _violating_insert(conn)
    finally:
        conn.close()


def test_載體二_匯入路徑那句PRAGMA自己就擋得住(tmp_path, monkeypatch):
    """把 schema.sql 那份載體拿掉,只剩 spec_store 匯入時開的那一次。"""
    stripped = _schema_without_pragma()
    schema_copy = tmp_path / "schema-no-pragma.sql"
    schema_copy.write_text(stripped, encoding="utf-8")
    print("mutated ok:餵給 build_store 的 schema 已經沒有那句 PRAGMA")

    monkeypatch.setattr("spec_store.SCHEMA_PATH", schema_copy)
    spec = contract(named_tests=["S99"], no_named_test_reason=None)
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", spec)
    assert any("FOREIGN KEY" in p for p in exc.value.problems), exc.value.problems


# ── 真實轉寫:數字釘住,分診跑得出來 ──────────────────────────────────────


def _triage(db: Path):
    return subprocess.run(
        [sys.executable, str(Path(__file__).with_name("contract_triage.py")), str(db)],
        capture_output=True, text=True, check=False)


def test_契約零條時報表印不適用而不是通過(tmp_path):
    """選填的病:不適用不會有人發現。所以它自成一類、有自己的離開碼。"""
    db = tmp_path / "triage-empty.db"
    build_store(db, load_spec(
        Path(__file__).with_name("fixtures") / "negative-scenarios.yaml"))
    out = _triage(db)
    assert out.returncode == 3, out.stdout
    assert "不適用(不是通過)" in out.stdout
    assert "通過" not in out.stdout.split("不適用(不是通過)")[0]


# ── 報表的閘門:exit 1 那條路,以及「兩欄不得合併」──────────────────────────
#
# ⚠️ 2026-08-18 稽核 §二.B:在這幾支寫出來以前,`contract_triage` 的閘門**一支測試
#    都沒有** —— 把 `return 1 if … else 0` 改成無條件 `return 0`、或把「有指名測試」
#    折進「宣稱有機械檢查」,24 支測試全綠。後者正是 ADR 0005 §2 明文禁止、
#    也是票 06 整個命題所在的合併。


def test_有指名測試不等於有機械檢查_兩欄分開印(tmp_path):
    """**這張票的整個命題。**(ADR 0005 §2)

    C1 的指名測試是 `S1, S2, S3, S5`,看起來「有人在守」;但 C1 說的是
    「**任何時候**總金額都等於明細加總」,一個情境只證明了「**這一筆**算對了」。
    讓「有指名測試」算成「有機械檢查」,就把 invariant → example 的降級整個蓋掉。

    所以這裡刻意造一個 **with_test = 1 而 with_enforcement = 0** 的 store:
    兩個數字**必須不一樣**。任何一個方向的合併(把 enforcement 抄成 test、
    或把 test 抄成 enforcement)都會在這支翻紅。
    """
    spec = load_spec(Path(__file__).with_name("fixtures") / "negative-scenarios.yaml")
    spec["domain_contracts"] = [dict(CONTRACT, named_tests=["S4"],
                                     no_named_test_reason=None)]
    db = tmp_path / "one-named-test.db"
    build_store(db, spec)
    out = _triage(db)

    assert "有指名測試的:1 條" in out.stdout, out.stdout
    assert "宣稱有機械檢查的(enforcement <> none):0 條" in out.stdout, out.stdout
    # 沒有待處理項目 —— 這一半同時釘住閘門不是「無條件回 1」。
    assert out.returncode == 0, (out.returncode, out.stdout)
