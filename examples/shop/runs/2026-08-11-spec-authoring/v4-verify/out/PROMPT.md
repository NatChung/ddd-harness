# PROMPT — 給實作 agent 的工作契約

你是實作 agent。依本 spec 包實作訂單系統。技術棧:Java 17、Spring Boot、Spring Data JPA、H2、Gradle(公司常備 starter 模板起步)。

## 凍結清單(不得修改的檔案)

- `GLOSSARY.md`、`SPEC.md`、`ARCHITECTURE.md`、`PROMPT.md`、`INTERVIEW-LOG.md`(本 spec 包五份)
- starter 模板既有檔案:Gradle build 檔(依賴鎖死,不得增刪依賴)、模板附帶的四條 ArchUnit 規則測試

發現 spec 有矛盾或錯誤:停下回報,不得自行改 spec。

## 要填的範圍

- `src/main/java` 下的 `domain/`、`usecase/`、`adapter/` 三層(佈局照 ARCHITECTURE T1)
- `src/test/java` 下的測試,至少含:
  - SPEC S1–S9 每條情境一比一對應的自動化測試
  - SPEC 契約表 C1–C8 的全部指名測試(測試類/方法名照表,含 `CreateOrderAtomicityTest#midPersistenceFailureLeavesNoResidue`、`OrderImmutabilityTest#orderExposesNoMutatingMethods`、`EndpointInventoryTest#exactlyTwoEndpoints`)
- 測試用的顧客表預置資料(H2;顧客資料唯讀,只准測試 fixture 預置,見 ARCHITECTURE A1)

## 硬規則

- 命名一律照 `GLOSSARY.md`,禁用同義詞清單零容忍。
- 端點恰好兩個(SPEC 端點清單),SPEC「明確不在範圍」列的每一項:不要做。
- 金額一律 cents 整數,禁浮點(ARCHITECTURE A3)。
- S9 的原子性測試不得空洞通過:必須先斷言模擬的中途失敗確實被觸發,再實查資料庫斷言零殘留。

## 完成的定義

**測試全綠**:模板四條 ArchUnit 規則 + 本 spec 全部情境測試與指名測試,一次 `./gradlew test` 全部通過。

## 歧義處理

spec 沒寫到的實作細節:自決,並**逐條記入 `ASSUMPTIONS.md`**(新建於輸出根目錄;每條寫:遇到的歧義、你的決定、理由)。與 spec 牴觸的自決不允許——牴觸就是回報,不是假設。
