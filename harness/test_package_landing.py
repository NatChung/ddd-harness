#!/usr/bin/env python3
"""`package_landing_check` 的測試 —— 對**凍結骨架**驗,不是對我編的例子驗。

預測寫在 `.scratch/ddd-harness/11-PREDICTION.md`,**commit 在寫程式之前**(`e0e0164`),
凍結骨架的數字逐個寫死:7 個宣告過的 package、3 個自有、M = 3 全空、
6 條 archunit 規則的 from 側全部落在空 package。下面把那些數字釘成契約。

已知陽性就是凍結骨架本身:`src/main/java` 底下只有 `Application.java`(`package com.shop;`),
三個宣告過的層 **一個 class 都沒有** —— 而 `ArchitectureTest.java` 每條規則都帶
`allowEmptyShould(true)`,所以那套**必然綠**。這支就是量那個差額的。

合成測試只用在**凍結骨架驗不到、而錯的方向是假通過**的那幾條(點號邊界、大小寫、
root 推導的洞、萬用字元、目錄路徑 vs package 宣告)。其餘一律用真資料。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import package_landing_check as plc  # noqa: E402


def _patterns(entries: list[dict]) -> list[str]:
    return [e["pattern"] for e in entries]


def _write_class(src: Path, package: str, name: str) -> None:
    d = src / Path(*package.split("."))
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.java").write_text(
        f"package {package};\n\npublic final class {name} {{\n}}\n", encoding="utf-8"
    )


# ── 假通過的來源(凍結骨架驗不到,錯的方向是綠燈)────────────────────────

def test_上層package不算在下層pattern裡() -> None:
    """**這支最容易寫出來的 bug**:`com.shop` 被 `com.shop.domain..` 誤配。

    凍結骨架的 `Application` 就住 `com.shop` —— 寫成無邊界字串前綴的話,
    三個空 package 會一次全部假通過。
    """
    assert plc.covers("com.shop.domain..", "com.shop.domain") is True
    assert plc.covers("com.shop.domain..", "com.shop.domain.order") is True
    assert plc.covers("com.shop.domain..", "com.shop") is False
    assert plc.covers("com.shop.domain..", "com.shop.domainhelper") is False
    assert plc.covers("com.shop.domain..", "com.shop.Domain") is False  # Java 大小寫敏感


def test_root推導用點號分段不是字串前綴() -> None:
    """`com.shop.domain` 與 `com.shopping.x` 的字串共同前綴是 `com.shop` —— 那是假 root。"""
    assert plc.derive_root(["com.shop.domain..", "com.shop.usecase..", "com.shop.adapter.."]) == "com.shop"
    assert plc.derive_root(["com.shop.domain..", "com.shopping.x.."]) == "com"
    assert plc.derive_root(["com.shop.domain.."]) == "com.shop.domain"
    assert plc.derive_root([]) == ""


def test_單一from_package_是已知的假通過洞(tmp_path: Path) -> None:
    """⚠️ **已知的洞,釘成契約而不是假裝沒有。**

    from 側只有一個值時 root = 那整個 package,於是 to 側的 `com.shop.adapter..`
    被歸成「第三方」而不被檢查 —— 它空著也不會被報。
    這就是報表為什麼要**逐個印出被排除的 package**,以及 `--root` 為什麼存在。
    """
    (tmp_path / "x").mkdir()
    rows = [("A3", "com.shop.domain..", "from"), ("A3", "com.shop.adapter..", "to")]

    bad = plc.judge(tmp_path / "x", rows)
    assert bad["root_used"] == "com.shop.domain"
    assert _patterns(bad["external"]) == ["com.shop.adapter.."]  # ← 洞:被當第三方放走
    assert len(bad["empty"]) == 1

    fixed = plc.judge(tmp_path / "x", rows, root="com.shop")
    assert fixed["root_overridden"] is True
    assert len(fixed["empty"]) == 2 and fixed["external"] == []


def test_萬用字元pattern比不了_算不適用不算通過(tmp_path: Path) -> None:
    """schema 的 CHECK 只逼 `%..`,所以 `com.*.domain..` 寫得進去。

    比不了就丟進「不適用」——**絕不當通過**,而且 exit 非 0。
    """
    src = tmp_path / "src"
    src.mkdir()
    _write_class(src, "com.shop.domain", "Order")
    rows = [("A1", "com.shop..", "from"), ("A1", "com.*.domain..", "to")]
    rep = plc.judge(src, rows)
    assert _patterns(rep["unmatchable"]) == ["com.*.domain.."]
    assert rep["empty"] == []  # 自有那個是滿的
    assert plc.report(rep) == 1  # 但仍然不算通過


def test_package取自宣告不是目錄路徑(tmp_path: Path) -> None:
    """凍結骨架的目錄與宣告一致,**這份語料分不出兩種做法** —— 用合成釘。

    宣告才是編譯器與 ArchUnit 認的那個。
    """
    src = tmp_path / "src"
    (src / "wherever").mkdir(parents=True)
    (src / "wherever/Order.java").write_text(
        "package com.shop.domain;\n\nclass Order {}\n", encoding="utf-8"
    )
    assert plc.scan_sources(src) == {"com.shop.domain": ["Order"]}


def test_不是class的java檔不算數(tmp_path: Path) -> None:
    """`package-info.java` 只掛 package annotation,`module-info.java` 是模組宣告,
    只有 license 註解的檔案裡沒有型別 —— 三種都不能讓一個空 package 看起來有東西。"""
    src = tmp_path / "src"
    d = src / "com/shop/domain"
    d.mkdir(parents=True)
    (d / "package-info.java").write_text("package com.shop.domain;\n", encoding="utf-8")
    (d / "module-info.java").write_text("module com.shop {}\n", encoding="utf-8")
    (d / "Notes.java").write_text("package com.shop.domain;\n// 只有註解\n", encoding="utf-8")
    assert plc.scan_sources(src) == {}


def test_沒有package宣告的檔案進預設package(tmp_path: Path) -> None:
    """default package 的 class **不屬於任何宣告過的 package**,不能拿來充數。"""
    src = tmp_path / "src"
    src.mkdir()
    (src / "Loose.java").write_text("class Loose {}\n", encoding="utf-8")
    assert plc.scan_sources(src) == {plc.DEFAULT_PACKAGE: ["Loose"]}
    rep = plc.judge(src, [("A1", "com.shop.domain..", "from")])
    assert len(rep["empty"]) == 1 and rep["undeclared"] == {plc.DEFAULT_PACKAGE: ["Loose"]}


# ── 一條 package 都沒宣告 = 檢查本身不適用(離開碼 3)────────────────────

NO_RULE_YAML = """
authorized_templates: []
architecture_rules:
  - id: A7
    rule: customers 表由 harness 建好,不得為它建立領域物件
    provenance: 推導自
    provenance_ref: examples/shop/spec/ARCHITECTURE.md L31-32
    enforcement: none
    ladder_note: 搬不上去,只有 review 抓得到。
"""


def test_沒有任何package宣告_是不適用不是通過(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """**「找不到東西所以沒問題」是最廉價的假綠燈**(票 03 的教訓)。

    全部 enforcement=none 的 store,三張參數子表都空 —— 離開碼 3,不是 0。
    """
    spec = tmp_path / "arch.yaml"
    spec.write_text(NO_RULE_YAML, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    rep = plc.check(src, [spec])
    assert rep["declared_total"] == 0
    assert plc.main(["x", str(src), str(spec)]) == 3
    out = capsys.readouterr().out
    assert "本次不適用(不是通過)" in out


# ── root 沒對上任何宣告 = 什麼都沒檢查到(離開碼 3,票 14 缺陷二)──────────


def test_宣告全是萬用字元_理由不准賴給root(tmp_path: Path) -> None:
    """自有 0 個有兩種成因,**報表要分得出來** —— 賴給 root 的話人會去改 `--root`,
    而真正的問題是那些 pattern 這支比不了。"""
    src = tmp_path / "src"
    src.mkdir()
    _write_class(src, "com.shop.domain", "Order")
    rows = [("A1", "com.*.domain..", "from")]
    rep = plc.judge(src, rows)
    assert rep["owned"] == [] and rep["external"] == [] and len(rep["unmatchable"]) == 1
    assert plc.report(rep) == 3


# ── 吃錯東西要當場掛;空目錄不算吃錯 ────────────────────────────────────


def test_參數不足與不認得的選項都回二(tmp_path: Path) -> None:
    assert plc.main(["x"]) == 2
    assert plc.main(["x", "src"]) == 2
    assert plc.main(["x", "src", "architecture.yaml", "--nope"]) == 2


def test_root兩種寫法都吃() -> None:
    assert plc.parse_argv(["src", "a.yaml", "--root", "com.shop"]) == (["src", "a.yaml"], "com.shop")
    assert plc.parse_argv(["src", "--root=com.shop", "a.yaml"]) == (["src", "a.yaml"], "com.shop")
    with pytest.raises(ValueError):
        plc.parse_argv(["src", "a.yaml", "--root"])


def test_spec沒過驗證不會被當成沒有宣告(tmp_path: Path) -> None:
    """壞掉的 spec 回 2(用法錯),**不是** 3(不適用)也不是 0 —— 兩者混起來
    就會讓「spec 寫壞了」看起來像「這份 store 沒有架構規則」。"""
    spec = tmp_path / "bad.yaml"
    spec.write_text(
        "authorized_templates: []\n"
        "architecture_rules:\n"
        "  - id: A1\n"
        "    rule: 隨便\n"
        "    provenance: 這不是五格之一\n"
        "    provenance_ref: x\n"
        "    enforcement: none\n"
        "    ladder_note: y\n",
        encoding="utf-8",
    )
    src = tmp_path / "src"
    src.mkdir()
    assert plc.main(["x", str(src), str(spec)]) == 2
