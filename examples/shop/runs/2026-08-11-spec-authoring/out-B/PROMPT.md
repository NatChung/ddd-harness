# PROMPT — 給實作 agent 的工作契約

你是實作 agent。依本目錄的 GLOSSARY.md、SPEC.md、ARCHITECTURE.md,在公司 starter(Java 17 / Spring Boot / Spring Data JPA / H2 / Gradle,三層 package + 四條 ArchUnit 規則 + 鎖死依賴的 build)之上完成訂單系統。

## 凍結清單(不得修改)

- `GLOSSARY.md`、`SPEC.md`、`ARCHITECTURE.md`(本規格包三份文件)
- starter 的 ArchUnit 規則檔(四條通用規則)
- starter 的 Gradle build 檔與依賴清單(不得新增/升版任何依賴)

發現規格衝突或覺得規則不合理:停在 ASSUMPTIONS.md 記錄並照規格字面實作,不得改動凍結檔案。

## 要填的範圍

1. `domain/` — Order、OrderId、OrderItem、Money、Currency、OrderStatus、Customer、CustomerId、OrderRepository(介面)、CustomerReader(唯讀介面);R1–R7 的 invariant 全部落在這層。
2. `usecase/` — PlaceOrder、ListOrders、OrderSummary(含 `CONFIRMED`→「已成立」的顯示文字組裝)。
3. `adapter/` — 兩個端點的 Controller 與 DTO、exception handler(錯誤代碼照 SPEC)、JPA entity 與 repository 實作、`customers` 表的唯讀讀取實作、H2 schema 與 seed。
4. 測試 — SPEC 的 S1–S9 每條情境至少一個自動化測試,一比一對應(測試名稱標注情境編號);另補 domain 單元測試覆蓋 R1–R7。

## 完成的定義

- `./gradlew test` 全綠:S1–S9 情境測試 + domain 測試 + starter 的 ArchUnit 測試,無一跳過(skip/disabled 視同未完成)。
- 端點恰好兩個(SPEC E1、E2),多一個即未完成。
- 命名與 GLOSSARY 完全一致(含「不得出現」清單);顯示文字「已成立」逐字正確。
- SPEC「明確不在範圍」清單內的任何項目都未被實作。

## 歧義自決規則

規格沒說死的(例:orderId 產生方式、日期時間格式細節、DTO 欄位排列、H2 記憶體或檔案模式):**自行決定,不回頭問**,但每一條決定逐條記入 `ASSUMPTIONS.md`(格式:決定、理由、影響面)。「明確不在範圍」的項目不屬於歧義——一律不做,連 ASSUMPTIONS 都不必記,除非你認為缺了會使某條 SPEC 情境無法通過,才記入 ASSUMPTIONS 說明衝突。
