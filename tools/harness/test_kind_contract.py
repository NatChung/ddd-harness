#!/usr/bin/env python3
"""「kind ↔ 該帶哪些參數」寫了兩次 —— 這份測試綁住那兩份。

`spec_store.ASSERTION_KINDS` / `REJECTED_ASSERTION_KINDS`(第 2 階,python dict)
與 `schema.sql` 的條件式 CHECK(第 1 階,SQL)**是同一條規則的兩個載體**。
在這份測試之前,沒有任何東西綁住它們,而漂掉的兩個方向都很難查:

* **python 放寬、schema 沒跟上** → 第 2 階放行、第 1 階 abort,
  agent 拿到的是一句 `CHECK constraint failed`,而不是「你少給了 expected_text」。
* **schema 放寬、python 沒跟上** → 第 2 階擋住一個其實合法的東西,
  agent 卡在一個它改不掉的錯誤裡。

**做法是行為比對,不是文字比對**:每一種 kind 都真的 INSERT 一次 ——
剛好給對的參數要進得去,少給一個或多給一個都要被 schema 擋下來。
文字比對只證明兩邊長得像,行為比對才證明兩邊擋的是同一件事。

外加一條反向的文字檢查:schema 的 `kind IN (...)` 清單不得出現 python 不認得的
kind —— 那個方向 INSERT 測不到(python 不知道它存在,就不會去試)。
"""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import spec_store  # noqa: E402

SCHEMA = Path(__file__).parent / "schema.sql"

# 斷言表上,除了 kind 之外可能出現的參數欄。python dict 的 value 就是從這裡取子集。
PARAM_COLUMNS = ("field", "expected_text", "expected_number")

# 各參數欄的合法測試值。`field` 要對得上 wire_list_field 的 FK。
PARAM_VALUE = {"field": "'status'", "expected_text": "'x'", "expected_number": "201"}


def fresh_db() -> sqlite3.Connection:
    """建一個開著 FK、備妥最小 fixture 的 in-memory store。

    ⚠️ `PRAGMA foreign_keys = ON` 不能省 —— SQLite 預設不檢查外鍵,
    少這行整組 FK 守衛會靜靜失效,而這份測試會全綠。
    """
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("INSERT INTO wire_list_field (field) VALUES ('status')")
    conn.execute(
        "INSERT INTO acceptance_scenario (id, given_when, then_expect, provenance, "
        "provenance_ref, expects_rejection) VALUES ('OK','g','t','Qn','ref',0)")
    conn.execute(
        "INSERT INTO scenario_step (scenario_id, alias, seq, customer_id) "
        "VALUES ('OK','okStep',0,'C-1')")
    conn.execute(
        "INSERT INTO acceptance_scenario (id, given_when, then_expect, provenance, "
        "provenance_ref, expects_rejection) VALUES ('NO','g','t','Qn','ref',1)")
    conn.execute(
        "INSERT INTO rejected_request (scenario_id, expects_rejection, alias, seq, "
        "customer_id) VALUES ('NO',1,'noReq',0,'C-2')")
    return conn


def insert(conn: sqlite3.Connection, table: str, scenario: str, alias: str,
           seq: int, kind: str, params: set[str]) -> None:
    cols = ["scenario_id", "seq", "kind", "target_alias", *sorted(params)]
    vals = [f"'{scenario}'", str(seq), f"'{kind}'", f"'{alias}'",
            *(PARAM_VALUE[p] for p in sorted(params))]
    conn.execute(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(vals)})")


CASES = [
    ("scenario_assertion", spec_store.ASSERTION_KINDS, "OK", "okStep", PARAM_COLUMNS),
    ("rejected_assertion", spec_store.REJECTED_ASSERTION_KINDS, "NO", "noReq",
     ("expected_number",)),
]


@pytest.mark.parametrize("table,kinds,scenario,alias,columns", CASES)
def test_剛好給對的參數_schema_要收(table, kinds, scenario, alias, columns) -> None:
    """python 說某個 kind 該帶哪些參數,照著給,schema 就必須收。

    這一半同時證明了:python 認得的每一種 kind,schema 的 `kind IN (...)` 都有。
    """
    conn = fresh_db()
    for seq, (kind, needed) in enumerate(sorted(kinds.items())):
        insert(conn, table, scenario, alias, seq, kind, needed)
    assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == len(kinds)


@pytest.mark.parametrize("table,kinds,scenario,alias,columns", CASES)
def test_少給一個參數_schema_要擋(table, kinds, scenario, alias, columns) -> None:
    conn = fresh_db()
    checked = 0
    for kind, needed in sorted(kinds.items()):
        for dropped in sorted(needed):
            with pytest.raises(sqlite3.IntegrityError):
                insert(conn, table, scenario, alias, 0, kind, needed - {dropped})
            checked += 1
    assert checked > 0, "沒有任何 kind 帶必填參數 —— 這條測試等於沒跑"


@pytest.mark.parametrize("table,kinds,scenario,alias,columns", CASES)
def test_多給一個參數_schema_要擋(table, kinds, scenario, alias, columns) -> None:
    """多給也要擋。`!=` 不是「有沒有包含」——
    `order_id_not_blank` 硬塞一個 expected_number 進去必須紅。"""
    conn = fresh_db()
    checked = 0
    for kind, needed in sorted(kinds.items()):
        for extra in (set(columns) - needed):
            with pytest.raises(sqlite3.IntegrityError):
                insert(conn, table, scenario, alias, 0, kind, needed | {extra})
            checked += 1
    assert checked > 0, "沒有任何多給的組合 —— 這條測試等於沒跑"


def schema_kinds(table: str) -> set[str]:
    """從 schema.sql 撈某張表的 `kind IN (...)` 清單。

    只在這一條反向檢查用文字比對 —— 因為「schema 有、python 沒有」的 kind,
    INSERT 測不到:python 不知道它存在,就不會去試著插它。
    """
    block = re.search(rf"CREATE TABLE {table} \((.*?)\n\);", SCHEMA.read_text(encoding="utf-8"),
                      re.S)
    assert block, f"schema.sql 找不到 {table}"
    body = re.sub(r"--[^\n]*", "", block.group(1))       # 去掉註解,免得撈到裡面的字串
    listing = re.search(r"kind\s+TEXT NOT NULL CHECK \(kind IN \((.*?)\)\)", body, re.S)
    assert listing, f"{table} 找不到 kind 的 CHECK IN 清單"
    return set(re.findall(r"'([^']+)'", listing.group(1)))


@pytest.mark.parametrize("table,kinds", [
    ("scenario_assertion", spec_store.ASSERTION_KINDS),
    ("rejected_assertion", spec_store.REJECTED_ASSERTION_KINDS),
])
def test_schema_沒有_python_不認得的_kind(table, kinds) -> None:
    """反向:schema 放寬了而 python 沒跟上,agent 會卡在一個它改不掉的錯誤裡。"""
    assert schema_kinds(table) == set(kinds), (
        f"{table} 的 kind 清單漂了:schema={sorted(schema_kinds(table))} "
        f"vs spec_store={sorted(kinds)}"
    )
