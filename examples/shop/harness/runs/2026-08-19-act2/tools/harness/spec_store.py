#!/usr/bin/env python3
"""spec.yaml → 驗證 → SQLite store。

第 5 題的介面:**agent 只交資料,碰不到 schema。**
它交一份 yaml/json,這支 script 驗證後匯入;失敗就退回一份逐條錯誤,agent 改完再交。
schema 是我們的,agent 改不掉 —— 那才是第 1 階。

兩層強度,不要混:
  * schema.sql 的 CHECK / REFERENCES / TRIGGER  = 第 1 階(填不了就寫不進去)
  * 本檔的跨列不變式(kind ↔ 參數要不要有)      = 第 2 階(會被擋下來,但擋的是 script)

用法:
    python3 spec_store.py import <spec.yaml> [<spec2.yaml> …] <out.db>

相依:JSON 只用標準庫;YAML 需要 PyYAML(lazy import,沒裝就只能餵 JSON)。
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).with_name("schema.sql")

# 每個 enforcement kind 的參數形狀與落點。加新 kind 就在這裡加一列
# —— 別讓 kind 的分支散進 _check_shape 和 build_store 兩處。
KINDS: dict[str, dict[str, Any]] = {
    "archunit_forbidden_dependency": {
        "param": "forbidden_dependencies",
        "scalars": {"from": "from_package"},
        "list_key": "to",
        "table": "forbidden_dependency",
        "value_column": "to_package",
    },
    "archunit_forbidden_annotation": {
        "param": "forbidden_annotations",
        "scalars": {"from": "from_package"},
        "list_key": "annotations",
        "table": "forbidden_annotation",
        "value_column": "annotation_package",
    },
    "archunit_forbidden_return_type": {
        "param": "forbidden_return_types",
        # 這個 kind 的來源是「package × 類名形狀」,不只是 package
        # —— 不能整個 adapter 層都禁回傳 domain 型別,Repository 本來就該回傳 Order。
        "scalars": {"from": "from_package", "class_name_suffix": "class_name_suffix"},
        "list_key": "return_packages",
        "table": "forbidden_return_type",
        "value_column": "return_package",
    },
}

SPEC_KEYS = {"authorized_templates", "architecture_rules", "acceptance_scenarios",
             "wire_contract", "domain_contracts", "glossary_terms", "banned_synonyms"}

# wire_contract 的必填欄(ADR 0004)。**全部必填,沒有預設值** ——
# 給預設值等於偷偷幫規格決定 wire shape,而那正是這一輪要拿掉的東西。
WIRE_REQUIRED = (
    "name",
    "req_customer_field", "req_items_field", "req_product_field",
    "req_quantity_field", "req_price_field", "req_currency_field",
    "res_order_id_field",
)
WIRE_OPTIONAL = ("req_total_field", "res_customer_id_field", "res_total_field",
                 "list_fields")
RULE_KEYS = {
    "id",
    "rule",
    "provenance",
    "provenance_ref",
    "enforcement",
    "ladder_note",
} | {k["param"] for k in KINDS.values()}


# 領域契約(ADR 0005)。**選填** —— 必填會打到 fixtures/negative-scenarios.yaml,
# 那是測試在用的,逼它長出一份與它無關的契約清單等於在測試資料裡塞假東西。
# 但選填有它自己的病:**不適用不會有人發現**。所以報表那一側綁死一條
# 「不適用不准算成通過」(contract_triage.py),不要只靠這裡。
CONTRACT_KEYS = {
    "id", "kind", "statement", "provenance", "provenance_ref",
    "guarded_in", "crosses_aggregate", "disposition",
    "enforcement", "ladder_note",
    "named_tests", "no_named_test_reason",
}

# 今天沒有任何生成器讀 domain_contract,所以值域只有 none(見 schema.sql 的註解)。
CONTRACT_ENFORCEMENTS = {"none"}

# 「處置」存本文,不存指標。認得出來的幾種指標寫法擋在這裡 ——
# **這是第 2 階**,schema 那邊只擋得住「旗標 = 1 卻整格空白」。
POINTER_WORD = r"(?:見|參見|詳見|同上|見上|如上|見前)"
POINTER_ONLY = re.compile(rf"^\s*{POINTER_WORD}")

# ⚠️ 上面那條**只錨行首**,所以 `處置:見 §9` ——「整格就是一個指標,一個字的本文都沒有」
#    —— 只因為前面多了兩個字就過關(2026-08-18 稽核 §二.D)。
#    補的這條收的是**掛了一個標籤的純指標**:短標籤 + 冒號 + 指標詞 + 一小段引用,然後就沒了。
#    刻意收得窄 —— 「寧可只擋整格就是一個指標的情況」:標籤後面只要有本文
#    (`處置:不新增聚合根,檢查移到…`),或指標後面接得下一句話,一律放行。
#    正當的處置本文裡本來就可能出現「見」字,擋過頭會把真的處置逼成假的。
LABELLED_POINTER_ONLY = re.compile(
    rf"^\s*[^\s,,。;;::]{{1,6}}[::]\s*{POINTER_WORD}[^,,。;;]{{0,12}}$"
)


def _is_pointer_only(text: str) -> bool:
    """整格就是一個指標(可以掛一個標籤),沒有任何本文。"""
    return bool(POINTER_ONLY.match(text) or LABELLED_POINTER_ONLY.match(text))


# 詞彙表(ADR 0005 §4)。**選填**,理由與 domain_contracts 相同。
# 「禁用同義詞」是**第二個頂層區塊**而不是巢在詞底下:一個講法可以**沒有替代詞**
# (它指的東西在本案不存在),那種列巢不進任何一個詞。ADR 定的是**子表**的形狀,
# 沒有定 yaml 的形狀 —— 這是本輪的決定,寫在這裡而不是散在註解裡。
GLOSSARY_KEYS = {
    "term", "definition", "ddd_type", "representation", "wire_field",
    "provenance", "provenance_ref",
}
BANNED_SYNONYM_KEYS = {"banned", "use_instead", "no_replacement_note", "note"}

# 「對外欄位名」要是**一個欄位名**,不是散文那一格的原文。
# 散文那一格裝得下註記(括號說明、型態記號、指向別列的指標),而那些東西
# 拿去跟合約比對永遠不會中 —— **靜靜地不中**,那正是本線最怕的失效形狀。
# 所以在這裡擋下來,逼轉寫的人當場決定:要嘛給一個真的欄位名,要嘛留空(= 不上線)。
WIRE_FIELD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


ASSERTION_KINDS: dict[str, set[str]] = {
    "status_is": {"expected_number"},
    "order_id_not_blank": set(),
    "list_row_exists": set(),
    "list_field_equals_text": {"field", "expected_text"},
    "list_field_equals_number": {"field", "expected_number"},
    "list_field_is_iso_date": {"field"},
}


class SpecError(Exception):
    """驗證失敗。`problems` 是逐條錯誤 —— 這就是回饋給 agent 的東西。"""

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__("\n".join(problems))


class NothingToGenerate(Exception):
    """這份 store 沒有這個生成器要的東西 —— **不適用,不是錯誤,也不是通過**。

    為什麼不是 `SystemExit`:`generate()` 是**函式**,而 `SystemExit` 在被 import
    進來呼叫時會把呼叫方整支打死。`verify_generated.py` 2026-08-18 在「沒有
    architecture_rule 的 store」上就是這樣 crash 的 —— stdout 一行都沒印、exit 1,
    於是**那份 store 的 drift check 從此量不到**,而且量不到的樣子跟「有東西漂了」
    長得一模一樣(票 10 的 P4 就是這樣落空的)。

    「沒東西可生成」與「呼叫方式錯了 / 目錄不見」是**兩件事**,不准折成同一個結果:
    前者是不適用(離開碼 3),後者是錯誤(離開碼 2)。**也不准折進通過** ——
    生成器不適用時,它那些檔案這一次**沒有被檢查過**(ADR 0005 §6)。
    """


def load_specs(paths: list[str | Path]) -> dict[str, Any]:
    """把多份 spec 檔合併成一份。同一個 key 出現在兩個檔就串起來。

    分檔的理由是**關注點**:架構規則與驗收情境是不同的東西、不同的 reviewer、
    不同的改動節奏。合併發生在這裡,不是要人自己 concat。
    """
    merged: dict[str, Any] = {}
    for path in paths:
        for key, value in load_spec(path).items():
            if isinstance(value, list):
                merged.setdefault(key, []).extend(value)
            else:
                merged[key] = value
    return merged


def load_spec(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # noqa: PLC0415  (lazy: JSON 路徑不需要相依)
        except ModuleNotFoundError as exc:  # pragma: no cover - 環境相關
            raise SpecError(
                [f"{path.name} 是 YAML,但這個環境沒有 PyYAML。改交 JSON,或 pip install PyYAML。"]
            ) from exc
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise SpecError([f"{path.name} 的頂層必須是 mapping,拿到 {type(data).__name__}"])
    return data


def _check_shape(spec: dict[str, Any]) -> list[str]:
    """形狀檢查。未知的 key 一律報錯 —— 打錯欄位名要當場掛,不要靜默忽略。"""
    problems: list[str] = []

    unknown = set(spec) - SPEC_KEYS
    if unknown:
        problems.append(f"頂層有未知的 key:{sorted(unknown)};允許的是 {sorted(SPEC_KEYS)}")

    # spec 是分段組成的(架構規則 / 驗收情境),一份檔案只帶其中一段是正常的
    # —— 硬性要求每份都帶全部,會逼交件者為了讓工具閉嘴而捏造它沒被要求產出的東西。
    rules = spec.get("architecture_rules") or []
    if not isinstance(rules, list):
        problems.append("architecture_rules 必須是 list")
        rules = []
    if not rules and not spec.get("acceptance_scenarios") \
            and not spec.get("domain_contracts") and not spec.get("glossary_terms"):
        problems.append(
            "spec 是空的:architecture_rules / acceptance_scenarios / domain_contracts "
            "/ glossary_terms 至少要有一段"
        )

    problems += _check_wire_contract(spec)

    for i, rule in enumerate(rules):
        where = f"architecture_rules[{i}]"
        if not isinstance(rule, dict):
            problems.append(f"{where} 必須是 mapping")
            continue
        rid = rule.get("id", f"<第 {i} 條,沒有 id>")
        unknown = set(rule) - RULE_KEYS
        if unknown:
            problems.append(f"{rid}:未知的 key {sorted(unknown)};允許的是 {sorted(RULE_KEYS)}")
        for required in ("id", "rule", "provenance", "provenance_ref", "enforcement"):
            if not rule.get(required):
                problems.append(f"{rid}:缺 {required}")
        if "enforced_by" in rule:
            problems.append(
                f"{rid}:enforced_by 不得由 spec 提供 —— 那一欄由生成器回填"
                "(誰強制的,只有生成器知道)"
            )

        # 第 2 階:kind ↔ 參數的不變式。宣稱有機械檢查就必須給得出參數;
        # 宣稱沒有就不准給參數,而且必須寫明為什麼還住第 4 階。
        kind = rule.get("enforcement")
        supplied = {name for name in (k["param"] for k in KINDS.values()) if rule.get(name)}

        if kind in KINDS:
            shape = KINDS[kind]
            params = rule.get(shape["param"])
            stray = supplied - {shape["param"]}
            if stray:
                problems.append(f"{rid}:enforcement={kind} 不該帶 {sorted(stray)}")
            wanted = ", ".join(f"{k}: <…>" for k in shape["scalars"])
            if not isinstance(params, dict):
                problems.append(
                    f"{rid}:enforcement={kind} 必須帶 "
                    f"{shape['param']}: {{{wanted}, {shape['list_key']}: [<pkg..>, …]}}"
                )
            else:
                unknown = set(params) - set(shape["scalars"]) - {shape["list_key"]}
                if unknown:
                    problems.append(f"{rid}.{shape['param']}:未知的 key {sorted(unknown)}")
                for scalar in shape["scalars"]:
                    if not params.get(scalar):
                        problems.append(f"{rid}.{shape['param']}:缺 {scalar}")
                values = params.get(shape["list_key"])
                if not isinstance(values, list) or not values:
                    problems.append(
                        f"{rid}.{shape['param']}:{shape['list_key']} 必須是非空的 list"
                    )
        elif kind == "none":
            if supplied:
                problems.append(
                    f"{rid}:enforcement=none 不該帶 {sorted(supplied)} —— "
                    "沒有機械檢查就沒有參數可填"
                )
            if not rule.get("ladder_note"):
                problems.append(
                    f"{rid}:enforcement=none 必須寫 ladder_note(為什麼還住第 4 階、搬得上去嗎)"
                )
        elif kind is not None:
            problems.append(
                f"{rid}:enforcement 只能是 {sorted(KINDS)} 或 none,拿到 {kind!r}"
            )

    problems += _check_scenarios(spec, spec.get("wire_contract") or {})
    problems += _check_contracts(spec)
    problems += _check_glossary(spec)
    return problems


def _check_contracts(spec: dict[str, Any]) -> list[str]:
    """領域契約的第 2 階(ADR 0005 §2、§3)。

    這裡擋的兩條,**SQLite 的 CHECK 都寫不出來**:

    * 「指不出任何測試時必須說出理由」——要跨表數 contract_named_test 的列數。
    * 「處置存本文,不存指標」——指標是文字形狀,不是欄位存在性。

    而「指名測試指向不存在的情境」**刻意不在這裡**:那條由 FK 擋(第 1 階),
    在這裡再擋一次就會變成同一條規則有兩份載體,而兩份規則會漂。
    """
    problems: list[str] = []
    contracts = spec.get("domain_contracts")
    if contracts is None:
        return problems
    if not isinstance(contracts, list):
        return ["domain_contracts 必須是 list"]

    for i, c in enumerate(contracts):
        where = f"domain_contracts[{i}]"
        if not isinstance(c, dict):
            problems.append(f"{where} 必須是 mapping")
            continue
        cid = c.get("id", f"<第 {i} 條契約,沒有 id>")

        unknown = set(c) - CONTRACT_KEYS
        if unknown:
            problems.append(
                f"{cid}:未知的 key {sorted(unknown)};允許的是 {sorted(CONTRACT_KEYS)}"
            )
        for required in ("id", "kind", "statement", "provenance", "provenance_ref",
                         "guarded_in", "enforcement"):
            if not c.get(required):
                problems.append(f"{cid}:缺 {required}")
        if "enforced_by" in c:
            problems.append(
                f"{cid}:enforced_by 不得由 spec 提供 —— 那一欄由生成器回填"
                "(誰強制的,只有生成器知道)"
            )

        kind = c.get("enforcement")
        if kind is not None and kind not in CONTRACT_ENFORCEMENTS:
            problems.append(
                f"{cid}:enforcement 只能是 {sorted(CONTRACT_ENFORCEMENTS)},拿到 {kind!r}"
                " —— 今天沒有任何生成器讀 domain_contract,宣稱有機械檢查就是空頭支票"
            )
        elif kind == "none" and not c.get("ladder_note"):
            problems.append(
                f"{cid}:enforcement=none 必須寫 ladder_note(為什麼還住第 4 階、搬得上去嗎)"
            )

        # 「守在哪」的三欄:旗標 / 處置。schema 擋得住「旗標=1 卻整格空白」,
        # 擋不住「填了一個指標」與「沒跨聚合根卻填了處置」。
        crosses = bool(c.get("crosses_aggregate"))
        disposition = c.get("disposition")
        if crosses and not str(disposition or "").strip():
            problems.append(
                f"{cid}:crosses_aggregate=1 必須寫 disposition —— "
                "「這條守不住」要配一個處置,不然分診佇列撈出來也不知道下一步"
            )
        if disposition and _is_pointer_only(str(disposition)):
            problems.append(
                f"{cid}:disposition 寫成了指標({str(disposition)[:20]!r}…)—— "
                "處置要存本文。指過去了而下游沒有任何一步會去讀那一節,"
                "**寫在該寫的地方不等於接上了**"
            )
        if disposition and not crosses:
            problems.append(
                f"{cid}:沒有 crosses_aggregate 卻填了 disposition —— "
                "那一欄是給「守不住的契約」用的"
            )

        # 「指名測試」零列時必填理由(ADR 0005 §2)。
        # 零列跟「還沒填」長得一樣,所以要逼出理由;反過來,指得出測試就不該有理由。
        named = c.get("named_tests") or []
        if not isinstance(named, list):
            problems.append(f"{cid}:named_tests 必須是 list")
            named = []
        if len(set(named)) != len(named):
            problems.append(f"{cid}:named_tests 有重複的情境編號 {sorted(named)}")
        reason = str(c.get("no_named_test_reason") or "").strip()
        if not named and not reason:
            problems.append(
                f"{cid}:指不出任何測試(named_tests 是空的),必須寫 "
                "no_named_test_reason —— **零列跟「還沒填」長得一樣**"
            )
        if named and reason:
            problems.append(
                f"{cid}:既有 named_tests 又寫了 no_named_test_reason —— 兩者只能有一個"
            )
    return problems


def _check_glossary(spec: dict[str, Any]) -> list[str]:
    """詞彙表的第 2 階(ADR 0005 §4)。

    這裡擋的三條,**SQLite 的 CHECK 都寫不出來**(或寫得出來但會擋錯東西):

    * 「對外欄位名要是一個欄位名,不是散文那一格的原文」——那是文字形狀。
    * 「有禁用同義詞就必須有詞彙表」——要跨區塊看。
    * 「一律改用 與 沒有替代詞的理由 只能有一個」——同列 CHECK 擋得住「兩個都沒有」,
      擋不住「兩個都有」那種自相矛盾。

    而下面這兩條**刻意不在這裡**,它們由第 1 階擋:

    * 「一律改用 指向一個詞彙表裡不存在的詞」→ FK。
    * 「兩個詞宣稱同一個對外欄位名」→ UNIQUE。

    在這裡再擋一次會變成同一條規則有兩份載體,而**兩份規則會漂**。
    """
    problems: list[str] = []
    terms = spec.get("glossary_terms")
    banned_rows = spec.get("banned_synonyms")

    if terms is not None and not isinstance(terms, list):
        return ["glossary_terms 必須是 list"]
    if banned_rows is not None and not isinstance(banned_rows, list):
        return ["banned_synonyms 必須是 list"]

    seen_terms: set[str] = set()
    for i, term in enumerate(terms or []):
        where = f"glossary_terms[{i}]"
        if not isinstance(term, dict):
            problems.append(f"{where} 必須是 mapping")
            continue
        name = term.get("term") or f"<第 {i} 個詞,沒有 term>"

        unknown = set(term) - GLOSSARY_KEYS
        if unknown:
            problems.append(
                f"{name}:未知的 key {sorted(unknown)};允許的是 {sorted(GLOSSARY_KEYS)}"
            )
        for required in ("term", "definition", "ddd_type", "provenance", "provenance_ref"):
            if not str(term.get(required) or "").strip():
                problems.append(f"{name}:缺 {required}")
        if name in seen_terms:
            problems.append(f"{name}:同一個詞出現兩次")
        seen_terms.add(name)

        # 對外欄位名:可空(= 這個詞不上線),但**填了就必須是一個欄位名**。
        wire_field = term.get("wire_field")
        if wire_field is not None and not WIRE_FIELD_RE.match(str(wire_field)):
            problems.append(
                f"{name}:wire_field {str(wire_field)[:24]!r} 不是一個欄位名 —— "
                "散文那一格常裝的是註記(括號說明 / 型態記號 / 指向別列的指標),"
                "而註記拿去跟合約比對**永遠不會中,而且是靜靜地不中**。"
                "要嘛給一個真的欄位名,要嘛留空 —— **留空有語意:這個詞不上線**"
            )

    if banned_rows and not terms:
        problems.append(
            "有 banned_synonyms 卻沒有 glossary_terms —— "
            "「一律改用」指回詞彙表,沒有詞彙表的話那一欄指不到任何東西"
        )

    seen_banned: set[str] = set()
    for i, row in enumerate(banned_rows or []):
        where = f"banned_synonyms[{i}]"
        if not isinstance(row, dict):
            problems.append(f"{where} 必須是 mapping")
            continue
        phrase = row.get("banned") or f"<第 {i} 列,沒有 banned>"

        unknown = set(row) - BANNED_SYNONYM_KEYS
        if unknown:
            problems.append(
                f"{phrase}:未知的 key {sorted(unknown)};"
                f"允許的是 {sorted(BANNED_SYNONYM_KEYS)}"
            )
        for required in ("banned", "note"):
            if not str(row.get(required) or "").strip():
                problems.append(f"{phrase}:缺 {required}")
        if phrase in seen_banned:
            problems.append(f"{phrase}:同一個講法被禁兩次")
        seen_banned.add(phrase)

        use_instead = str(row.get("use_instead") or "").strip()
        note = str(row.get("no_replacement_note") or "").strip()
        if use_instead and note:
            problems.append(
                f"{phrase}:既指了 use_instead 又寫了 no_replacement_note —— "
                "兩者只能有一個。有替代詞就指過去,沒有才寫理由"
            )
    return problems


def _check_wire_contract(spec: dict[str, Any]) -> list[str]:
    """wire shape 的宣告(ADR 0004)。

    有驗收情境就必須有合約 —— 沒有合約的話,生成器只能回去猜欄位名,
    而 2026-08-18 量到的就是「猜出來的名字跟實作全對不上,4 條全紅」。
    """
    problems: list[str] = []
    wire = spec.get("wire_contract")
    scenarios = spec.get("acceptance_scenarios") or []

    if not wire:
        if scenarios:
            problems.append(
                "有 acceptance_scenarios 就必須有 wire_contract —— "
                "wire shape 歸規格擁有(ADR 0004),生成器不再自己填欄位名"
            )
        return problems
    if not isinstance(wire, dict):
        return ["wire_contract 必須是 mapping"]

    unknown = set(wire) - set(WIRE_REQUIRED) - set(WIRE_OPTIONAL)
    if unknown:
        problems.append(f"wire_contract:未知的 key {sorted(unknown)}")
    for required in WIRE_REQUIRED:
        if not wire.get(required):
            problems.append(f"wire_contract:缺 {required}")

    list_fields = wire.get("list_fields")
    if not isinstance(list_fields, list) or not list_fields:
        problems.append("wire_contract:list_fields 必須是非空的 list(列表一列有哪些欄位)")
        list_fields = []

    # 列表的訂單識別欄一定要在 list_fields 裡 —— findInList 靠它比對。
    oid = wire.get("res_order_id_field")
    if oid and oid not in list_fields:
        problems.append(
            f"wire_contract:res_order_id_field {oid!r} 不在 list_fields 裡 —— "
            "列表沒有這一欄的話,findInList 認不出是哪一列"
        )
    cid = wire.get("res_customer_id_field")
    if cid and cid not in list_fields:
        problems.append(f"wire_contract:res_customer_id_field {cid!r} 不在 list_fields 裡")

    # 斷言引用的欄位要宣告過。schema 的 FK 也擋得住,但那時的訊息是
    # 「FOREIGN KEY constraint failed」—— 讀的人看不出是哪個欄位名打錯。
    for sc in scenarios:
        if not isinstance(sc, dict):
            continue
        for j, a in enumerate(sc.get("assertions") or []):
            if isinstance(a, dict) and a.get("field") and a["field"] not in list_fields:
                problems.append(
                    f"{sc.get('id')}.assertions[{j}]:斷言了欄位 {a['field']!r},"
                    f"但 wire_contract.list_fields 沒宣告它({sorted(list_fields)})"
                )
        # list_no_row_for_customer 需要列表揭露客人編號。有的合約不揭露它 ——
        # 那不是缺陷,是那份合約的事實,要講清楚。
        if sc.get("expects_rejection") and not cid:
            for a in sc.get("rejected_assertions") or []:
                if isinstance(a, dict) and a.get("kind") == "list_no_row_for_customer":
                    problems.append(
                        f"{sc.get('id')}:用了 list_no_row_for_customer,但這份 wire 合約"
                        "沒有 res_customer_id_field —— 列表不揭露客人編號就斷言不了這條"
                    )
                    break
    # 夾帶總金額(S3)要有欄位名才送得出去。沒宣告卻填了值的話,生成器會產出
    # `"None":5000` —— **import 過、Java 編得起來、跑起來測的是一個不存在的欄位**。
    # 這是「守衛靜靜失效」的另一個形狀,所以擋在這裡。
    if not wire.get("req_total_field"):
        for sc in scenarios:
            if not isinstance(sc, dict):
                continue
            carriers = (sc.get("steps") or []) + (sc.get("rejected_requests") or [])
            for c in carriers:
                if isinstance(c, dict) and c.get("claimed_total_cents") is not None:
                    problems.append(
                        f"{sc.get('id')}.{c.get('alias')}:填了 claimed_total_cents,"
                        "但 wire_contract 沒宣告 req_total_field —— "
                        "這份合約的請求沒有夾帶總金額的欄位,送不出去"
                    )

    # Σ(數量 × 單價) 那條不變式靠 res_total_field 認人。沒宣告 = 那條檢查不適用,
    # 而**不適用不會有人發現**。有斷言總額卻沒宣告欄位的話,講出來。
    if not wire.get("res_total_field"):
        for sc in scenarios:
            if not isinstance(sc, dict):
                continue
            if any(isinstance(a, dict) and a.get("kind") == "list_field_equals_number"
                   for a in (sc.get("assertions") or [])):
                problems.append(
                    f"{sc.get('id')}:斷言了列表上的數字欄位,但 wire_contract 沒宣告 "
                    "res_total_field —— 那樣「總額 = Σ(數量 × 單價)」那條不變式就不會被檢查"
                )
                break

    if spec.get("architecture_rules") and not scenarios:
        problems.append("wire_contract 只在有 acceptance_scenarios 時才有意義")
    return problems


def _check_scenarios(spec: dict[str, Any], wire: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    for i, sc in enumerate(spec.get("acceptance_scenarios") or []):
        sid = sc.get("id", f"<第 {i} 條情境,沒有 id>") if isinstance(sc, dict) else f"[{i}]"
        if not isinstance(sc, dict):
            problems.append(f"acceptance_scenarios[{i}] 必須是 mapping")
            continue
        for required in ("id", "given_when", "then_expect", "provenance", "provenance_ref"):
            if not sc.get(required):
                problems.append(f"{sid}:缺 {required}")

        # 負面情境走另一組欄位(ADR 0003):rejected_requests / rejected_assertions。
        # 兩組**不得混用** —— 混用表示作者沒想清楚這個情境預期成功還是預期被拒。
        if sc.get("expects_rejection"):
            problems += _check_rejection_scenario(sid, sc)
            continue

        for key in ("rejected_requests", "rejected_assertions"):
            if sc.get(key):
                problems.append(
                    f"{sid}:有 {key} 卻沒有 expects_rejection: true —— "
                    "違法的 fixture 只掛得上預期被拒的情境"
                )

        steps = sc.get("steps")
        if not isinstance(steps, list) or not steps:
            problems.append(f"{sid}:steps 必須是非空的 list")
            steps = []
        aliases: dict[str, int] = {}
        for step in steps:
            if not isinstance(step, dict) or not step.get("alias"):
                problems.append(f"{sid}:每個 step 都要有 alias")
                continue
            if not step.get("customer_id"):
                problems.append(f"{sid}.{step['alias']}:缺 customer_id")
            items = step.get("items")
            if not isinstance(items, list) or not items:
                problems.append(f"{sid}.{step['alias']}:items 必須是非空的 list")
                items = []
            total = 0
            for item in items:
                if not isinstance(item, dict):
                    problems.append(f"{sid}.{step['alias']}:item 必須是 mapping")
                    continue
                missing = [k for k in
                           ("product_id", "quantity", "unit_price_cents", "currency")
                           if item.get(k) is None]
                if missing:
                    problems.append(f"{sid}.{step['alias']}:item 缺 {missing}")
                else:
                    total += int(item["quantity"]) * int(item["unit_price_cents"])
            aliases[step["alias"]] = total
            # 夾帶的總金額若剛好等於算出來的,這個情境**證明不了任何事** ——
            # 「被忽略」與「被採用」在結果上完全一樣。這是規格層假驗收的一種,
            # 而且是這次寫測試資料時自己撞出來的。
            claimed = step.get("claimed_total_cents")
            if claimed is not None and int(claimed) == total:
                problems.append(
                    f"{sid}.{step['alias']}:夾帶的總金額 {claimed} 等於各明細算出來的 "
                    f"{total} —— 這樣「指定值被忽略」與「被採用」的結果一樣,斷言不了"
                )

        for j, a in enumerate(sc.get("assertions") or []):
            where = f"{sid}.assertions[{j}]"
            if not isinstance(a, dict):
                problems.append(f"{where} 必須是 mapping")
                continue
            kind = a.get("kind")
            if kind not in ASSERTION_KINDS:
                problems.append(f"{where}:kind 只能是 {sorted(ASSERTION_KINDS)},拿到 {kind!r}")
                continue
            if a.get("target") not in aliases:
                problems.append(
                    f"{where}:target {a.get('target')!r} 不是這個情境的 alias "
                    f"({sorted(aliases)})"
                )
            needed = ASSERTION_KINDS[kind]
            supplied = {k for k in ("field", "expected_text", "expected_number") if k in a}
            if supplied != needed:
                problems.append(
                    f"{where}:kind={kind} 該帶 {sorted(needed) or '(無參數)'},"
                    f"實際帶了 {sorted(supplied) or '(無)'}"
                )
            # ⚠️ 推導型矛盾的機械檢查:總額必須等於各明細的乘加。
            #    散文裡寫錯一個數字沒人擋得住(讀的人得自己心算);這裡寫錯就匯不進去。
            # ⚠️ 認人方式跟著合約走,不寫死欄位名。寫死的話,規格只要取了別的名字,
            #    這條就靜靜地永遠不再檢查。
            total_field = wire.get("res_total_field")
            if (kind == "list_field_equals_number" and total_field
                    and a.get("field") == total_field
                    and a.get("target") in aliases and a.get("expected_number") is not None):
                expected, computed = int(a["expected_number"]), aliases[a["target"]]
                if expected != computed:
                    problems.append(
                        f"{where}:{total_field} 期望 {expected},但各明細的「數量 × 單價」"
                        f"加總是 {computed} —— 兩者不一致"
                    )
        # 有查列表欄位、卻沒先確認那一列存在 → 失敗時會 NPE,而不是一句清楚的
        # 「列表中找不到訂單 X」。行為上一樣紅,但訊息品質差一截,而 agent 讀不到
        # 那個差別 —— 它的完成定義是「import 印 ok」,所以要在這裡講。
        # (2026-08-18 第二幕實跑觀察:agent 交的 S3/S4/S5 都少了這個守衛。)
        needs_row = {
            a["target"] for a in (sc.get("assertions") or [])
            if isinstance(a, dict) and str(a.get("kind", "")).startswith("list_field_")
        }
        has_row_check = {
            a["target"] for a in (sc.get("assertions") or [])
            if isinstance(a, dict) and a.get("kind") == "list_row_exists"
        }
        for alias in sorted(needs_row - has_row_check):
            problems.append(
                f"{sid}:對 {alias} 查了列表欄位,卻沒有先 list_row_exists —— "
                "那一列不存在時會 NPE,而不是一句看得懂的失敗訊息"
            )

        if not sc.get("assertions"):
            problems.append(f"{sid}:assertions 必須是非空的 list")

    problems += _check_rejection_customers_are_exclusive(spec)
    return problems


# 負面情境的斷言 kind ↔ 該帶哪些參數(對應 schema 的 rejected_assertion CHECK)
REJECTED_ASSERTION_KINDS: dict[str, set[str]] = {
    "status_is": {"expected_number"},
    "list_no_row_for_customer": set(),
}


def _check_rejection_scenario(sid: str, sc: dict[str, Any]) -> list[str]:
    """預期被拒的情境(ADR 0003)。

    這裡**刻意不檢查** fixture 的合法性 —— 數量 0、空明細、空的 customer_id
    全都是合法的輸入,因為那正是這種情境要送出去的東西。schema 那邊也拿掉了
    對應的 CHECK。要擋的是別的:形狀、目標、以及斷言有沒有涵蓋到「沒有殘骸」。
    """
    problems: list[str] = []
    for key in ("steps", "assertions"):
        if sc.get(key):
            problems.append(
                f"{sid}:expects_rejection 的情境不得有 {key} —— "
                f"請用 rejected_requests / rejected_assertions"
            )

    requests = sc.get("rejected_requests")
    if not isinstance(requests, list) or not requests:
        problems.append(f"{sid}:rejected_requests 必須是非空的 list")
        requests = []

    aliases: set[str] = set()
    for req in requests:
        if not isinstance(req, dict) or not req.get("alias"):
            problems.append(f"{sid}:每個 rejected_request 都要有 alias")
            continue
        if "customer_id" not in req:
            # 空字串是合法的(S7 未登入),但「整個欄位沒寫」是漏了。
            problems.append(f"{sid}.{req['alias']}:缺 customer_id(要送空的請寫 \"\")")
        aliases.add(req["alias"])
        for item in req.get("items") or []:   # 允許沒有 items —— S4 空單就是這樣表達的
            if not isinstance(item, dict):
                problems.append(f"{sid}.{req['alias']}:item 必須是 mapping")
                continue
            missing = [k for k in
                       ("product_id", "quantity", "unit_price_cents", "currency")
                       if item.get(k) is None]
            if missing:
                problems.append(f"{sid}.{req['alias']}:item 缺 {missing}")

    assertions = sc.get("rejected_assertions")
    if not isinstance(assertions, list) or not assertions:
        problems.append(f"{sid}:rejected_assertions 必須是非空的 list")
        assertions = []

    kinds_by_target: dict[str, set[str]] = {}
    for j, a in enumerate(assertions):
        where = f"{sid}.rejected_assertions[{j}]"
        if not isinstance(a, dict):
            problems.append(f"{where} 必須是 mapping")
            continue
        kind = a.get("kind")
        if kind not in REJECTED_ASSERTION_KINDS:
            problems.append(
                f"{where}:kind 只能是 {sorted(REJECTED_ASSERTION_KINDS)},拿到 {kind!r}"
            )
            continue
        if a.get("target") not in aliases:
            problems.append(
                f"{where}:target {a.get('target')!r} 不是這個情境的 alias ({sorted(aliases)})"
            )
        supplied = {k for k in ("expected_number",) if k in a}
        if supplied != REJECTED_ASSERTION_KINDS[kind]:
            problems.append(
                f"{where}:kind={kind} 該帶 {sorted(REJECTED_ASSERTION_KINDS[kind]) or '(無參數)'},"
                f"實際帶了 {sorted(supplied) or '(無)'}"
            )
        kinds_by_target.setdefault(a.get("target"), set()).add(kind)

    # 只斷言 400 的話,「**回了 400 但還是寫了一筆**」會通過 —— 而那正是這條規則
    # 存在要擋的失效。S4/S5/S6 的 Then 明文是兩半:「系統拒絕」**加上**
    # 「不產生任何訂單紀錄」。少掉後半,這條驗收就只測了 HTTP 狀態碼。
    for alias in sorted(aliases):
        kinds = kinds_by_target.get(alias, set())
        if "status_is" not in kinds:
            problems.append(f"{sid}.{alias}:缺 status_is —— 沒斷言請求被拒")
        if "list_no_row_for_customer" not in kinds:
            problems.append(
                f"{sid}.{alias}:缺 list_no_row_for_customer —— "
                "只斷言狀態碼的話,「回了 400 但還是寫了一筆」會通過"
            )
    return problems


def _check_rejection_customers_are_exclusive(spec: dict[str, Any]) -> list[str]:
    """拒絕情境用到的客人編號,不得出現在任何預期成功的情境。

    ⚠️ **這條不補,`list_no_row_for_customer` 會是空的。** 生成的驗收共用一個
    Spring context、一個資料庫,而且**不做 per-test 重置**(`@SpringBootTest`
    RANDOM_PORT,沒有 @DirtiesContext / @Transactional)—— 訂單會跨情境累積。
    所以「列表裡沒有屬於 C-004 的列」只有在 C-004 不曾被任何成功情境建立時才成立;
    否則這條斷言會被別的情境建的列弄成假紅,而且**情境順序一換就時紅時綠**。

    這是「規格層假驗收」的同一個家族(見 CONTEXT.md「代理編碼」),
    差別是這次在做之前就看到了,所以擋在 import。
    """
    scenarios = [s for s in (spec.get("acceptance_scenarios") or []) if isinstance(s, dict)]
    success_customers: dict[str, str] = {}
    for sc in scenarios:
        if sc.get("expects_rejection"):
            continue
        for step in sc.get("steps") or []:
            if isinstance(step, dict) and step.get("customer_id"):
                success_customers.setdefault(str(step["customer_id"]), str(sc.get("id")))

    problems: list[str] = []
    for sc in scenarios:
        if not sc.get("expects_rejection"):
            continue
        for req in sc.get("rejected_requests") or []:
            if not isinstance(req, dict):
                continue
            cid = str(req.get("customer_id") or "")
            if cid and cid in success_customers:
                problems.append(
                    f"{sc.get('id')}.{req.get('alias')}:客人 {cid} 也出現在預期成功的情境 "
                    f"{success_customers[cid]} —— list_no_row_for_customer 會被那一列弄成假紅。"
                    f"拒絕情境要用專屬的客人編號"
                )
    return problems


def build_store(db_path: str | Path, spec: dict[str, Any]) -> None:
    """建 store。任何一條掛掉就整個不寫 —— 部分匯入比匯入失敗更難查。"""
    problems = _check_shape(spec)
    if problems:
        raise SpecError(problems)

    db_path = Path(db_path)
    if db_path.exists():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.execute("PRAGMA foreign_keys = ON")

        wire = spec.get("wire_contract")
        if wire:
            for field in wire["list_fields"]:
                conn.execute("INSERT INTO wire_list_field (field) VALUES (?)", (field,))
            conn.execute(
                "INSERT INTO wire_contract (id, name, req_customer_field, req_items_field, "
                "req_product_field, req_quantity_field, req_price_field, req_currency_field, "
                "req_total_field, res_order_id_field, res_customer_id_field, res_total_field) "
                "VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (wire["name"], wire["req_customer_field"], wire["req_items_field"],
                 wire["req_product_field"], wire["req_quantity_field"],
                 wire["req_price_field"], wire["req_currency_field"],
                 wire.get("req_total_field"), wire["res_order_id_field"],
                 wire.get("res_customer_id_field"), wire.get("res_total_field")),
            )

        # 詞彙表放在 authorized_template 之後 —— glossary_term 的「模板既定」trigger
        # 要查那張白名單;禁用同義詞的 FK 又指 glossary_term,所以是三段的順序。
        for seq, term in enumerate(spec.get("glossary_terms") or []):
            conn.execute(
                "INSERT INTO glossary_term "
                "(term, definition, ddd_type, representation, wire_field, "
                " provenance, provenance_ref, seq) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    term["term"],
                    term["definition"],
                    term["ddd_type"],
                    term.get("representation"),
                    term.get("wire_field"),
                    term["provenance"],
                    term["provenance_ref"],
                    seq,
                ),
            )
        for seq, row in enumerate(spec.get("banned_synonyms") or []):
            conn.execute(
                "INSERT INTO glossary_banned_synonym "
                "(banned, use_instead, no_replacement_note, note, seq) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    row["banned"],
                    row.get("use_instead"),
                    row.get("no_replacement_note"),
                    row["note"],
                    seq,
                ),
            )

        for doc in spec.get("authorized_templates") or []:
            conn.execute("INSERT INTO authorized_template (document) VALUES (?)", (doc,))

        for rule in spec.get("architecture_rules") or []:
            conn.execute(
                "INSERT INTO architecture_rule "
                "(id, rule, provenance, provenance_ref, enforcement, ladder_note) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    rule["id"],
                    rule["rule"],
                    rule["provenance"],
                    rule["provenance_ref"],
                    rule["enforcement"],
                    rule.get("ladder_note"),
                ),
            )
            shape = KINDS.get(rule["enforcement"])
            if shape:
                params = rule[shape["param"]]
                columns = ["rule_id", *shape["scalars"].values(), shape["value_column"], "seq"]
                placeholders = ", ".join("?" * len(columns))
                for seq, value in enumerate(params[shape["list_key"]]):
                    conn.execute(
                        # 表名與欄位名都來自本檔的 KINDS 常數,不是外來輸入
                        f"INSERT INTO {shape['table']} ({', '.join(columns)}) "  # noqa: S608
                        f"VALUES ({placeholders})",
                        (
                            rule["id"],
                            *(params[k] for k in shape["scalars"]),
                            value,
                            seq,
                        ),
                    )
        for sc in spec.get("acceptance_scenarios") or []:
            rejects = bool(sc.get("expects_rejection"))
            conn.execute(
                "INSERT INTO acceptance_scenario "
                "(id, given_when, then_expect, provenance, provenance_ref, "
                " expects_rejection, proxy_for) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (sc["id"], sc["given_when"], sc["then_expect"],
                 sc["provenance"], sc["provenance_ref"],
                 1 if rejects else 0, sc.get("proxy_for")),
            )
            if rejects:
                for r_seq, req in enumerate(sc["rejected_requests"]):
                    conn.execute(
                        "INSERT INTO rejected_request (scenario_id, expects_rejection, "
                        "alias, seq, customer_id, claimed_total_cents) "
                        "VALUES (?, 1, ?, ?, ?, ?)",
                        (sc["id"], req["alias"], r_seq, req.get("customer_id", ""),
                         req.get("claimed_total_cents")),
                    )
                    for i_seq, item in enumerate(req.get("items") or []):
                        conn.execute(
                            "INSERT INTO rejected_request_item (scenario_id, alias, seq, "
                            "product_id, quantity, unit_price_cents, currency) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (sc["id"], req["alias"], i_seq, item["product_id"],
                             item["quantity"], item["unit_price_cents"], item["currency"]),
                        )
                for a_seq, a in enumerate(sc["rejected_assertions"]):
                    conn.execute(
                        "INSERT INTO rejected_assertion (scenario_id, seq, kind, "
                        "target_alias, expected_number) VALUES (?, ?, ?, ?, ?)",
                        (sc["id"], a_seq, a["kind"], a["target"], a.get("expected_number")),
                    )
                continue
            for s_seq, step in enumerate(sc["steps"]):
                conn.execute(
                    "INSERT INTO scenario_step (scenario_id, alias, seq, customer_id, "
                    "claimed_total_cents) VALUES (?, ?, ?, ?, ?)",
                    (sc["id"], step["alias"], s_seq, step["customer_id"],
                     step.get("claimed_total_cents")),
                )
                for i_seq, item in enumerate(step["items"]):
                    conn.execute(
                        "INSERT INTO step_item (scenario_id, alias, seq, product_id, "
                        "quantity, unit_price_cents, currency) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (sc["id"], step["alias"], i_seq, item["product_id"],
                         item["quantity"], item["unit_price_cents"], item["currency"]),
                    )
            for a_seq, a in enumerate(sc["assertions"]):
                conn.execute(
                    "INSERT INTO scenario_assertion (scenario_id, seq, kind, target_alias, "
                    "field, expected_text, expected_number) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (sc["id"], a_seq, a["kind"], a["target"],
                     a.get("field"), a.get("expected_text"), a.get("expected_number")),
                )

        # 契約放在最後 —— contract_named_test 的 FK 指 acceptance_scenario,
        # 情境要先在裡面。
        for contract in spec.get("domain_contracts") or []:
            conn.execute(
                "INSERT INTO domain_contract "
                "(id, kind, statement, provenance, provenance_ref, guarded_in, "
                " crosses_aggregate, disposition, enforcement, ladder_note, "
                " no_named_test_reason) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    contract["id"],
                    contract["kind"],
                    contract["statement"],
                    contract["provenance"],
                    contract["provenance_ref"],
                    contract["guarded_in"],
                    1 if contract.get("crosses_aggregate") else 0,
                    contract.get("disposition"),
                    contract["enforcement"],
                    contract.get("ladder_note"),
                    contract.get("no_named_test_reason"),
                ),
            )
            for seq, scenario_id in enumerate(contract.get("named_tests") or []):
                conn.execute(
                    "INSERT INTO contract_named_test "
                    "(contract_id, scenario_id, seq) VALUES (?, ?, ?)",
                    (contract["id"], scenario_id, seq),
                )

        conn.commit()
    except sqlite3.IntegrityError as exc:
        # rollback 只救得回 insert;DDL 是 executescript 自動 commit 的,
        # 所以檔案還在、schema 還在、只是一條規則都沒有。那個半成品會騙人
        # ——「spec.db 出現了」不能等於「匯入成功」。整個刪掉。
        conn.rollback()
        conn.close()
        db_path.unlink(missing_ok=True)
        raise SpecError([f"schema 擋下來了:{exc}"]) from exc
    except Exception:
        conn.close()
        db_path.unlink(missing_ok=True)
        raise
    finally:
        try:
            conn.close()
        except sqlite3.ProgrammingError:
            pass  # 已在錯誤路徑關過


def main(argv: list[str]) -> int:
    if len(argv) < 4 or argv[1] != "import":
        print(__doc__, file=sys.stderr)
        return 2
    *specs, db = argv[2:]
    try:
        build_store(db, load_specs(specs))
    except SpecError as exc:
        print("spec 未通過驗證,一條都沒有寫入:", file=sys.stderr)
        for problem in exc.problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    print(f"ok: {', '.join(specs)} → {db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
