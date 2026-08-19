#!/usr/bin/env python3
"""SQLite store → ArchitectureTest.java(第 2 階的機械檢查)。

第 14 題的生成器。目前認三種規則形狀(見 KIND_IMPORTS / generate 的 kinds):
    archunit_forbidden_dependency   package → 不得依賴哪些 package
    archunit_forbidden_annotation   package 底下的類別與成員 → 不得掛哪些 package 的 annotation
    archunit_forbidden_return_type  package × 類名字尾 → public 方法不得回傳哪些 package 的型別

生成後把「由誰強制」回填進 store 的 enforced_by —— 8/13 題 2 要的「指名那條測試」
因此不需要人手寫,也不可能寫錯:誰生成的,誰知道自己生了什麼。

輸出是**確定性**的(無時間戳、無隨機、排序固定),否則 verifyGenerated 每次都會 diff。

離開碼:
    0  生成了
    2  用法錯誤(參數個數不對)
    3  **不適用** —— 不是通過,也不是錯誤。**兩種成因**:
       (a) 這份 store 裡沒有生成得出來的規則;
       (b) 有規則,但 from 側各值**推不出共同的點號分段前綴**,決定不了
           `importPackages` 的根。
       兩種都走 `NothingToGenerate`,**不是 `SystemExit`** —— 後者會把 import
       它的呼叫方(`verify_generated.py`)整支打死。
       (b) 歸「不適用」是沿用 `package_landing_check` 的先例,不是新語意。

用法:
    python3 gen_archunit.py <spec.db> <out/ArchitectureTest.java>
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from spec_store import NothingToGenerate  # noqa: E402

CLASS_NAME = "ArchitectureTest"

BASE_IMPORTS = [
    "com.tngtech.archunit.core.domain.JavaClasses",
    "com.tngtech.archunit.core.importer.ClassFileImporter",
    "com.tngtech.archunit.core.importer.ImportOption",
    "org.junit.jupiter.api.BeforeAll",
    "org.junit.jupiter.api.DisplayName",
    "org.junit.jupiter.api.Test",
]

# 只在真的用到那個 kind 時才 import —— 生成物是要給人 review 的,不該帶死 import
KIND_IMPORTS: dict[str, tuple[list[str], list[str]]] = {
    "archunit_forbidden_dependency": (
        [],
        ["com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses"],
    ),
    "archunit_forbidden_annotation": (
        [
            "com.tngtech.archunit.core.domain.JavaAnnotation",
            "com.tngtech.archunit.core.domain.JavaClass",
            "com.tngtech.archunit.core.domain.JavaMember",
            "com.tngtech.archunit.lang.ArchCondition",
            "com.tngtech.archunit.lang.ConditionEvents",
            "com.tngtech.archunit.lang.SimpleConditionEvent",
        ],
        ["com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses"],
    ),
    "archunit_forbidden_return_type": (
        [],
        [
            "com.tngtech.archunit.core.domain.JavaClass.Predicates.resideInAnyPackage",
            "com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noMethods",
        ],
    ),
}

HEADER = """package architecture;

__IMPORTS__

/**
 * 生成物 —— 由 tools/harness/gen_archunit.py 從 spec store 產生。
 *
 * <p><b>不要手改這個檔案。</b>改了 {@code ./gradlew verifyGenerated} 會 fail:
 * 它會重新生成一次,跟 commit 的內容比。要改規則就改 spec,重新生成。
 *
 * <p>這幾條是第 9 課階梯的第 2 階 —— 相依性原則以「違反就 fail」的形式存在,
 * 不是以「文件裡的一句話」的形式存在。
 *
 * <p>{@code allowEmptyShould(true)} 是刻意的:骨架階段 {@code domain/} 還是空的,
 * 規則沒有東西可查也算過 —— 骨架的紅燈只能來自驗收,不該來自這裡。
 */
@DisplayName("機械檢查:相依性原則(生成物)")
class __CLASS_NAME__ {

    private static JavaClasses classes;

    @BeforeAll
    static void importClasses() {
        classes = new ClassFileImporter()
                .withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS)
                .importPackages("__BASE_PACKAGE__");
    }
"""

DEPENDENCY_TEST = """
    /** {rule_id} —— 來源:{provenance} {provenance_ref} */
    @Test
    @DisplayName("{rule_id}: {display}")
    void rule_{rule_id}() {{
        noClasses().that().resideInAPackage("{from_package}")
                .should().dependOnClassesThat().resideInAnyPackage(
{values})
                .allowEmptyShould(true)
                .check(classes);
    }}
"""

ANNOTATION_TEST = """
    /** {rule_id} —— 來源:{provenance} {provenance_ref} */
    @Test
    @DisplayName("{rule_id}: {display}")
    void rule_{rule_id}() {{
        noClasses().that().resideInAPackage("{from_package}")
                .should(annotatedWithAnythingIn(
{values}))
                .allowEmptyShould(true)
                .check(classes);
    }}
"""

# 注意 from 是「package × 類名字尾」而不是單純 package:JpaOrderRepository 也住 adapter,
# 而它本來就該回傳 Order。整層禁掉會擋錯人。
RETURN_TYPE_TEST = """
    /** {rule_id} —— 來源:{provenance} {provenance_ref} */
    @Test
    @DisplayName("{rule_id}: {display}")
    void rule_{rule_id}() {{
        noMethods().that().areDeclaredInClassesThat().resideInAPackage("{from_package}")
                .and().areDeclaredInClassesThat().haveSimpleNameEndingWith("{class_name_suffix}")
                .and().arePublic()
                .should().haveRawReturnType(resideInAnyPackage(
{values}))
                .allowEmptyShould(true)
                .check(classes);
    }}
"""

# 只有出現 annotation 規則時才生成。ArchUnit 沒有現成的「掛了這些 package 底下
# 任一 annotation」條件 —— beAnnotatedWith 只吃單一型別,列舉型別名是白名單式的
# 不完整(漏一個 @Embeddable 就穿了),所以用 package 前綴自己寫一條。
#
# **刻意連 member 一起查。** 類別層級只看得到 @Entity;把 @Column / @Id / @JsonProperty
# 掛在欄位上一樣是「領域物件直接當持久化模型」,而那才是輪 1 實際出現的樣子。
ANNOTATION_HELPER = """
    /**
     * 「指定 package 底下的類別(含其欄位、方法、建構子)掛了這些 package 的 annotation」。
     *
     * <p>搭配 {@code noClasses()} 使用 —— 條件成立即為違反。
     */
    private static ArchCondition<JavaClass> annotatedWithAnythingIn(String... packagePatterns) {
        return new ArchCondition<JavaClass>(
                "be annotated with an annotation in " + String.join(", ", packagePatterns)) {
            @Override
            public void check(JavaClass item, ConditionEvents events) {
                for (JavaAnnotation<?> annotation : item.getAnnotations()) {
                    reportIfForbidden(events, item, item.getName(), annotation, packagePatterns);
                }
                for (JavaMember member : item.getMembers()) {
                    for (JavaAnnotation<?> annotation : member.getAnnotations()) {
                        reportIfForbidden(
                                events, item, member.getFullName(), annotation, packagePatterns);
                    }
                }
            }
        };
    }

    private static void reportIfForbidden(
            ConditionEvents events,
            JavaClass owner,
            String where,
            JavaAnnotation<?> annotation,
            String[] packagePatterns) {
        String annotationPackage = annotation.getRawType().getPackageName();
        for (String pattern : packagePatterns) {
            String prefix = pattern.endsWith("..")
                    ? pattern.substring(0, pattern.length() - 2)
                    : pattern;
            if (annotationPackage.equals(prefix) || annotationPackage.startsWith(prefix + ".")) {
                events.add(SimpleConditionEvent.satisfied(
                        owner, where + " is annotated with " + annotation.getRawType().getName()));
                return;
            }
        }
    }
"""


def _java_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _base_package(from_packages: list[str]) -> str:
    """所有來源 package 的最長共同前綴,例:com.shop.domain.. + com.shop.usecase.. → com.shop

    確定性、不用額外設定欄位。單一規則時退回它自己去掉尾綴的 package。
    """
    segment_lists = [pkg.rstrip(".").split(".") for pkg in from_packages]
    common: list[str] = []
    for segments in zip(*segment_lists):
        if len(set(segments)) != 1:
            break
        common.append(segments[0])
    if not common:
        # ⚠️ **不是 `SystemExit`**,理由同 `generate()` 裡那條:這支是被
        #    `verify_generated.py` import 進來當函式呼叫的(2026-08-19 實測:
        #    stdout 一行都沒印、exit 1,跟「生成物漂了」長得一模一樣,而且
        #    **另外那個生成器也一起停擺**)。
        #    歸類沿用 `package_landing_check` 的先例:「推不出共同前綴」在那支是
        #    整份**不適用**(離開碼 3)——(c) 宣告全是萬用字元比不了,同一種形狀
        #    ——**不是錯誤**。這裡不另外發明一套語意。
        raise NothingToGenerate(
            "來源 package 沒有共同前綴,決定不了 importPackages 的根 —— "
            "有規則,但這份 store 生不出檔"
        )
    return ".".join(common)


def generate(db_path: str | Path, out_path: str | Path) -> dict[str, str]:
    """產生 Java 檔,並把 enforced_by 回填。回傳 {rule_id: enforced_by}。"""
    # kind → (參數表, 值欄位, Java 樣板)
    kinds = {
        "archunit_forbidden_dependency": (
            "forbidden_dependency",
            "to_package",
            DEPENDENCY_TEST,
        ),
        "archunit_forbidden_annotation": (
            "forbidden_annotation",
            "annotation_package",
            ANNOTATION_TEST,
        ),
        "archunit_forbidden_return_type": (
            "forbidden_return_type",
            "return_package",
            RETURN_TYPE_TEST,
        ),
    }

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rules = conn.execute(
            "SELECT id, rule, provenance, provenance_ref, enforcement FROM architecture_rule "
            # length 再 id:A1..A9 排在 A10 之前。純字典序會排成 A1, A10, A2 —— 
            # 確定性一樣有,但生成物是要給人讀的
            f"WHERE enforcement IN ({','.join('?' * len(kinds))}) "
            "ORDER BY length(id), id",
            tuple(kinds),
        ).fetchall()
        if not rules:
            # ⚠️ **不是 `SystemExit`**:這支是被 `verify_generated.py` import 進來當
            #    函式呼叫的,`SystemExit` 會連帶把它整支打死(2026-08-18 實測:
            #    drift check stdout 一行都沒印、exit 1)。「沒東西可生成」是**不適用**,
            #    要讓呼叫方分得出來、並且照樣去比對**其他**生成器的產物。
            raise NothingToGenerate("store 裡沒有生成得出來的規則,沒有東西可生成")

        # SELECT * → 每個 kind 的參數欄位直接變成樣板的具名欄位,加新 kind 不用改這裡
        params: dict[str, list[sqlite3.Row]] = {}
        for table, _, _ in kinds.values():
            for row in conn.execute(f"SELECT * FROM {table} ORDER BY rule_id, seq"):  # noqa: S608
                params.setdefault(row["rule_id"], []).append(row)

        from_packages = [params[r["id"]][0]["from_package"] for r in rules]
        used_kinds = {r["enforcement"] for r in rules}
        plain, static = set(BASE_IMPORTS), set()
        for kind in used_kinds:
            kind_plain, kind_static = KIND_IMPORTS[kind]
            plain.update(kind_plain)
            static.update(kind_static)
        imports = "\n".join(f"import {i};" for i in sorted(plain))
        imports += "\n\n" + "\n".join(f"import static {i};" for i in sorted(static))

        # 用 replace 而非 format:HEADER 的 javadoc 含 {@code …},會被 format 當成欄位名
        body = (
            HEADER.replace("__IMPORTS__", imports)
            .replace("__CLASS_NAME__", CLASS_NAME)
            .replace("__BASE_PACKAGE__", _base_package(from_packages))
        )

        enforced: dict[str, str] = {}
        for rule in rules:
            rows = params[rule["id"]]
            _, value_column, template = kinds[rule["enforcement"]]
            value_lines = ",\n".join(
                f'                        "{_java_string(r[value_column])}"' for r in rows
            )
            scalars = {
                key: _java_string(rows[0][key])
                for key in rows[0].keys()
                if key not in {"rule_id", "seq", value_column}
            }
            body += template.format(
                rule_id=rule["id"],
                display=_java_string(rule["rule"]),
                provenance=rule["provenance"],
                provenance_ref=_java_string(rule["provenance_ref"]),
                values=value_lines,
                **scalars,
            )
            enforced[rule["id"]] = f"{CLASS_NAME}.rule_{rule['id']}"

        # helper 只在真的有 annotation 規則時才生成 —— 否則會是一段沒人叫的死碼
        if "archunit_forbidden_annotation" in used_kinds:
            body += ANNOTATION_HELPER
        body += "}\n"

        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        for rule_id, enforced_by in enforced.items():
            conn.execute(
                "UPDATE architecture_rule SET enforced_by = ? WHERE id = ?",
                (enforced_by, rule_id),
            )
        conn.commit()
        return enforced
    finally:
        conn.close()


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        enforced = generate(argv[1], argv[2])
    except NothingToGenerate as exc:
        # 3 = 不適用,跟「用法錯誤」(2)分得開。原本這裡是 `SystemExit` 的 1,
        # 而 1 在這條線上是「有問題/有漂移」—— 兩件事共用一個碼就分不出來了。
        print(f"不適用(不是通過):{exc}", file=sys.stderr)
        return 3
    print(f"ok: {argv[2]}")
    for rule_id, enforced_by in sorted(enforced.items()):
        print(f"  {rule_id} 由 {enforced_by} 強制")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
