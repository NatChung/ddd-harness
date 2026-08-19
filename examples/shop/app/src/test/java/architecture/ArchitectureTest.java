package architecture;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;

/**
 * 機械檢查(第 9 課階梯的第 2 階)—— 由 harness 提供。**實作者不得修改本檔案。**
 *
 * 這幾條就是第 5 課的相依性原則,以「違反就 fail」的形式存在,
 * 而不是以「文件裡的一句話」的形式存在。
 *
 * 注意這裡刻意用 allowEmptyShould(true):骨架階段 domain/ 還是空的,
 * 規則沒有東西可查也算過 —— 骨架的紅燈只能來自驗收,不該來自這裡。
 */
@DisplayName("機械檢查:第 5 課的相依性原則")
class ArchitectureTest {

    private static JavaClasses classes;

    @BeforeAll
    static void importClasses() {
        classes = new ClassFileImporter()
                .withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS)
                .importPackages("com.shop");
    }

    @Test
    @DisplayName("domain/ 不得 import 任何框架(Spring、JPA、Jackson)")
    void domain層不得依賴框架() {
        noClasses().that().resideInAPackage("com.shop.domain..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "org.springframework..",
                        "jakarta.persistence..",
                        "jakarta.transaction..",
                        "com.fasterxml.jackson..")
                .allowEmptyShould(true)
                .check(classes);
    }

    @Test
    @DisplayName("usecase/ 不得 import 任何框架(Spring、JPA、Jackson)")
    void usecase層不得依賴框架() {
        noClasses().that().resideInAPackage("com.shop.usecase..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "org.springframework..",
                        "jakarta.persistence..",
                        "jakarta.transaction..",
                        "com.fasterxml.jackson..")
                .allowEmptyShould(true)
                .check(classes);
    }

    @Test
    @DisplayName("domain/ 不得 import usecase/ 或 adapter/(內層不知道外層)")
    void domain層不得依賴外層() {
        noClasses().that().resideInAPackage("com.shop.domain..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "com.shop.usecase..",
                        "com.shop.adapter..")
                .allowEmptyShould(true)
                .check(classes);
    }

    @Test
    @DisplayName("usecase/ 不得 import adapter/(介面宣告在內層,實作在外層)")
    void usecase層不得依賴adapter層() {
        noClasses().that().resideInAPackage("com.shop.usecase..")
                .should().dependOnClassesThat().resideInAnyPackage("com.shop.adapter..")
                .allowEmptyShould(true)
                .check(classes);
    }
}
