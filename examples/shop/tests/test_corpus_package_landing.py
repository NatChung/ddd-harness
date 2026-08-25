#!/usr/bin/env python3
"""`package_landing_check` 的測試 —— 對**凍結骨架**驗,不是對我編的例子驗。

從 `harness/test_package_landing.py` 搬來(票 32):這幾支讀的是
`examples/shop/app/src/main/java`(凍結骨架)與 `examples/shop/harness/architecture.yaml`,
hub 沒有那份語料。預測寫在 `.scratch/ddd-harness/11-PREDICTION.md`,凍結骨架的數字
逐個寫死:7 個宣告過的 package、3 個自有、M = 3 全空、6 條規則整條不適用。
`_patterns` / `_write_class` 仍是 harness 那份測試檔的,這裡只 import;合成語料的那些留在 harness。
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import package_landing_check as plc  # harness/ 由 conftest 放進 sys.path
from test_package_landing import _patterns, _write_class

REPO = Path(__file__).resolve().parents[3]
SKELETON_SRC = REPO / "examples/shop/app/src/main/java"
ARCH_YAML = REPO / "examples/shop/harness/architecture.yaml"


def _arch_rows() -> list[tuple[str, str, str]]:
    """凍結骨架那份 spec 的 (rule_id, package, role) 三元組 —— 走 `check` 同一條路。"""
    import sqlite3
    import tempfile

    from spec_store import build_store, load_specs  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "spec.db"
        build_store(db, load_specs([ARCH_YAML]))
        conn = sqlite3.connect(db)
        try:
            return conn.execute(plc.DECLARED_SQL).fetchall()
        finally:
            conn.close()


# ── 預測的數字(凍結骨架,逐個釘死)──────────────────────────────────────

def test_凍結骨架_七個宣告三個自有四個第三方() -> None:
    """P1:去重後 7 個宣告過的 package,只有 3 個是本案自己的。

    天真寫法「每個宣告過的 package 都必須有 class」會把 4 個第三方判成缺,
    報表變成「7 缺 4」的噪音 —— **噪音會讓真正的 3 個缺被跳過去**。
    """
    rep = plc.check(SKELETON_SRC, [ARCH_YAML])
    assert rep["declared_total"] == 7
    assert _patterns(rep["owned"]) == [
        "com.shop.adapter..", "com.shop.domain..", "com.shop.usecase..",
    ]
    assert _patterns(rep["external"]) == [
        "com.fasterxml.jackson..", "jakarta.persistence..",
        "jakarta.transaction..", "org.springframework..",
    ]
    assert rep["unmatchable"] == []


def test_凍結骨架_root推導出com點shop() -> None:
    """P1b:root = `com.shop`,不是 `com`、不是 `com.shop.`(帶尾點)。"""
    rep = plc.check(SKELETON_SRC, [ARCH_YAML])
    assert rep["root_derived"] == rep["root_used"] == "com.shop"
    assert rep["root_overridden"] is False


def test_凍結骨架_三個自有package全空而且離開碼是一() -> None:
    """P2 + P6:**M = 3**,exit 1。

    `Application.java` 的 `com.shop` **不屬於** `com.shop.domain..`。
    M = 0 就表示比對被寫成了無邊界的字串前綴 —— **那個錯的方向是假通過**。
    """
    rep = plc.check(SKELETON_SRC, [ARCH_YAML])
    assert len(rep["empty"]) == 3 and rep["filled"] == []
    assert all(e["class_count"] == 0 for e in rep["empty"])
    assert plc.main(["x", str(SKELETON_SRC), str(ARCH_YAML)]) == 1


def test_凍結骨架_那一個class落在宣告外的com點shop() -> None:
    """P2b:唯一那個 class 落在 `com.shop` —— 一個**沒有任何規則宣告**的 package。"""
    rep = plc.check(SKELETON_SRC, [ARCH_YAML])
    assert rep["classes_total"] == 1
    assert rep["undeclared"] == {"com.shop": ["Application"]}


def test_凍結骨架_六條規則整條不適用() -> None:
    """P3:6 條 archunit 規則的 from 側全部落在空 package → **整套一條都沒在跑**。

    配上 `allowEmptyShould(true)`,它們綠得跟「完全遵守架構規則」一模一樣。
    """
    rep = plc.check(SKELETON_SRC, [ARCH_YAML])
    assert rep["vacuous_rules"] == ["A1", "A2", "A3", "A4", "A6", "A10"]
    assert rep["weakened_rules"] == []  # 六條全都因為 from 側就掛了,沒有只弱化的


# ── 破壞式:先確認破壞生效,再看數字 ────────────────────────────────────

def _copy_skeleton(tmp_path: Path) -> Path:
    src = tmp_path / "src/main/java"
    shutil.copytree(SKELETON_SRC, src)
    return src


def test_破壞式_在domain放一個class_三條規則從不適用變適用(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """P4。**先斷言破壞本身被看見**(掃描器報 `com.shop.domain` 非空),再斷言數字。

    順序是硬性的 —— 上一輪在這裡假通過過一次:破壞沒生效,而測試以為它驗到了。
    """
    src = _copy_skeleton(tmp_path)
    before = plc.check(src, [ARCH_YAML])
    assert len(before["empty"]) == 3  # 複製過來的骨架跟本尊一樣

    _write_class(src, "com.shop.domain", "Order")
    assert plc.scan_sources(src).get("com.shop.domain") == ["Order"], "破壞沒生效"
    print("mutated ok: com.shop.domain 現在有 Order")

    after = plc.check(src, [ARCH_YAML])
    assert len(after["empty"]) == 2
    assert _patterns(after["empty"]) == ["com.shop.adapter..", "com.shop.usecase.."]
    assert _patterns(after["filled"]) == ["com.shop.domain.."]
    # A1 / A3 / A6 翻面:from 側現在掃得到東西了
    assert after["vacuous_rules"] == ["A2", "A4", "A10"]
    # A3 的 from 側(domain)現在滿了 → 規則真的在跑,但它兩個禁止目標
    # (usecase / adapter)都不存在 → 那一半約束是空的。**這一格是報表 from/to
    # 分開講的唯一證據**,不釘住的話 weakened_rules 永遠只驗得到空 list。
    assert after["weakened_rules"] == ["A3"]
    assert plc.main(["x", str(src), str(ARCH_YAML)]) == 1  # 還有兩個空的 → 仍然不算通過
    assert "mutated ok" in capsys.readouterr().out


def test_子package也算數(tmp_path: Path) -> None:
    """`com.shop.domain.order.Order` 要能滿足 `com.shop.domain..`(pattern 的 `..` 的意思)。"""
    src = _copy_skeleton(tmp_path)
    _write_class(src, "com.shop.domain.order", "Order")
    rep = plc.check(src, [ARCH_YAML])
    assert _patterns(rep["filled"]) == ["com.shop.domain.."]
    assert rep["filled"][0]["packages"] == {"com.shop.domain.order": ["Order"]}


# ── 本票存在的理由:class 放到規格沒宣告的 package ──────────────────────

def test_攻擊情境_class放到order點domain_三個宣告照樣全空(tmp_path: Path) -> None:
    """**這就是這張票存在的理由**(ADR 0006 §3)。

    訪談那份 §10 寫 `order/domain`,凍結骨架寫 `com.shop.domain` —— 兩套本來就對不上。
    agent 照 §10 把 class 放進 `order.domain`,三套機械檢查裡的架構那套**全部靜靜不適用**,
    而且是綠的。這支要在那時候說「不適用」。
    """
    src = _copy_skeleton(tmp_path)
    for pkg, name in [("order.domain", "Order"),
                      ("order.application", "PlaceOrderService"),
                      ("order.adapter", "OrderController")]:
        _write_class(src, pkg, name)
    rep = plc.check(src, [ARCH_YAML])

    assert len(rep["empty"]) == 3, "宣告過的三個 package 照樣一個 class 都沒有"
    assert rep["vacuous_rules"] == ["A1", "A2", "A3", "A4", "A6", "A10"]
    assert rep["classes_total"] == 4  # 三個新的 + Application
    assert set(rep["undeclared"]) == {
        "com.shop", "order.adapter", "order.application", "order.domain",
    }
    assert plc.main(["x", str(src), str(ARCH_YAML)]) == 1


# ── 「不適用」不准折進「通過」(ADR 0005 §6)────────────────────────────

def test_不適用印在最上面而且明講不是通過(capsys: pytest.CaptureFixture[str]) -> None:
    """守衛沒有壞掉,是不再適用了,而**不適用不會有人發現** —— 除非把它印在第一個。"""
    plc.main(["x", str(SKELETON_SRC), str(ARCH_YAML)])
    out = capsys.readouterr().out
    assert "【不適用】—— 不是通過" in out
    assert out.index("【不適用】") < out.index("【通過】") < out.index("【不檢查")
    assert "整條不適用的規則(from 側掃不到任何 class)**:A1、A2、A3、A4、A6、A10" in out
    assert "共 6 條" in out
    assert "【通過】—— 宣告過而且真的有 class:**0 個 package**" in out


def test_報表自己印出已知上限(capsys: pytest.CaptureFixture[str]) -> None:
    """**讀報表的人拿不到票**,所以上限要印在報表裡,不是只寫在票裡。"""
    plc.main(["x", str(SKELETON_SRC), str(ARCH_YAML)])
    out = capsys.readouterr().out
    assert "只看「package 裡有沒有 class」,不看那些 class 對不對" in out
    assert "掃源碼樹,不掃編譯產出" in out
    assert "大小寫敏感" in out and "`com.shop` 不算在 `com.shop.domain..` 裡" in out
    assert "排除清單" in out and "最大的假通過來源" in out
    assert "「宣告外的 package」只印,不進判定" in out


def test_第三方排除清單逐個印出來(capsys: pytest.CaptureFixture[str]) -> None:
    """排除清單是這支最大的假通過來源 —— 只印個數的話沒人看得出哪個被放走了。"""
    plc.main(["x", str(SKELETON_SRC), str(ARCH_YAML)])
    out = capsys.readouterr().out
    for pkg in ("org.springframework..", "jakarta.persistence..",
                "jakarta.transaction..", "com.fasterxml.jackson.."):
        assert f"`{pkg}`" in out


# ── root 沒對上任何宣告 = 什麼都沒檢查到(離開碼 3,票 14 缺陷二)──────────

def test_root打錯一個字母_不是綠燈而是不適用(capsys: pytest.CaptureFixture[str]) -> None:
    """⚠️ **這條釘的是「離開碼會翻綠」那一半。**

    `--root com.shopp`(多一個 p)→ 三個自有 package 全被歸成第三方 →
    空的 0 個 → 舊版 `return 1 if (empty or unmatchable) else 0` 給出 **0**。
    上限段本來就寫著「排除清單是最大的假通過來源」,但沒說離開碼會翻綠,
    而**翻綠才是會騙到人的那半**。
    """
    # 破壞前:正常跑是 1(三個自有 package 全空)
    assert plc.main(["x", str(SKELETON_SRC), str(ARCH_YAML)]) == 1
    capsys.readouterr()

    rep = plc.judge(SKELETON_SRC, _arch_rows(), root="com.shopp")
    # 破壞真的生效了才問得下去:7 個宣告**全部**被歸成第三方,自有 0 個
    assert rep["declared_total"] == 7, "mutated ok"
    assert len(rep["external"]) == 7 and rep["owned"] == [], "mutated ok"
    assert rep["empty"] == [] and rep["unmatchable"] == []  # ← 舊版就是靠這兩個空的翻綠

    assert plc.report(rep) == 3
    out = capsys.readouterr().out
    assert "自有 package = 0 個" in out and "不是乾淨" in out
    assert "打錯了嗎?" in out and "`com.shop`" in out       # 推導值當提示印出來
    assert "整份不適用,不是通過" in out
    assert plc.main(["x", str(SKELETON_SRC), str(ARCH_YAML), "--root", "com.shopp"]) == 3


def test_推導出空root_也是同一條_不是綠燈() -> None:
    """`--root=` 或推不出共同前綴時 root 是空字串 —— 一樣是「一個都沒檢查到」。

    不用打錯字也踩得到:所以判定條件卡在**自有 package = 0**,不是卡在「root 長得怪」。
    """
    rows = _arch_rows()
    rep = plc.judge(SKELETON_SRC, rows, root="")
    assert rep["root_used"] == "" and rep["owned"] == [], "mutated ok"
    assert plc.report(rep) == 3
    assert plc.main(["x", str(SKELETON_SRC), str(ARCH_YAML), "--root="]) == 3


# ── 吃錯東西要當場掛;空目錄不算吃錯 ────────────────────────────────────

def test_吃錯目錄要當場掛而且離開碼是二不是一(tmp_path: Path) -> None:
    """沒有那個目錄就是餵錯東西,要立刻知道,不要回一份空報表讓人以為乾淨。

    **而且離開碼必須是 2。** 1 是「宣告過的 package 空著」那個判定 —— 兩者混起來,
    吃錯路徑就會被讀成「實作把 package 放光了」:檢查根本沒跑,卻回報了
    它存在的理由那個結論。
    """
    with pytest.raises(SystemExit) as exc:
        plc.scan_sources(tmp_path / "nope")
    assert exc.value.code == 2

    with pytest.raises(SystemExit) as exc:
        plc.main(["x", str(tmp_path / "nope"), str(ARCH_YAML)])
    assert exc.value.code == 2


def test_空目錄不是吃錯_是合法的空骨架(tmp_path: Path) -> None:
    """目錄在、零個 `.java` = 還沒開始寫,不是用法錯 —— M = 全部、exit 1。"""
    src = tmp_path / "src"
    src.mkdir()
    assert plc.scan_sources(src) == {}
    assert plc.main(["x", str(src), str(ARCH_YAML)]) == 1


def test_main真的走check_不是自己抄一份(monkeypatch: pytest.MonkeyPatch) -> None:
    """**上面那 10 個 `plc.check(...)` 要測得到生產路徑,前提是 `main()` 真的呼叫它。**

    原本 `main()` 裡是一段 `check()` 的**逐行複本**(store→SQL→`judge`,只差
    `spec_paths` / `args[1:]`),而 `check()` 生產路徑上零呼叫者 —— 於是這份測試
    檔測的是**沒人跑的那一份**,兩份各自漂而漂了不會有人發現。這條把它釘住:
    換掉 `check` 就要看得到 `main` 的結果跟著變。

    順便釘 `--root` 有傳下去 —— 那正是複本與 `check()` 唯一的差異,
    也是「合而為一時最容易掉的那一格」。
    """
    seen: dict = {}

    def fake_check(src_root, spec_paths, root=None):
        seen["args"] = (Path(src_root), [str(p) for p in spec_paths], root)
        return plc.judge(SKELETON_SRC, _arch_rows(), root=root)

    monkeypatch.setattr(plc, "check", fake_check)
    assert plc.main(["x", str(SKELETON_SRC), str(ARCH_YAML), "--root", "com.shopp"]) == 3
    assert seen["args"] == (SKELETON_SRC, [str(ARCH_YAML)], "com.shopp")
