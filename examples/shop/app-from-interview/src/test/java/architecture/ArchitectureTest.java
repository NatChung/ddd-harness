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
 *
 * ⚠️ **空骨架階段這四條全綠,要記成「不適用」而不是「通過」**(ADR 0006 §1,
 *    規矩同 ADR 0005 §6 對譯檢查那條)。每一條的 that() 命中 0 個 class,
 *    綠燈裡沒有任何資訊。一個什麼都不寫的 agent 在這裡是免費綠的。
 *
 * ⚠️ **這一套不是這份規格擁有的,是從凍結骨架繼承來的。** 兩個證據:
 *    (1) 這份 store(runs/2026-08-18-act2-rerun/agent-acceptance.yaml)頂層只有
 *        wire_contract 與 acceptance_scenarios,gen_archunit.py 對它印
 *        「store 裡沒有生成得出來的規則,沒有東西可生成」;
 *    (2) 散文自己寫著(input-SPEC.md L304)「機械檢查(ArchUnit 之類)目前一條都沒有,
 *        架構規則靠人工守;這是已知缺口,不是遺漏」。
 *    → 底下的 package 名 com.shop.domain / usecase / adapter **是這個檔案發明的**,
 *      不是規格宣告的。ADR 0006 §3 那個坑(agent 把 class 放到別的 package,
 *      整套檢查就靜靜地不適用、看起來跟完全遵守一模一樣)在這裡**全開**,
 *      補它的是票 11 的 package 落點檢查,不是這個檔案。
 *
 * ⚠️ 受測品(ADR 0006 §6):改了它後續的跑就不能跟先前比。
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
