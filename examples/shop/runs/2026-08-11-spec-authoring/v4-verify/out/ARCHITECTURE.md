# ARCHITECTURE — 訂單系統

技術棧(工程前提,既定):Java 17、Spring Boot、Spring Data JPA、H2、Gradle。
每條規則標出處:**模板既定**(逐字有據於常備模板/工程前提)或 **本案自決**(附 [Qn] 依據)。

## 常備模板(起筆基礎)

| # | 規則 | 出處 | 機械檢查 |
|---|---|---|---|
| T1 | 三層 package 佈局:`domain/`、`usecase/`、`adapter/` | 模板既定 | ArchUnit(佈局為後續規則的前提) |
| T2 | domain 不 import 框架 | 模板既定 | ArchUnit(模板四條之一) |
| T3 | usecase 不 import 框架 | 模板既定 | ArchUnit(模板四條之一) |
| T4 | domain 不 import 上層 | 模板既定 | ArchUnit(模板四條之一) |
| T5 | usecase 不 import adapter | 模板既定 | ArchUnit(模板四條之一) |
| T6 | build 鎖死依賴 | 模板既定 | Gradle build(不得增刪依賴) |

相依方向:`adapter → usecase → domain`;框架(Spring、JPA)只准出現在 adapter。

## 本案特有規則(追加)

| # | 規則 | 出處 | 機械檢查 |
|---|---|---|---|
| A1 | **顧客資料唯讀**:`CustomerRepository` port 只宣告查詢方法;全系統不得有任何寫入 `customer` 表的 code path,不得有顧客相關端點。 | 本案自決 [Q2][Q14] | 介面層級(port 無寫入方法即編譯期強制);端點面由 A2 的測試涵蓋;介面層級已編譯期強制,不需另立 ArchUnit 規則 |
| A2 | **端點恰好兩個**:`POST /orders`、`GET /orders`,不多不少。 | 本案自決 [Q13] | 指名測試:`EndpointInventoryTest#exactlyTwoEndpoints`(列舉 Spring handler mappings 斷言恰為此二者) |
| A3 | **金額表示**:金額一律 cents 整數(`long`),幣別 ISO 4217 三碼;全系統禁用浮點數表示金額。 | 本案自決 [Q12] | `Money` Value Object 型別強制(編譯期);測試以整數斷言 |
| A4 | **交易邊界在 usecase 層**:建單為單一交易,失敗整筆回滾(原子性,見 SPEC C7)。交易註解等框架機制由 adapter 層組裝提供,usecase 本身不 import 框架(維持 T3)。 | 本案自決 [Q15] | 指名測試:`CreateOrderAtomicityTest#midPersistenceFailureLeavesNoResidue`(SPEC S9) |
| A5 | **顯示值分層**:`OrderStatus` 在 domain 為英文 enum(`CREATED`);中文顯示值「已成立」的轉換只准在 adapter 層。domain/usecase 不得出現中文顯示字串。 | 本案自決 [Q5][Q12] | T2/T4 間接強制(顯示屬呈現關注);`ListOrdersUseCaseTest` 斷言 API 輸出 `statusText="已成立"` |
| A6 | **讀寫佈局**:本案不做 CQRS 分離——訂單量與查詢需求(全列 + 排序)不需要;`ListOrdersUseCase` 直接經 `OrderRepository` 讀。 | 本案自決 [Q11][Q13](列表需求僅全列 + 排序,無更複雜查詢被提出) | 無(結構決定,由 code review 把關) |

## 邊界例外

無。本案沒有需要突破模板四條 ArchUnit 規則的例外;不得為實作方便新增例外。(出處:模板既定 T2–T5 + 本案無 [Qn] 支持任何例外。)
