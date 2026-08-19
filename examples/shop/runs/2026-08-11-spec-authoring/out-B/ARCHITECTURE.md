# ARCHITECTURE — 訂單系統

基底 = 公司常備模板(starter),本文件只寫「模板本身」的摘要 + 本案特有規則。凡標 **[機械檢查]** 者由 ArchUnit / build 強制,其餘由 code review 與測試把關。

## 常備模板(照抄,不改)

技術棧:Java 17、Spring Boot、Spring Data JPA、H2、Gradle(版本鎖死於 starter 的 build,不得自行加依賴)。

### Package 佈局(三層)

```
<root>
├── domain/     # 純領域:Order、OrderItem、Money、Currency、OrderStatus、
│               # Customer、CustomerId、OrderRepository(介面)、CustomerReader(介面)
├── usecase/    # PlaceOrder、ListOrders、OrderSummary
└── adapter/    # Web(Controller、request/response DTO)、
                # Persistence(JPA entity、repository 實作)、CRM 顧客表讀取實作
```

### 相依方向(模板四條通用規則)

1. `domain` 不 import 框架(Spring / JPA / Jakarta 等一律禁止) **[機械檢查:ArchUnit]**
2. `usecase` 不 import 框架 **[機械檢查:ArchUnit]**
3. `domain` 不 import 上層(`usecase`、`adapter`) **[機械檢查:ArchUnit]**
4. `usecase` 不 import `adapter` **[機械檢查:ArchUnit]**

依賴只能由外向內:`adapter → usecase → domain`。build 鎖死依賴清單 **[機械檢查:build]**。

## 本案特有規則(只此追加)

### A1 CRM 顧客資料是唯讀外部邊界

- `Customer` 由 CRM 擁有;本系統以 H2 中一張 `customers` 資料表模擬 CRM 的表(欄位:`customer_id`, `name`),由 seed script 灌測試資料。
- domain 只定義 `CustomerReader` 唯讀介面(只有查詢方法);adapter 提供實作。
- **介面上不得存在任何 save/update/delete 方法;程式碼中不得有任何寫入 `customers` 表的路徑**(含 JPA save、SQL insert/update/delete)。由 code review + 測試把關(ArchUnit 不易表達);若實作方便,可加一條 ArchUnit 自訂規則掃描 `CustomerReader` 實作類不得依賴具寫入能力的 JPA repository 型別。

### A2 寫側/讀側佈局(同一聚合,分開的 use case)

- 寫側:`PlaceOrder` 走完整聚合——建構 `Order`(計算 TotalAmount、驗證 R2/R5)→ `OrderRepository.save`。
- 讀側:`ListOrders` 回 `OrderSummary` 列表(含 join 顧客姓名);讀側可以由 adapter 的查詢直接組 `OrderSummary`,但 `OrderSummary` 型別定義在 `usecase`,欄位名照 GLOSSARY。
- 「已成立」這個顯示文字的對照(`CONFIRMED` → `已成立`)屬展示規則,放在 usecase 的輸出組裝(`OrderSummary.statusText`),不放 Controller,也不進 domain(domain 只有 enum 值)。

### A3 domain 不可變性的落法

- `Order` 一經建構完成即不可變:domain 物件不提供 setter、不提供任何改變明細/金額/狀態的方法 **[機械檢查:可加 ArchUnit 規則——domain package 無 public setter;至少由 code review 把關]**。
- JPA entity(可變、有註解)只存在於 `adapter`;domain 物件與 JPA entity 分開,由 adapter 做雙向轉換。**domain 類別上不得出現任何 JPA/Jakarta 註解 [機械檢查:模板規則 1 已涵蓋]**。

### A4 端點面收斂

- Controller 只映射 SPEC 的兩個端點(POST `/orders`、GET `/orders`),不得多開 **[驗收:SPEC S9 的測試]**。
- 錯誤回應統一 400 + `error` 代碼(`CUSTOMER_NOT_FOUND` / `EMPTY_ITEMS` / `INVALID_QUANTITY` / `INVALID_UNIT_PRICE` / `INVALID_CURRENCY`),對應 domain/usecase 拋出的例外,由 adapter 層的 exception handler 轉譯。

### A5 資料表

| 表 | 歸屬 | 說明 |
|---|---|---|
| `customers` | CRM(模擬,唯讀) | `customer_id`, `name`;seed 資料 |
| `orders` | 本系統 | id、customer_id、currency、status、order_date、total_amount(冗餘存計算結果可,但真值來源是 domain 計算) |
| `order_items` | 本系統 | 隸屬 orders;product_name、quantity、unit_price |

## 機械檢查總表

| 規則 | 工具 |
|---|---|
| 模板四條相依規則 | ArchUnit(starter 內建,凍結) |
| 依賴清單鎖死 | Gradle build(starter 內建,凍結) |
| 兩端點之外無其他訂單端點 | SPEC S9 自動化測試 |
| TotalAmount 由系統算 | SPEC S2 自動化測試 |
| CRM 唯讀 | code review + CustomerReader 介面形狀(無寫方法) |
