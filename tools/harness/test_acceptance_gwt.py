#!/usr/bin/env python3
"""`acceptance_gwt` 的離開碼 —— **三態要三個碼**。

這支工具原本零測試,而它裡面唯一「不用 gradle 也跑得動」的東西就是
**判定與離開碼**:三段的結論怎麼折成一個 exit code。真正卡住的是那三段本身
(`stage` 要 `git archive`、`run_tests` 要 `./gradlew`),所以下面把這兩支
換掉,只留判定路徑 —— 測的是**判定**,不是 gradle。

已知不在這裡測的:`stage` 的 git 取出、`run_tests` 的 XML 解析與
「類別層級就爆了」那條 fallback、`BREAKS` 的破壞點還在不在。
那些要 gradle 才驗得動,**沒驗過就不要假裝驗過**。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import acceptance_gwt as gwt  # noqa: E402


def _generated(tmp_path: Path, contract: str, ids: list[str]) -> Path:
    """一份最小的「生成物」:`contract_of` 與 `scenario_ids` 讀得到的那兩個形狀。

    刻意手寫而不是叫生成器產 —— 這裡要測的是判定,不是生成器。
    """
    body = "\n".join(f"    void scenario_{i}() {{}}" for i in ids)
    path = tmp_path / "OrderAcceptanceTest.java"
    path.write_text(
        f"// 這份骨架綁的是 wire 合約「{contract}」\n"
        f"package acceptance;\n"
        f"class OrderAcceptanceTest {{\n{body}\n}}\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def no_gradle(monkeypatch: pytest.MonkeyPatch):
    """`stage` / `run_tests` 換掉,並回傳一個「這一輪誰是紅的」的開關。"""
    state = {"reds": None}   # None = 全紅

    monkeypatch.setattr(gwt, "stage",
                        lambda generated, workdir, label, branch: Path(workdir) / label)
    monkeypatch.setattr(
        gwt, "run_tests",
        lambda app, ids: {
            i: ("failed" if state["reds"] is None or i in state["reds"] else "passed")
            for i in ids
        },
    )
    return state


def test_有不適用就是3不是0(tmp_path: Path, no_gradle) -> None:
    """**這是本次修的那條。** 合約對不上 → 第 2、3 段不適用,第 1 段(空骨架全紅)通過。

    報表本來就印「⏭️ 不適用」「**這不等於驗收通過**」,但**離開碼回 0** ——
    報表分得開、離開碼分不開,等於只有讀報表的人知道,自動化一律讀成綠。
    「整份/有項目不適用不算通過」是 ADR 0005 §6 的規矩,離開碼 3。
    """
    generated = _generated(tmp_path, "demo-other-v1", ["S1", "S2"])
    assert gwt.contract_of(generated) != gwt.FROZEN_CONTRACT   # 前提
    assert gwt.main(["x", str(generated), str(tmp_path / "work")]) == 3


def test_有項目未通過仍然是1(tmp_path: Path, no_gradle) -> None:
    """「沒通過」壓過「不適用」—— 1 不能被 3 蓋掉。

    空骨架**沒有全紅**(有東西在沒有實作的骨架上綠了)= 恆真的嫌疑,
    那是這支存在的第一個理由,不准被降級成「不適用」。
    """
    generated = _generated(tmp_path, "demo-other-v1", ["S1", "S2"])
    no_gradle["reds"] = {"S1"}          # S2 在空骨架上綠了 → 第 1 段不通過
    assert gwt.main(["x", str(generated), str(tmp_path / "work")]) == 1


def test_代理編碼的情境也算不適用(tmp_path: Path,
                                   monkeypatch: pytest.MonkeyPatch) -> None:
    """被排除在驗收之外的情境**不是通過**,離開碼要看得出來。

    落檔 12 條、驗收只驗 8 條,那個差距就是還沒補上的動詞缺口(票 01)。

    這裡合約**對得上**凍結那份,所以第 1、2 段都真的會跑、都通過 ——
    唯一的 ⏭️ 是代理編碼那一條。情境 id 刻意取 `SX`(不在 `BREAKS` 裡),
    第 3 段就沒有破壞點要跑,不必真的去改凍結骨架的 java。
    """
    generated = _generated(tmp_path, gwt.FROZEN_CONTRACT, ["SX"])
    (tmp_path / "OrderProxyAcceptanceTest.java").write_text(
        "class OrderProxyAcceptanceTest { void scenario_P1() {} }\n", encoding="utf-8"
    )
    assert "SX" not in gwt.BREAKS               # 前提:第 3 段沒東西可跑

    calls = {"n": 0}

    def runner(app, ids):
        calls["n"] += 1
        # 第 1 次是空骨架(要全紅),第 2 次是 OL1(要全綠)
        return {i: ("failed" if calls["n"] == 1 else "passed") for i in ids}

    monkeypatch.setattr(gwt, "stage",
                        lambda generated, workdir, label, branch: Path(workdir) / label)
    monkeypatch.setattr(gwt, "run_tests", runner)
    assert gwt.main(["x", str(generated), str(tmp_path / "work")]) == 3


def test_用法錯誤是2(tmp_path: Path) -> None:
    """參數個數不對、生成物裡一個 `scenario_*` 都沒有 —— 兩種都是**用法錯誤**,
    不是「不適用」:餵錯東西跟「有東西可查但這次查不了」是兩件事。"""
    assert gwt.main(["x"]) == 2
    empty = tmp_path / "OrderAcceptanceTest.java"
    empty.write_text("// wire 合約「demo-other-v1」\nclass X {}\n", encoding="utf-8")
    assert gwt.main(["x", str(empty), str(tmp_path / "work")]) == 2
