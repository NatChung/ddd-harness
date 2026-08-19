# 實作任務(給 agent 的固定啟動指令)

你要在 `examples/shop/app/` 這個 Spring Boot 專案裡,實作
`examples/shop/spec/` 規格描述的功能。四份規格文件都要讀:

1. `SPEC.md` —— 功能、端點、情境、領域規則
2. `GLOSSARY.md` —— 詞彙表(命名必須照它)
3. `ARCHITECTURE.md` —— package 佈局與相依規則
4. 本檔 —— 工作方式

## 給你的東西(不得修改)

- `app/build.gradle`、`app/settings.gradle`、Gradle wrapper
- `app/src/main/java/com/shop/Application.java`
- `app/src/main/resources/`(`application.properties`、`data.sql`)
- `app/src/test/java/acceptance/OrderAcceptanceTest.java`(驗收套件)
- `app/src/test/java/architecture/ArchitectureTest.java`(機械檢查)

## 你要寫的東西

`app/src/main/java/com/shop/` 底下的 `domain/`、`usecase/`、`adapter/` 三個
package 的全部內容。不得新增依賴,不得動 harness 的檔案。

## 工作方式

- 在 `examples/shop/app/` 目錄執行 `./gradlew test` 來驗證。
  **完成的定義:全部測試綠**(驗收 + 機械檢查)。
- 你可以自己加單元測試(放 `app/src/test/java/com/shop/` 底下),不強制。
- 規格有歧義或沒講到的地方:**自己做決定,不要問人**,並把每一個這類決定
  記在 `examples/shop/app/ASSUMPTIONS.md`(一行一個:遇到什麼歧義、你選了什麼、為什麼)。
- 如果在合理嘗試後仍無法讓測試全綠:停下來,把目前狀態與卡住的原因寫進
  `ASSUMPTIONS.md` 的最後一節,不要無限重試。
- 完成(或停下)後:`git add` 你動過的檔案並 commit(訊息開頭
  `impl:`),然後回報:測試結果摘要、你做的主要設計決定、ASSUMPTIONS 條數。
