# GLOSSARY — Ubiquitous Language

> **命名鐵律:實作命名必須照此表,不得另創同義詞。**
> 程式中的類別名、方法名、欄位名、測試名,凡對應下表概念者,一律使用表中英文名。
>
> **禁用同義詞清單**(出現即違規):
> - `Purchase` / `Booking` / `Deal` →(一律用)`Order`
> - `OrderItem` / `LineItem` / `Item` / `Detail` → `OrderLine`
> - `Client` / `Member` / `User` / `Buyer` → `Customer`
> - `Price` / `Cost` / `Fee` → `UnitPrice`(單價)或 `TotalAmount`(總額)
> - `Amount` 單獨使用 → `Money`(帶幣別)或 `TotalAmount`
> - `CurrencyCode` / `Ccy` → `Currency`
> - `CreatedAt` / `OrderDate` / `Timestamp` → `PlacedAt`
> - `State` / `Phase` → `OrderStatus`
> - `SubmitOrder` / `CreateOrder` / `MakeOrder` → `PlaceOrder`
> - `GetOrders` / `FetchOrders` / `QueryOrders` → `ListOrders`

| 詞(英文名) | 中文 | 型態(DDD) | 定義 | 所屬層 | 回鏈 |
|---|---|---|---|---|---|
| `Order` | 訂單 | Aggregate Root | 客人一次下單的成立結果;成立即鎖定,不提供任何變更方法 | domain | [Q0][Q1] |
| `OrderLine` | 訂單明細 | Value Object(隸屬 Order aggregate) | 訂單內一條購買項:`ProductName` + `Quantity` + `UnitPrice`;不單獨存在 | domain | [Q7][Q8] |
| `Customer` | 顧客 | 唯讀參照資料(external read model,非本系統 aggregate) | CRM 維護的顧客;本系統只讀,欄位僅 `CustomerId` + `CustomerName` | domain(唯讀) | [Q2][Q3] |
| `CustomerId` | 顧客編號 | Value Object | 顧客在 CRM 表中的識別字串;下單時必須指到已存在的顧客 | domain | [Q3][Q10] |
| `CustomerName` | 顧客姓名 | Value Object(字串) | CRM 表中的姓名;列表「誰買的」顯示此欄 | domain | [Q3][Q5] |
| `Money` | 金額 | Value Object | 一個金額 = 整數(**一律最小貨幣單位 cents,整數,禁止浮點/小數**)+ `Currency` | domain | [Q4][Q13] |
| `Currency` | 幣別 | Value Object | 3 個大寫英文字母代碼(ISO 4217 形式,只驗格式);一張訂單只有一個,定義在 Order 層 | domain | [Q4][Q13] |
| `Quantity` | 數量 | Value Object(整數) | 明細購買數量;整數,≥ 1 | domain | [Q7][Q11] |
| `UnitPrice` | 單價 | Value Object | 明細單價,cents 整數,≥ 0;幣別隨所屬 Order | domain | [Q7][Q11][Q13] |
| `ProductName` | 商品名稱 | Value Object(字串) | 明細的商品名;不對照商品主檔(字串內容驗證屬規格沉默,實作自決記 ASSUMPTIONS.md) | domain | [Q8] |
| `TotalAmount` | 總額 | 導出值(derived Value Object,型態為 Money) | 系統計算:Σ(每條明細 `Quantity` × `UnitPrice`);外部不得傳入 | domain | [Q7] |
| `OrderStatus` | 訂單狀態 | Value Object(enum) | 本版唯一值 `CREATED`;對外顯示一律中文「已成立」 | domain(顯示轉換在 adapter) | [Q5][Q13] |
| `OrderId` | 訂單編號 | Value Object | 系統產生的不透明字串識別 | domain | [Q13] |
| `PlacedAt` | 下單時間 | Value Object(時間) | 系統於下單當下取得;**UTC、ISO-8601 表示**(例 `2026-08-11T03:00:00Z`) | domain | [Q5][Q13] |
| `PlaceOrder` | 下單 | Use Case | 收下單請求 → 驗證 → 成立 Order → 持久化;單一交易,全有全無 | usecase | [Q0][Q9] |
| `ListOrders` | 查詢所有訂單 | Use Case | 回傳全部訂單的列表列(姓名、狀態、總額、下單時間),新到舊 | usecase | [Q0][Q5][Q13] |
| `OrderRepository` | 訂單儲存庫 | Repository | Order aggregate 的持久化介面(存、全撈) | domain 定義介面 / adapter 實作 | [Q0] |
| `CustomerRepository` | 顧客儲存庫 | Repository(**唯讀**) | 只有查詢方法(依 `CustomerId` 找 Customer);不得有任何寫入方法 | domain 定義介面 / adapter 實作 | [Q2][Q3] |

## 量值表示法(定死,無歧義)

| 量值 | 單位/表示法 | 回鏈 |
|---|---|---|
| 金額(UnitPrice、TotalAmount) | 最小貨幣單位(cents)整數;例:USD $25.00 = `2500` | [Q13] |
| 幣別 | 3 個大寫英文字母,例 `USD` | [Q4][Q13] |
| 數量 | 整數,≥ 1 | [Q11] |
| 時間 | UTC,ISO-8601 字串 | [Q13] |
| 狀態顯示 | API 回應中一律中文字串「已成立」 | [Q5][Q13] |
