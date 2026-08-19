package architecture;

import com.tngtech.archunit.core.domain.JavaAnnotation;
import com.tngtech.archunit.core.domain.JavaClass;
import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.domain.JavaMember;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.lang.ArchCondition;
import com.tngtech.archunit.lang.ConditionEvents;
import com.tngtech.archunit.lang.SimpleConditionEvent;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static com.tngtech.archunit.core.domain.JavaClass.Predicates.resideInAnyPackage;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noMethods;

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
class ArchitectureTest {

    private static JavaClasses classes;

    @BeforeAll
    static void importClasses() {
        classes = new ClassFileImporter()
                .withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS)
                .importPackages("com.shop");
    }

    /** A1 —— 來源:推導自 examples/shop/spec/ARCHITECTURE.md L19 */
    @Test
    @DisplayName("A1: domain/ 不得 import 任何框架(Spring、JPA、Jackson)")
    void rule_A1() {
        noClasses().that().resideInAPackage("com.shop.domain..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "org.springframework..",
                        "jakarta.persistence..",
                        "jakarta.transaction..",
                        "com.fasterxml.jackson..")
                .allowEmptyShould(true)
                .check(classes);
    }

    /** A2 —— 來源:推導自 examples/shop/spec/ARCHITECTURE.md L20 */
    @Test
    @DisplayName("A2: usecase/ 不得 import 任何框架(Spring、JPA、Jackson)")
    void rule_A2() {
        noClasses().that().resideInAPackage("com.shop.usecase..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "org.springframework..",
                        "jakarta.persistence..",
                        "jakarta.transaction..",
                        "com.fasterxml.jackson..")
                .allowEmptyShould(true)
                .check(classes);
    }

    /** A3 —— 來源:推導自 examples/shop/spec/ARCHITECTURE.md L21 */
    @Test
    @DisplayName("A3: domain/ 不得 import usecase/ 或 adapter/(內層不知道外層)")
    void rule_A3() {
        noClasses().that().resideInAPackage("com.shop.domain..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "com.shop.usecase..",
                        "com.shop.adapter..")
                .allowEmptyShould(true)
                .check(classes);
    }

    /** A4 —— 來源:推導自 examples/shop/spec/ARCHITECTURE.md L22-23 */
    @Test
    @DisplayName("A4: usecase/ 不得 import adapter/(介面宣告在內層,實作在外層 —— 相依性倒轉)")
    void rule_A4() {
        noClasses().that().resideInAPackage("com.shop.usecase..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "com.shop.adapter..")
                .allowEmptyShould(true)
                .check(classes);
    }

    /** A6 —— 來源:推導自 examples/shop/spec/ARCHITECTURE.md L28-30 */
    @Test
    @DisplayName("A6: 領域物件不得直接作為 JPA entity —— domain/ 的類別與其成員不得掛任何 JPA/Jackson annotation")
    void rule_A6() {
        noClasses().that().resideInAPackage("com.shop.domain..")
                .should(annotatedWithAnythingIn(
                        "jakarta.persistence..",
                        "com.fasterxml.jackson.."))
                .allowEmptyShould(true)
                .check(classes);
    }

    /** A10 —— 來源:推導自 examples/shop/spec/ARCHITECTURE.md L42-43 */
    @Test
    @DisplayName("A10: Controller 的 public 方法不得回傳 domain/ 型別;HTTP 回應一律用 usecase 的 View Model 或 adapter 自己的 response 物件")
    void rule_A10() {
        noMethods().that().areDeclaredInClassesThat().resideInAPackage("com.shop.adapter..")
                .and().areDeclaredInClassesThat().haveSimpleNameEndingWith("Controller")
                .and().arePublic()
                .should().haveRawReturnType(resideInAnyPackage(
                        "com.shop.domain.."))
                .allowEmptyShould(true)
                .check(classes);
    }

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
}
