# PROMPT — 給實作 agent 的工作契約

你是實作 agent。依本 spec 包(GLOSSARY.md、SPEC.md、ARCHITECTURE.md)實作下單系統。
技術棧已定:Java 17、Spring Boot、Spring Data JPA、H2、Gradle,從公司常備 starter 起步。

## 凍結清單(不得修改的檔案)

- `GLOSSARY.md`、`SPEC.md`、`ARCHITECTURE.md`、`PROMPT.md`、`INTERVIEW-LOG.md`(本 spec 包五份)
- starter 內建的四條通用 ArchUnit 規則測試檔(不得修改、不得刪除、不得弱化)
- `build.gradle` / `settings.gradle` 及依賴鎖定(不得新增或移除依賴)

## 要填的範圍

- `src/main/java/**` 之下,依 ARCHITECTURE 的 `domain/ usecase/ adapter/` 三層佈局實作
- `src/test/java/**`:實作 SPEC 指名的全部測試(測試類別名必須與 SPEC 一字不差):
  `OrderImmutabilityTest`、`PlaceOrderRejectsEmptyLinesTest`、`PlaceOrderRejectsUnknownCustomerTest`、
  `PlaceOrderRejectsInvalidQuantityTest`、`PlaceOrderRejectsNegativeUnitPriceTest`、
  `PlaceOrderRejectsBadCurrencyFormatTest`、`PlaceOrderAtomicityTest`、`OrderTotalCalculationTest`、
  `OrderStatusDisplayTest`、`ListOrdersContentAndSortingTest`、`ListOrdersEmptyTest`
- 測試 fixture:`customers` 表預載 `("C001", "王小明")`、`("C002", "李大同")`(SPEC 共同 Given)

## 硬性約束(重申,違反即未完成)

- 命名一律照 GLOSSARY,禁用同義詞清單一個都不准出現。
- 端點只有 `POST /orders`、`GET /orders`,不多不少。
- SPEC「明確不在範圍」列出的每一項:不要做。
- 每條失敗路徑(SPEC S3–S8)必須驗證「不留殘骸」:失敗後訂單數不變、無孤兒 order_lines。

## 完成的定義

`./gradlew test` 全綠——含 starter 四條 ArchUnit 規則 + 上列全部指名測試。測試紅著就是沒完成。

## 歧義處理

遇到 spec 未載明的細節:**自決,不回頭問**,但每一條決定逐條記入 `ASSUMPTIONS.md`
(格式:決定內容 + 為何 spec 沒涵蓋 + 你選的理由)。與 spec 衝突的自決無效——spec 優先。
