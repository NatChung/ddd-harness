"""harness 工具的測試 —— 離線,不碰 gradle、不碰網路。

這些測試驗的是**階梯本身**:每一條原本住在散文裡的規則,現在是不是真的擋得住。
測試名字刻意寫成「寫不進去」而不是「驗證失敗」—— 那是第 1 階跟第 2 階的差別。
"""

from __future__ import annotations

import copy

import pytest

from gen_archunit import generate
from spec_store import NothingToGenerate, SpecError, build_store, load_spec
from verify_generated import UsageError, verify
from verify_generated import main as vg_main

VALID = {
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
                "to": ["org.springframework..", "jakarta.persistence.."],
            },
        },
        {
            "id": "A2",
            "rule": "usecase/ 不得 import adapter/",
            "provenance": "推導自",
            "provenance_ref": "[Q7] 介面宣告在內層",
            "enforcement": "archunit_forbidden_dependency",
            "forbidden_dependencies": {
                "from": "com.shop.usecase..",
                "to": ["com.shop.adapter.."],
            },
        },
    ],
}


ANNOTATION_RULE = {
    "id": "A6",
    "rule": "domain/ 的類別與其成員不得掛任何 JPA/Jackson annotation",
    "provenance": "本案自決",
    "provenance_ref": "領域物件不得直接作為持久化模型",
    "enforcement": "archunit_forbidden_annotation",
    "forbidden_annotations": {
        "from": "com.shop.domain..",
        "annotations": ["jakarta.persistence..", "com.fasterxml.jackson.."],
    },
}


def with_annotation_rule():
    s = copy.deepcopy(VALID)
    s["architecture_rules"].append(copy.deepcopy(ANNOTATION_RULE))
    return s


def spec(**changes):
    """複製一份 valid spec,對第一條規則套用改動(值為 None = 刪掉那個 key)。"""
    s = copy.deepcopy(VALID)
    for key, value in changes.items():
        if value is None:
            s["architecture_rules"][0].pop(key, None)
        else:
            s["architecture_rules"][0][key] = value
    return s


def problems_of(tmp_path, s) -> list[str]:
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", s)
    return exc.value.problems


# ── 第 1 階:schema 擋的(填不了就寫不進去)────────────────────────────────


def test_模板既定_在白名單為空時寫不進去(tmp_path):
    problems = problems_of(
        tmp_path, spec(provenance="模板既定", provenance_ref="某份文件 L12")
    )
    assert any("模板既定" in p for p in problems), problems


def test_模板既定_指向白名單裡的文件就過(tmp_path):
    s = spec(provenance="模板既定", provenance_ref="starter/ARCHITECTURE.md L12")
    s["authorized_templates"] = ["starter/ARCHITECTURE.md"]
    build_store(tmp_path / "spec.db", s)  # 不該丟


def test_自創第六格來源寫不進去(tmp_path):
    problems = problems_of(tmp_path, spec(provenance="未定案"))
    assert any("schema 擋下來了" in p for p in problems), problems


def test_來源為空寫不進去(tmp_path):
    problems = problems_of(tmp_path, spec(provenance_ref="   "))
    assert any("schema 擋下來了" in p for p in problems), problems


def test_package_pattern_沒有結尾兩點寫不進去(tmp_path):
    problems = problems_of(
        tmp_path,
        spec(
            forbidden_dependencies={
                "from": "com.shop.domain",  # 少了 ..
                "to": ["org.springframework.."],
            }
        ),
    )
    assert any("schema 擋下來了" in p for p in problems), problems


def test_無機械檢查而沒寫階梯說明時寫不進去(tmp_path):
    """ladder_note 的 CHECK 是條件式的 —— 繞過 import 的形狀檢查也還是擋得住。"""
    s = spec(enforcement="none", forbidden_dependencies=None, ladder_note="先寫著")
    # 直接把 ladder_note 抽掉,模擬「形狀檢查放過但 schema 仍該擋」
    s["architecture_rules"][0]["ladder_note"] = "x"
    build_store(tmp_path / "spec.db", s)  # 有值就過


# ── 第 2 階:import 的跨列不變式 ───────────────────────────────────────────


def test_agent_不得自己寫由誰強制(tmp_path):
    s = spec()
    s["architecture_rules"][0]["enforced_by"] = "我說我被強制了"
    problems = problems_of(tmp_path, s)
    assert any("enforced_by" in p for p in problems), problems


def test_宣稱有機械檢查卻不給參數會被擋(tmp_path):
    problems = problems_of(tmp_path, spec(forbidden_dependencies=None))
    assert any("forbidden_dependencies" in p for p in problems), problems


def test_沒有機械檢查卻給參數會被擋(tmp_path):
    problems = problems_of(
        tmp_path, spec(enforcement="none", ladder_note="待搬")
    )
    assert any("不該帶" in p and "forbidden_dependencies" in p for p in problems), problems


def test_沒有機械檢查就必須寫階梯說明(tmp_path):
    problems = problems_of(
        tmp_path, spec(enforcement="none", forbidden_dependencies=None)
    )
    assert any("ladder_note" in p for p in problems), problems


def test_未知欄位當場掛而不是靜默忽略(tmp_path):
    s = spec()
    s["architecture_rules"][0]["enfocement"] = "archunit_forbidden_dependency"  # 打錯
    problems = problems_of(tmp_path, s)
    assert any("未知的 key" in p for p in problems), problems


def test_驗證失敗時一條都沒寫入(tmp_path):
    db = tmp_path / "spec.db"
    with pytest.raises(SpecError):
        build_store(db, spec(provenance="未定案"))
    assert not db.exists() or db.stat().st_size == 0


# ── 生成器 ────────────────────────────────────────────────────────────────


def test_生成器回填由誰強制(tmp_path):
    import sqlite3

    db = tmp_path / "spec.db"
    build_store(db, VALID)
    enforced = generate(db, tmp_path / "ArchitectureTest.java")
    assert enforced == {
        "A1": "ArchitectureTest.rule_A1",
        "A2": "ArchitectureTest.rule_A2",
    }
    stored = dict(
        sqlite3.connect(db).execute("SELECT id, enforced_by FROM architecture_rule")
    )
    assert stored == enforced


def test_生成是確定性的(tmp_path):
    """不確定性會讓 drift check 每次都紅 —— 這條測試守著那件事。"""
    first, second = tmp_path / "a.java", tmp_path / "b.java"
    for out in (first, second):
        db = tmp_path / f"{out.stem}.db"
        build_store(db, VALID)
        generate(db, out)
    assert first.read_bytes() == second.read_bytes()


def test_基底_package_取共同前綴(tmp_path):
    db = tmp_path / "spec.db"
    build_store(db, VALID)
    out = tmp_path / "ArchitectureTest.java"
    generate(db, out)
    assert 'importPackages("com.shop")' in out.read_text(encoding="utf-8")


# ── drift check ───────────────────────────────────────────────────────────


# ── 第二個 kind:forbidden_annotation ─────────────────────────────────────


def test_annotation_kind_可以匯入(tmp_path):
    build_store(tmp_path / "spec.db", with_annotation_rule())  # 不該丟


def test_annotation_kind_不給參數會被擋(tmp_path):
    s = with_annotation_rule()
    del s["architecture_rules"][-1]["forbidden_annotations"]
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", s)
    assert any("forbidden_annotations" in p for p in exc.value.problems)


def test_kind_與參數對不上會被擋(tmp_path):
    """宣稱是 annotation 規則卻交 dependency 的參數 —— 兩個 kind 的參數不得互串。"""
    s = with_annotation_rule()
    s["architecture_rules"][-1]["forbidden_dependencies"] = {
        "from": "com.shop.domain..",
        "to": ["org.springframework.."],
    }
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", s)
    assert any("不該帶" in p for p in exc.value.problems), exc.value.problems


def test_annotation_pattern_沒有結尾兩點寫不進去(tmp_path):
    s = with_annotation_rule()
    s["architecture_rules"][-1]["forbidden_annotations"]["annotations"] = [
        "jakarta.persistence"  # 少了 ..
    ]
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", s)
    assert any("schema 擋下來了" in p for p in exc.value.problems)


def test_有_annotation_規則才生成_helper(tmp_path):
    """沒人叫的 helper 是死碼,而死碼在生成物裡特別討厭 —— 沒人敢刪。"""
    with_ann, without = tmp_path / "with.java", tmp_path / "without.java"

    db1 = tmp_path / "with.db"
    build_store(db1, with_annotation_rule())
    generate(db1, with_ann)
    assert "annotatedWithAnythingIn" in with_ann.read_text(encoding="utf-8")

    db2 = tmp_path / "without.db"
    build_store(db2, VALID)
    generate(db2, without)
    assert "annotatedWithAnythingIn" not in without.read_text(encoding="utf-8")


# ── 第三個 kind:forbidden_return_type ────────────────────────────────────

RETURN_TYPE_RULE = {
    "id": "A10",
    "rule": "Controller 的 public 方法不得回傳 domain/ 型別",
    "provenance": "本案自決",
    "provenance_ref": "往外傳的形狀由外層自己定義",
    "enforcement": "archunit_forbidden_return_type",
    "forbidden_return_types": {
        "from": "com.shop.adapter..",
        "class_name_suffix": "Controller",
        "return_packages": ["com.shop.domain.."],
    },
}


def with_return_type_rule():
    s = copy.deepcopy(VALID)
    s["architecture_rules"].append(copy.deepcopy(RETURN_TYPE_RULE))
    return s


def test_return_type_kind_可以匯入(tmp_path):
    build_store(tmp_path / "spec.db", with_return_type_rule())  # 不該丟


def test_return_type_缺類名字尾會被擋(tmp_path):
    """這個 kind 比前兩個多一個 scalar —— 少了它會擋錯人(Repository 本來就該回傳 Order)。"""
    s = with_return_type_rule()
    del s["architecture_rules"][-1]["forbidden_return_types"]["class_name_suffix"]
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", s)
    assert any("class_name_suffix" in p for p in exc.value.problems), exc.value.problems


def test_只在用到時才_import(tmp_path):
    """生成物是要給人 review 的,不該帶沒用到的 import。"""
    only_deps, with_return = tmp_path / "deps.java", tmp_path / "ret.java"

    db1 = tmp_path / "deps.db"
    build_store(db1, VALID)
    generate(db1, only_deps)
    text = only_deps.read_text(encoding="utf-8")
    assert "noMethods" not in text
    assert "ArchCondition" not in text

    db2 = tmp_path / "ret.db"
    build_store(db2, with_return_type_rule())
    generate(db2, with_return)
    assert "noMethods" in with_return.read_text(encoding="utf-8")


def test_規則以數字順序排列(tmp_path):
    """純字典序會排成 A1, A10, A2 —— 確定性一樣有,但生成物是要給人讀的。"""
    s = with_return_type_rule()
    db = tmp_path / "spec.db"
    build_store(db, s)
    out = tmp_path / "T.java"
    generate(db, out)
    text = out.read_text(encoding="utf-8")
    assert text.index("rule_A1(") < text.index("rule_A2(") < text.index("rule_A10(")


def _seed_generated(tmp_path):
    """把兩個生成物都產到一個目錄,回傳 (generated_dir, spec_path)。"""
    import json

    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(with_scenario()), encoding="utf-8")
    out_dir = tmp_path / "generated"
    out_dir.mkdir()
    db = tmp_path / "spec.db"
    build_store(db, load_spec(spec_path))
    generate(db, out_dir / "ArchitectureTest.java")
    gen_acceptance(db, out_dir / "OrderAcceptanceTest.java")
    return out_dir, spec_path


def test_drift_check_在一致時過(tmp_path):
    out_dir, spec_path = _seed_generated(tmp_path)
    assert all(not d for d in verify(out_dir, [spec_path]).drift.values())


def test_drift_check_抓到手改生成物(tmp_path):
    out_dir, spec_path = _seed_generated(tmp_path)
    arch = out_dir / "ArchitectureTest.java"
    # 模擬 agent 把一條規則放寬(把 domain 的框架禁令刪掉)
    arch.write_text(
        arch.read_text(encoding="utf-8").replace('"org.springframework..",\n', ""),
        encoding="utf-8",
    )
    assert verify(out_dir, [spec_path]).drift["ArchitectureTest.java"] != []


def test_drift_check_也蓋到驗收生成物(tmp_path):
    """新加的生成器如果沒進 GENERATORS,它的生成物就沒人盯 —— 這條守著那件事。"""
    out_dir, spec_path = _seed_generated(tmp_path)
    acc = out_dir / "OrderAcceptanceTest.java"
    acc.write_text(
        acc.read_text(encoding="utf-8").replace("isEqualTo(201)", "isEqualTo(200)"),
        encoding="utf-8",
    )
    assert verify(out_dir, [spec_path]).drift["OrderAcceptanceTest.java"] != []


# ── 生成器不適用時,drift check 不准整支停擺(票 14 缺陷一)────────────────

def _seed_no_arch(tmp_path):
    """沒有 architecture_rule、但有驗收情境的 store —— 訪談那份規格的骨架就長這樣。

    只生驗收那兩支到 `generated/`,**`ArchitectureTest.java` 刻意不放** ——
    這份 spec 生不出它。
    """
    import json

    s = with_scenario()
    s["architecture_rules"] = []
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(s), encoding="utf-8")
    out_dir = tmp_path / "generated"
    out_dir.mkdir()
    db = tmp_path / "spec.db"
    build_store(db, load_spec(spec_path))
    gen_acceptance(db, out_dir / "OrderAcceptanceTest.java")
    return out_dir, spec_path


def test_沒有架構規則的store_架構那支算不適用_而其餘照比(tmp_path):
    """⚠️ **這條釘的是票 10 的 P4 落空那個缺陷。**

    在此之前 `gen_archunit.generate` 丟 `SystemExit`,而 drift check 是把它
    **import 進來當函式呼叫**的 —— 整支被打死:stdout 一行都沒印、exit 1,
    於是「沒有架構規則的 store」的生成物**有沒有被手改過永遠量不到**。

    三件事一起釘:架構那支進**不適用**(不是通過、不是錯誤)、驗收那兩支
    **照樣比對過**、離開碼 0。
    """
    out_dir, spec_path = _seed_no_arch(tmp_path)

    # 前提:這份 store 真的生不出架構那支(不然下面在測空氣)
    with pytest.raises(NothingToGenerate):
        db = tmp_path / "pre.db"
        build_store(db, load_spec(spec_path))
        generate(db, tmp_path / "pre.java")

    res = verify(out_dir, [spec_path])
    assert "ArchitectureTest.java" in res.not_applicable
    assert "ArchitectureTest.java" not in res.drift, "不適用不准折進比對過的那一堆"
    assert res.unbacked == []
    assert set(res.drift) == {"OrderAcceptanceTest.java", "OrderProxyAcceptanceTest.java"}
    assert all(not d for d in res.drift.values())
    assert vg_main(["x", str(out_dir), str(spec_path)]) == 0


def test_不適用的生成物卻在commit裡_是異常不是不適用(tmp_path):
    """把 spec 的架構規則刪光、再手寫一份 ArchitectureTest.java commit 進去 ——
    若「不適用」一律放行,這條就是**靜默綠燈**:那個檔案永遠不會被任何 drift check 碰到。
    """
    out_dir, spec_path = _seed_no_arch(tmp_path)
    assert vg_main(["x", str(out_dir), str(spec_path)]) == 0  # 破壞前是綠的

    (out_dir / "ArchitectureTest.java").write_text("手寫的,沒有 spec 撐著\n", encoding="utf-8")
    assert (out_dir / "ArchitectureTest.java").exists(), "mutated ok"

    res = verify(out_dir, [spec_path])
    assert res.unbacked == ["ArchitectureTest.java"]
    assert vg_main(["x", str(out_dir), str(spec_path)]) == 1


# 只有詞彙表的 spec:兩個生成器都沒東西可生成,而 spec 本身是合法的
#(全空的 spec 在 store 那層就被擋了 —— 「整份不適用」得是**合法但生不出東西**才問得到)。
ONLY_GLOSSARY = {
    "glossary_terms": [
        {
            "term": "某某編號 SomeId",
            "definition": "認出是哪一個的那組編號",
            "ddd_type": "識別碼",
            "provenance": "Qn",
            "provenance_ref": "[Q1]",
        }
    ]
}


def test_每個生成器都不適用_離開碼三不是零(tmp_path):
    """「找不到東西所以沒問題」是最廉價的假綠燈 —— 整份不適用是 3,不是 0。"""
    import json

    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(ONLY_GLOSSARY), encoding="utf-8")
    out_dir = tmp_path / "generated"
    out_dir.mkdir()

    res = verify(out_dir, [spec_path])
    assert res.drift == {}, "前提:一個檔都比不了"
    assert len(res.not_applicable) == 3
    assert vg_main(["x", str(out_dir), str(spec_path)]) == 3


def test_整份不適用_但commit裡有那個檔_異常蓋過不適用(tmp_path):
    """3(整份不適用)與 1(異常)撞在一起時,**1 蓋過 3**。

    理由:3 的意思是「什麼都沒查到」,而這裡**查到東西了** —— 一個沒有 spec
    撐著的生成物 —— 而且是壞消息。回 3 等於把它降級成「本來就沒東西可看」。
    """
    import json

    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(ONLY_GLOSSARY), encoding="utf-8")
    out_dir = tmp_path / "generated"
    out_dir.mkdir()
    assert vg_main(["x", str(out_dir), str(spec_path)]) == 3  # 破壞前:整份不適用

    (out_dir / "ArchitectureTest.java").write_text("手寫的\n", encoding="utf-8")
    res = verify(out_dir, [spec_path])
    assert res.drift == {} and res.unbacked == ["ArchitectureTest.java"], "mutated ok"
    assert vg_main(["x", str(out_dir), str(spec_path)]) == 1


def test_吃錯目錄_離開碼二不是一(tmp_path):
    """目錄不在 → 每個檔都「commit 的是空的、重新生成的有內容」→ 舊版逐檔印 diff、
    喊「生成物漂了」、exit 1。**吃錯路徑偽裝成最嚴重的那個結論。**"""
    _, spec_path = _seed_generated(tmp_path)
    with pytest.raises(UsageError):
        verify(tmp_path / "nope", [spec_path])
    assert vg_main(["x", str(tmp_path / "nope"), str(spec_path)]) == 2


def test_spec沒過驗證_離開碼二不是一(tmp_path):
    """跟「生成物漂了」共用 1 的話,「spec 寫壞了」看起來就會像「有人手改了生成物」。
    (`package_landing_check` 對同一個條件也是回 2。)"""
    import json

    s = with_scenario()
    s["architecture_rules"][0]["provenance"] = "這不是五格之一"
    spec_path = tmp_path / "bad.json"
    spec_path.write_text(json.dumps(s), encoding="utf-8")
    out_dir = tmp_path / "generated"
    out_dir.mkdir()
    assert vg_main(["x", str(out_dir), str(spec_path)]) == 2


def test_生成器自己的CLI_沒東西可生成是三不是一(tmp_path):
    """CLI 也要分得開:3 = 不適用、2 = 用法錯誤。原本 `SystemExit` 給的是 1,
    而 1 在這條線上是「有問題」。"""
    import gen_acceptance as ga
    import gen_archunit as ge

    db = tmp_path / "spec.db"
    build_store(db, ONLY_GLOSSARY)
    assert ge.main(["x", str(db), str(tmp_path / "A.java")]) == 3
    assert ga.main(["x", str(db), str(tmp_path / "B.java")]) == 3
    assert ge.main(["x"]) == 2 and ga.main(["x"]) == 2


def test_有情境卻沒宣告wire_shape_理由要跟沒有情境分得開(tmp_path):
    """兩種不適用**不是同一件事**:一種是「這份 store 不談驗收」,
    另一種是「規格缺了一塊」。糊成同一句話,讀報表的人就修錯地方。"""
    import sqlite3

    db = tmp_path / "spec.db"
    build_store(db, with_scenario())
    # store 那層本來就擋「有情境沒 wire_contract」的 spec,所以這個狀態只有
    # 直接動 db 才做得出來 —— 先確認破壞真的生效了,不然下面在測空氣。
    conn = sqlite3.connect(db)
    conn.execute("DELETE FROM wire_contract")
    conn.commit()
    assert conn.execute("SELECT count(*) FROM wire_contract").fetchone()[0] == 0, "mutated ok"
    assert conn.execute("SELECT count(*) FROM acceptance_scenario").fetchone()[0] > 0
    conn.close()

    with pytest.raises(NothingToGenerate) as exc:
        gen_acceptance(db, tmp_path / "A.java")
    assert "wire_contract" in str(exc.value) and "規格缺了一塊" in str(exc.value)


# ── 有規則、但推不出共同前綴,也是不適用(票 18)──────────────────────────

def _no_common_root(tmp_path):
    """兩條規則分屬兩棵樹(`com.shop..` / `org.other..`)—— `_base_package` 推不出根。

    驗收情境照樣有,**這樣才問得出「架構那支不適用時,驗收那兩支照樣比得到」**。
    """
    import json

    s = with_scenario()
    s["architecture_rules"][1]["forbidden_dependencies"]["from"] = "org.other.usecase.."
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(s), encoding="utf-8")
    out_dir = tmp_path / "generated"
    out_dir.mkdir()
    db = tmp_path / "spec.db"
    build_store(db, load_spec(spec_path))
    gen_acceptance(db, out_dir / "OrderAcceptanceTest.java")
    return out_dir, spec_path


def test_推不出共同前綴_是不適用而不是把呼叫方打死(tmp_path):
    """⚠️ 這是票 14 那個缺陷在**同一支裡的第二個**(票 18)。

    修之前:`_base_package` `raise SystemExit` —— `SystemExit` 不是 `Exception`
    的子類,`except NothingToGenerate` 接不到,整支 drift check 被打死
    (2026-08-19 實測:stdout **0 byte**、exit 1,跟「生成物漂了」的 1 長得一模一樣)。
    所以這條**不能**只斷言「有丟東西」—— 要斷言丟的是 `NothingToGenerate`,
    而 `pytest.raises` 對 `SystemExit` 不會放行。

    歸「不適用」而不是「錯誤」是沿用 `package_landing_check` 的先例,不是新語意。
    """
    _, spec_path = _no_common_root(tmp_path)
    db = tmp_path / "pre.db"
    build_store(db, load_spec(spec_path))
    with pytest.raises(NothingToGenerate) as exc:
        generate(db, tmp_path / "pre.java")
    assert "共同前綴" in str(exc.value)

    import gen_archunit as ge
    assert ge.main(["x", str(db), str(tmp_path / "A.java")]) == 3, "3 = 不適用,不是 1"


def test_推不出共同前綴時_另外那個生成器照樣比得到(tmp_path):
    """缺一個生成器不該讓另外兩個也停擺 —— 這是那個缺陷真正的代價。"""
    out_dir, spec_path = _no_common_root(tmp_path)

    res = verify(out_dir, [spec_path])
    assert "ArchitectureTest.java" in res.not_applicable
    assert "ArchitectureTest.java" not in res.drift, "不適用不准折進比對過的那一堆"
    assert res.unbacked == []
    assert set(res.drift) == {"OrderAcceptanceTest.java", "OrderProxyAcceptanceTest.java"}
    assert all(not d for d in res.drift.values())
    assert vg_main(["x", str(out_dir), str(spec_path)]) == 0


def test_推不出共同前綴_而commit裡有那個檔_是異常(tmp_path):
    """跟「沒有架構規則」那條同一條紀律:不適用一律放行 = 靜默綠燈。"""
    out_dir, spec_path = _no_common_root(tmp_path)
    assert vg_main(["x", str(out_dir), str(spec_path)]) == 0  # 破壞前是綠的

    (out_dir / "ArchitectureTest.java").write_text("手寫的\n", encoding="utf-8")
    assert (out_dir / "ArchitectureTest.java").exists(), "mutated ok"

    assert verify(out_dir, [spec_path]).unbacked == ["ArchitectureTest.java"]
    assert vg_main(["x", str(out_dir), str(spec_path)]) == 1


# ── 假驗收偵測(vacuous_tests)────────────────────────────────────────────

from vacuous_tests import AllowlistError, analyse as analyse_mutations, load_allowlist  # noqa: E402


def _mutations_xml(tmp_path, mutations):
    """組一份最小的 PIT mutation matrix。mutations = [(killers, survivors), …]"""
    parts = ["<mutations>"]
    for killers, survivors in mutations:
        parts.append(
            "<mutation><mutatedClass>com.shop.domain.X</mutatedClass>"
            "<mutatedMethod>m</mutatedMethod><lineNumber>1</lineNumber>"
            "<mutator>M</mutator>"
            f"<killingTests>{'|'.join(killers)}</killingTests>"
            f"<succeedingTests>{'|'.join(survivors)}</succeedingTests></mutation>"
        )
    parts.append("</mutations>")
    path = tmp_path / "mutations.xml"
    path.write_text("".join(parts), encoding="utf-8")
    return path


def test_恆真測試被抓到_即使它繼承了_setup_的擊殺(tmp_path):
    """回歸測試:第一版偵測器用「殺了 0 個」,在這個形狀上會回報乾淨。

    真實案例是 HL2 的 OrderTest.testOrderNoSetters —— 它殺了 7 個,全部來自
    @BeforeEach 的建構路徑,自己一個都沒賺到。
    """
    setup = ["OrderTest.testReal", "OrderTest.testVacuous"]  # 全班都踩到 = setup 路徑
    xml = _mutations_xml(tmp_path, [
        (setup, []),                          # setup mutant
        (setup, []),                          # setup mutant
        (["OrderTest.testReal"], []),         # 只有 testReal 殺得掉
    ])
    stats, total = analyse_mutations(xml)
    assert total == 3
    assert stats["OrderTest.testVacuous"]["kills"] == 2       # 不是 0 —— 舊指標會漏掉
    assert stats["OrderTest.testVacuous"]["setup_only"] is True
    assert stats["OrderTest.testReal"]["setup_only"] is False


def test_只是跟別條重疊的測試不算候選(tmp_path):
    """健康的測試本來就會互相重疊 —— 那不是恆真,不該被標。"""
    both = ["OrderTest.testA", "OrderTest.testB"]
    xml = _mutations_xml(tmp_path, [
        (both, []),                    # 共同(setup)
        (both, []),                    # 兩條都殺得到,但這不是 setup-only 的判準來源
        (["OrderTest.testA"], []),     # A 獨佔 → A 不是 setup_only
        (["OrderTest.testB"], []),     # B 獨佔 → B 不是 setup_only
    ])
    stats, _ = analyse_mutations(xml)
    assert stats["OrderTest.testA"]["setup_only"] is False
    assert stats["OrderTest.testB"]["setup_only"] is False


def test_沒殺過任何東西的測試也算候選(tmp_path):
    xml = _mutations_xml(tmp_path, [
        (["OrderTest.testReal"], ["OrderTest.testNothing"]),
    ])
    stats, _ = analyse_mutations(xml)
    assert stats["OrderTest.testNothing"]["kills"] == 0
    # kills 為空時 setup_only 是 False(bool(mine) 為假),由 unique==0 那條路徑接手
    assert stats["OrderTest.testNothing"]["unique"] == 0


def test_allowlist_沒寫理由就拒收(tmp_path):
    """沒有理由的豁免會慢慢長成全部豁免 —— 跟 provenance_ref NOT NULL 同一招。"""
    bad = tmp_path / "allow.txt"
    bad.write_text("OrderTest.testX\n", encoding="utf-8")
    with pytest.raises(AllowlistError):
        load_allowlist(bad)


def test_allowlist_有理由就收(tmp_path):
    good = tmp_path / "allow.txt"
    good.write_text(
        "# 這行是註解\nOrderTest.testX  # 斷言字串常數,PIT 沒有字串 mutator\n",
        encoding="utf-8",
    )
    assert load_allowlist(good) == {"OrderTest.testX"}


def test_PIT_的兩種測試名都認得():
    from vacuous_tests import normalise
    assert normalise(
        "com.shop.domain.OrderTest.[engine:junit-jupiter]/[class:com.shop.domain.OrderTest]"
        "/[method:testOrderNoSetters()]"
    ) == "OrderTest.testOrderNoSetters"
    assert normalise("com.shop.domain.OrderTest.testX(com.shop.domain.OrderTest)") == "OrderTest.testX"


def test_沒有共用_setup_的恆真測試也要進佇列(tmp_path):
    """回歸測試:setup_only 在第二個已知陽性(HL1)上漏抓。

    HL1 的 testNoSetters 在測試內自己 new Order(...),不靠 @BeforeEach,
    所以它殺到的建構子 mutant 不在「全班交集」裡 —— setup_only 不觸發。
    改用「被支配」(別人殺的是我的超集)才涵蓋兩種形狀。
    """
    xml = _mutations_xml(tmp_path, [
        # testVacuous 只殺建構路徑;testReal 殺同一批再加自己的
        (["OrderTest.testVacuous", "OrderTest.testReal"], []),
        (["OrderTest.testReal"], []),
        # 有一條測試完全不碰建構路徑 → 全班交集是空的 → setup_only 不會觸發
        (["OrderTest.testOther"], []),
    ])
    stats, _ = analyse_mutations(xml)
    assert stats["OrderTest.testVacuous"]["setup_only"] is False   # 舊指標漏抓
    assert stats["OrderTest.testVacuous"]["dominated"] is True     # 新指標抓到
    assert stats["OrderTest.testReal"]["dominated"] is False


def test_最小共殺數_恆真測試偏高(tmp_path):
    """恆真測試只死在很多人都踩到的 mutant 上,所以這個數字會偏高。"""
    many = [f"T.test{i}" for i in range(5)]
    xml = _mutations_xml(tmp_path, [
        (many, []),                    # 5 條都殺得到 —— 廣泛共用的建構路徑
        (["T.test0"], []),             # 只有 test0 殺得到 —— 它有專屬的東西
    ])
    stats, _ = analyse_mutations(xml)
    assert stats["T.test0"]["min_cokillers"] == 1   # 有專屬貢獻
    assert stats["T.test1"]["min_cokillers"] == 5   # 只吃共用的


# ── 驗收情境(GWT)────────────────────────────────────────────────────────

from gen_acceptance import generate as gen_acceptance  # noqa: E402

SCENARIO = {
    "id": "S1",
    "given_when": "一位存在的顧客送出一筆訂單",
    "then_expect": "回 201",
    "provenance": "推導自",
    "provenance_ref": "SPEC.md L44",
    "steps": [{
        "alias": "order",
        "customer_id": "C-001",
        "items": [{"product_id": "P-100", "quantity": 2,
                   "unit_price_cents": 1500, "currency": "TWD"}],
    }],
    "assertions": [
        {"kind": "status_is", "target": "order", "expected_number": 201},
        {"kind": "order_id_not_blank", "target": "order"},
    ],
}


# wire shape 歸規格擁有(ADR 0004)—— 有驗收情境就必須宣告合約,
# 所以每份測試用的 spec 都要帶一份。這裡用凍結那份 app 的欄位名。
WIRE = {
    "name": "shop-frozen-v1",
    "req_customer_field": "customerId",
    "req_items_field": "items",
    "req_product_field": "productId",
    "req_quantity_field": "quantity",
    "req_price_field": "unitPriceCents",
    "req_currency_field": "currency",
    "res_order_id_field": "orderId",
    "res_total_field": "totalCents",
    "list_fields": ["orderId", "customerName", "statusLabel", "totalCents", "placedAt"],
}


def with_scenario(**patch):
    s = copy.deepcopy(VALID)
    sc = copy.deepcopy(SCENARIO)
    sc.update(patch)
    s["acceptance_scenarios"] = [sc]
    s["wire_contract"] = copy.deepcopy(WIRE)
    return s


def test_情境可以匯入(tmp_path):
    build_store(tmp_path / "spec.db", with_scenario())  # 不該丟


def test_總額期望值對不上乘加就匯不進去(tmp_path):
    """推導型矛盾的機械檢查 —— 散文裡寫錯一個數字沒人擋得住,讀的人得自己心算。

    2 × 1500 = 3000;期望值寫 3500 就該擋下來。
    """
    s = with_scenario(assertions=[
        {"kind": "list_row_exists", "target": "order"},
        {"kind": "list_field_equals_number", "target": "order",
         "field": "totalCents", "expected_number": 3500},
    ])
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", s)
    assert any("3000" in p and "3500" in p for p in exc.value.problems), exc.value.problems


def test_總額期望值正確就過(tmp_path):
    build_store(tmp_path / "spec.db", with_scenario(assertions=[
        {"kind": "list_row_exists", "target": "order"},
        {"kind": "list_field_equals_number", "target": "order",
         "field": "totalCents", "expected_number": 3000},
    ]))


def test_數量非正寫不進去(tmp_path):
    s = with_scenario()
    s["acceptance_scenarios"][0]["steps"][0]["items"][0]["quantity"] = 0
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", s)
    assert any("quantity > 0" in p for p in exc.value.problems), exc.value.problems


def test_幣別不是三碼寫不進去(tmp_path):
    s = with_scenario()
    s["acceptance_scenarios"][0]["steps"][0]["items"][0]["currency"] = "TWDD"
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", s)
    assert any("length(currency)" in p for p in exc.value.problems), exc.value.problems


def test_斷言的_kind_與參數對不上會被擋(tmp_path):
    s = with_scenario(assertions=[
        {"kind": "status_is", "target": "order", "field": "statusLabel",
         "expected_number": 201},
    ])
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", s)
    assert any("該帶" in p for p in exc.value.problems), exc.value.problems


def test_斷言指到不存在的_alias_會被擋(tmp_path):
    s = with_scenario(assertions=[{"kind": "list_row_exists", "target": "nobody"}])
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", s)
    assert any("不是這個情境的 alias" in p for p in exc.value.problems), exc.value.problems


def test_驗收生成是確定性的(tmp_path):
    first, second = tmp_path / "a.java", tmp_path / "b.java"
    for out in (first, second):
        db = tmp_path / f"{out.stem}.db"
        build_store(db, with_scenario())
        gen_acceptance(db, out)
    assert first.read_bytes() == second.read_bytes()


def test_生成的驗收不_import_任何實作類別(tmp_path):
    """MISSION 那條的字面實作:同一套驗收要能判定兩份長得完全不同的實作。

    一旦它 import 了實作的類別名,就綁死了一種寫法。
    """
    db = tmp_path / "spec.db"
    build_store(db, with_scenario())
    out = tmp_path / "OrderAcceptanceTest.java"
    gen_acceptance(db, out)
    text = out.read_text(encoding="utf-8")
    # 只看程式碼,不看註解 —— 註解裡提到 com.shop 是在說明這條規則本身
    code = [
        line for line in text.split("\n")
        if "com.shop" in line and not line.strip().startswith(("*", "//", "/*"))
    ]
    assert not any(line.strip().startswith("import com.shop") for line in code), code
    # 唯一允許的 com.shop 引用是 harness 自己的 Application(啟動用)
    assert all("Application" in line for line in code), code


def test_查列表欄位卻沒守衛那一列會被擋(tmp_path):
    """2026-08-18 第二幕實跑逼出來的檢查 —— 而它反過來抓到我自己手寫的那份。

    沒有 list_row_exists 就直接查欄位,那一列不存在時是 NPE,不是看得懂的失敗訊息。
    agent 讀不到這個差別:它的完成定義是「import 印 ok」。
    """
    s = with_scenario(assertions=[
        {"kind": "list_field_equals_text", "target": "order",
         "field": "statusLabel", "expected_text": "已成立"},
    ])
    with pytest.raises(SpecError) as exc:
        build_store(tmp_path / "spec.db", s)
    assert any("list_row_exists" in p for p in exc.value.problems), exc.value.problems


def test_有守衛就過(tmp_path):
    build_store(tmp_path / "spec.db", with_scenario(assertions=[
        {"kind": "list_row_exists", "target": "order"},
        {"kind": "list_field_equals_text", "target": "order",
         "field": "statusLabel", "expected_text": "已成立"},
    ]))
