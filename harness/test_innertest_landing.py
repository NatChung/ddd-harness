#!/usr/bin/env python3
"""`innertest_landing_check` 的測試(票 13)—— tmp dir 合成三態,外加對真實 run 的一條。

預測寫在 `.scratch/ddd-harness/13-PREDICTION.md`(P1、P4),**commit 在寫程式之前**
(`02ac617`)。釘的重點是三條容易被折掉的邊:

- 沒有 `src/innerTest/` 是 **3 不適用**;**目錄在但零個檔 / 零個 `@covers` 是 1**,不折成 3 ——
  `run_act4.sh` 自己會 mkdir 那層,「空的」正是 agent 什麼都沒寫的長相;
- 舊約定(方法名帶編號)**不算落點**,只計數;
- 情境不進判定(它們的落點在外圈生成的驗收),但 `@covers G16` 是合法宣告、反向段照查。

store 用 `schema.sql` 直接 INSERT 最小列(不走 `spec_store` 的驗證 —— 這支測的是落點,
不是匯入;考卷那邊走的才是完整的 import 路徑)。
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import innertest_landing_check as ilc  # noqa: E402

HERE = Path(__file__).parent
SCHEMA = HERE / "schema.sql"
CORPUS = HERE.parent.parent / "examples" / "shop" / "harness" / "runs" / "2026-08-19-act4"
CORPUS_SPEC = HERE.parent.parent / "examples" / "shop" / "harness" / "runs" / "2026-08-19-act2"


# ── fixtures ─────────────────────────────────────────────────────────────

def make_store(path: Path, contracts: list[str], scenarios: list[str] = ()) -> Path:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    for cid in contracts:
        conn.execute(
            "INSERT INTO domain_contract (id, kind, statement, provenance, provenance_ref, "
            "guarded_in, enforcement, ladder_note) VALUES (?, 'invariant', 's', 'Qn', '[Q1]', "
            "'訂單', 'none', 'n')",
            (cid,),
        )
    for sid in scenarios:
        conn.execute(
            "INSERT INTO acceptance_scenario (id, given_when, then_expect, provenance, provenance_ref) "
            "VALUES (?, 'g', 't', 'Qn', '[Q1]')",
            (sid,),
        )
    conn.commit()
    conn.close()
    return path


def java(work: Path, name: str, header: str, body: str = "") -> Path:
    p = work / "src" / "innerTest" / "java" / "com" / "shop" / f"{name}.java"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        "package com.shop;\n\nimport org.junit.jupiter.api.Test;\n\n"
        f"{header}\n@DisplayName(\"x\")\nclass {name} {{\n{body}\n}}\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def store(tmp_path: Path) -> Path:
    return make_store(tmp_path / "spec.db", ["C1", "C2", "C10"], ["G1", "G16"])


@pytest.fixture
def work(tmp_path: Path) -> Path:
    w = tmp_path / "work"
    (w / "src" / "innerTest" / "java").mkdir(parents=True)   # run_act4.sh 會 mkdir 這層
    return w


def run(store: Path, work: Path, capsys) -> tuple[int, str]:
    rc = ilc.main(["innertest_landing_check.py", str(store), str(work)])
    return rc, capsys.readouterr().out


# ── 三態 ─────────────────────────────────────────────────────────────────

def test_沒有innerTest目錄是不適用3(store: Path, tmp_path: Path, capsys) -> None:
    w = tmp_path / "bare"
    w.mkdir()
    rc, out = run(store, w, capsys)
    assert rc == 3
    assert "整份不適用(不是通過)" in out
    assert "--- 第一段" not in out   # 不適用就不印落點段(上限段會提到「無落點」這個詞,不算)


def test_store零契約零情境是不適用3(tmp_path: Path, work: Path, capsys) -> None:
    empty = make_store(tmp_path / "empty.db", [], [])
    java(work, "AnyTest", "/** @covers C1 */")
    rc, out = run(empty, work, capsys)
    assert rc == 3
    assert "契約 0 條、情境 0 條" in out


def test_目錄在但零個java是漏1不是不適用(store: Path, work: Path, capsys) -> None:
    rc, out = run(store, work, capsys)
    assert rc == 1
    assert "零個 .java" in out
    assert "無落點 3 條:C1、C2、C10" in out
    assert "整份不適用" not in out


def test_有檔但零covers每條無落點1(store: Path, work: Path, capsys) -> None:
    """舊約定:方法名帶編號、javadoc 是散文 —— 不算落點,只計數。"""
    java(work, "MoneyTest", "/**\n * 內圈測試 —— 契約 C1(invariant)。\n */",
         "    @Test\n    void C1_金額不可為負() {}\n")
    rc, out = run(store, work, capsys)
    assert rc == 1
    assert "檔頭帶 `@covers` 的 0 支" in out
    assert "舊約定方法名帶編號 1 條(不算落點)" in out
    assert "❌ C1(invariant)" in out and "無落點 3 條" in out
    assert "沒有任何宣告,所以沒有東西可以漂" in out


def test_每條契約都有covers是0(store: Path, work: Path, capsys) -> None:
    java(work, "ATest", "/**\n * 守 C1、C2。\n * @covers C1, C2\n */")
    java(work, "BTest", "/** @covers C10 */")
    rc, out = run(store, work, capsys)
    assert rc == 0
    assert "有落點 3 / 3;無落點 0 條:(無)" in out
    assert "✅ C1(invariant)守在:訂單 —— src/innerTest/java/com/shop/ATest.java" in out
    assert "(全部存在)" in out


def test_一檔多條兩條都算落點(store: Path, work: Path, capsys) -> None:
    java(work, "ATest", "/** @covers C1 C2 C10 */")
    rc, out = run(store, work, capsys)
    assert rc == 0
    for cid in ("C1", "C2", "C10"):
        assert f"✅ {cid}(invariant)" in out


# ── 反向:漂 ─────────────────────────────────────────────────────────────

def test_指到store沒有的編號是漂1(store: Path, work: Path, capsys) -> None:
    java(work, "ATest", "/** @covers C1, C2, C10, C99 */")
    rc, out = run(store, work, capsys)
    assert rc == 1
    assert "❌ `C99` ← src/innerTest/java/com/shop/ATest.java —— store 裡沒有這個編號" in out
    assert "有落點 3 / 3" in out   # 落點那半照樣過;離開碼是被反向段拉成 1 的


def test_認不出來的寫法列進反向段(store: Path, work: Path, capsys) -> None:
    java(work, "ATest", "/** @covers 契約一, C2, C10 */")
    java(work, "BTest", "/** @covers C1 */")
    rc, out = run(store, work, capsys)
    assert rc == 1
    assert "`契約一` ← src/innerTest/java/com/shop/ATest.java —— `@covers` 後面認不出來的寫法" in out


def test_方法javadoc裡的covers位置不對不算落點(store: Path, work: Path, capsys) -> None:
    java(work, "ATest", "/** 檔頭沒宣告 */",
         "    /** @covers C1 */\n    @Test\n    void x() {}\n")
    java(work, "BTest", "/** @covers C2, C10 */")
    rc, out = run(store, work, capsys)
    assert rc == 1
    assert "❌ C1(invariant)" in out
    assert "`@covers` 不在 class 的 javadoc 裡" in out


# ── 情境:只印參考,反向段照查 ─────────────────────────────────────────────

def test_情境沒宣告不影響離開碼但反向段查得到(store: Path, work: Path, capsys) -> None:
    java(work, "ATest", "/** @covers C1, C2, C10, G16 */")
    rc, out = run(store, work, capsys)
    assert rc == 0
    assert "· G1 —— (內圈沒宣告)" in out
    assert "· G16 —— src/innerTest/java/com/shop/ATest.java" in out


def test_情境編號不寫死前綴(tmp_path: Path, work: Path, capsys) -> None:
    """2026-08-19 那份 store 的情境是 G,不是票裡舉例的 S —— 從 store 讀,S / G 都行。"""
    s = make_store(tmp_path / "s.db", ["C1"], ["S3"])
    java(work, "ATest", "/** @covers C1, S3 */")
    rc, out = run(s, work, capsys)
    assert rc == 0
    assert "· S3 —— src/innerTest/java/com/shop/ATest.java" in out


# ── 第三段:打在哪個入口(第 4 階,人讀) ────────────────────────────────

def test_第三段列出三種token且標第4階(store: Path, work: Path, capsys) -> None:
    java(work, "ATest", "/** @covers C1, C2, C10 */",
         "    @Test void x() {\n"
         "        Order o = Order.place(OrderId.of(\"x\"), new CustomerName(\"n\"));\n"
         "        for (var m : Order.class.getDeclaredMethods()) {}\n"
         "        // Money.twd(1) 在註解裡,不算\n"
         "        String s = \"Sku.of(\";\n"
         "    }\n")
    rc, out = run(store, work, capsys)
    assert rc == 0
    assert "第 4 階,人讀" in out
    assert "Type.method(:Order.place、OrderId.of" in out
    assert "new Type(   :CustomerName" in out
    assert "Type.class  :Order" in out
    assert "Money" not in out.split("--- 第三段")[1].split("--- 副")[0]
    assert "Sku" not in out.split("--- 第三段")[1].split("--- 副")[0]


def test_常數不當型別(store: Path, work: Path, capsys) -> None:
    java(work, "ATest", "/** @covers C1, C2, C10 */",
         "    private static final String THE_ONLY = \"changeStatusTo\";\n"
         "    @Test void x() { THE_ONLY.equals(\"x\"); }\n")
    _, out = run(store, work, capsys)
    assert "THE_ONLY" not in out.split("--- 第三段")[1]


# ── 上限與副 ─────────────────────────────────────────────────────────────

def test_上限與第三類提醒印在報表裡(store: Path, work: Path, capsys) -> None:
    java(work, "ATest", "/** @covers C1, C2, C10 */")
    _, out = run(store, work, capsys)
    assert "`@covers` 是一條約定" in out
    assert "第三類「範圍不足」**兩支都抓不到**" in out
    assert "vacuous_tests.py" in out
    assert "!isStatic" in out          # 陽性一點名
    assert "沒試 `null`" in out        # 陽性二點名


# ── 用法錯誤 ─────────────────────────────────────────────────────────────

def test_吃錯目錄是2不是3(store: Path, tmp_path: Path, capsys) -> None:
    assert ilc.main(["x", str(store), str(tmp_path / "nowhere")]) == 2
    assert ilc.main(["x", str(tmp_path / "no.db"), str(tmp_path)]) == 2
    assert ilc.main(["x"]) == 2


# ── 真實 run:P1 ─────────────────────────────────────────────────────────

@pytest.mark.skipif(not (CORPUS / "src" / "innerTest").is_dir(), reason="語料不在")
def test_P1_對2026_08_19_act4跑整份無落點(tmp_path: Path, capsys) -> None:
    """13-PREDICTION P1:舊約定、沒 `@covers` → 1,契約 17/17 無落點,舊約定 9 條,
    `OrderImmutabilityTest` 那格列得出 `Order.class`(陽性一的向量)。"""
    pytest.importorskip("yaml")
    from spec_store import build_store, load_specs
    db = tmp_path / "spec.db"
    build_store(db, load_specs([CORPUS_SPEC / "contracts.yaml", CORPUS_SPEC / "acceptance.yaml",
                                CORPUS_SPEC / "glossary.yaml"]))
    rc, out = run(db, CORPUS, capsys)
    assert rc == 1
    assert "store:契約 17 條、情境 5 條;內圈測試檔 6 支,其中檔頭帶 `@covers` 的 0 支;" \
           "舊約定方法名帶編號 9 條(不算落點)。" in out
    assert "有落點 0 / 17;無落點 17 條" in out
    third = out.split("--- 第三段")[1]
    imm = third.split("OrderImmutabilityTest.java")[1].split("· src/")[0]
    assert "Type.class  :Order" in imm
