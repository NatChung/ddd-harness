# ARCHITECTURE — 從常備模板起筆

技術棧(工程前提,既定):Java 17、Spring Boot、Spring Data JPA、H2、Gradle。
每條規則標出處:**「模板既定」**(逐字有據於常備模板/工程前提)或**「本案自決」**(附 [Qn] 依據)。
「機械檢查」欄標注哪些由自動化強制。

## 模板既定(不得動)

| # | 規則 | 機械檢查 | 出處 |
|---|---|---|---|
| R1 | 三層 package 佈局:`domain/`、`usecase/`、`adapter/` | ArchUnit(模板附帶) | 模板既定 |
| R2 | domain 不 import 框架 | ArchUnit 規則 1(模板四條之一) | 模板既定 |
| R3 | usecase 不 import 框架 | ArchUnit 規則 2(模板四條之一) | 模板既定 |
| R4 | domain 不 import 上層;usecase 不 import adapter | ArchUnit 規則 3、4(模板四條之二) | 模板既定 |
| R5 | 依賴鎖死:build 檔(Gradle)已鎖定依賴,不得增刪 | build(模板附帶) | 模板既定 |

## 本案自決(追加規則)

| # | 規則 | 機械檢查 | 出處 |
|---|---|---|---|
| R6 | `CustomerRepository` port 定義於 `domain/`,**只含查詢方法**(依 `CustomerId` 查、查是否存在),不得含任何寫入方法;JPA/H2 讀取實作在 `adapter/`。這是 C10(Customer 唯讀)的結構性保證 | 編譯期結構保證(介面無寫入方法);ArchUnit R2/R4 強制 port 位於 domain 且不碰框架 | 本案自決 [Q2][Q15] |
| R7 | `OrderRepository` port 定義於 `domain/`(儲存、列出全部);JPA/H2 實作在 `adapter/` | ArchUnit R2/R4 | 本案自決 [Q0][Q15] |
| R8 | 狀態中文字面「已成立」是**表現層 mapping**:domain 只持有 `OrderStatus.CREATED` enum,CREATED→「已成立」的轉換只存在於 `adapter/`(回應組裝處)。domain/usecase 內不得出現中文字面 | 指名測試 `OrderImmutabilityTest` 之外另由整合測試 S8 斷言輸出字面;mapping 位置由 code review 把關(無專屬 ArchUnit) | 本案自決 [Q5][Q15] |
| R9 | Money 表示法:金額以該幣別 minor units **整數**持久化與傳輸,全系統不得使用浮點數表示金額 | 整合測試 S1/S2/S8 斷言整數值;型別選擇由 code review 把關 | 本案自決 [Q4][Q15](單位定義見 GLOSSARY「Money」) |
| R10 | Transaction 邊界在 `adapter/` 層:由 adapter 的進入點(如 controller 或 adapter 內包裹 usecase 的 Spring bean)以 `@Transactional` 包住一次 PlaceOrder 呼叫——因 R3(usecase 不 import 框架),`@Transactional` 不得出現在 usecase/domain。此為 C9(失敗不留殘骸)的實作手段 | ArchUnit R2/R3 強制註解不進 domain/usecase;行為由 `PlaceOrderAtomicityTest`(S10)強制 | 本案自決 [Q15] |
| R11 | 讀寫佈局:本案不做 CQRS 分離——ListOrders 直接經 `OrderRepository` 讀,不另建 read model(規模不需要) | 無機械檢查(結構簡單性,由 code review 把關) | 本案自決 [Q15] |
| R12 | 時間來源可注入:下單時間取自注入的 `Clock`(port 於 domain/usecase 可見處),不得直接呼叫 `Instant.now()` 之類靜態時間——S8 排序測試需要可控時間 | 測試層面由 S8 強制(需能造出指定下單時間);ArchUnit R2/R3 擋框架但不擋 JDK 靜態呼叫,故另由 code review 把關 | 本案自決 [Q13][Q15] |

## 邊界例外

無。本案沒有任何規則需要豁免模板四條 ArchUnit;若實作中發現非例外不可,停下並記入 ASSUMPTIONS.md(見 PROMPT.md),不得自行放寬。
