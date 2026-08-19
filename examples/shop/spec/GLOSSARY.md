# 詞彙表(Ubiquitous Language)

這份詞彙表是規格的一部分。實作中的類別、方法、欄位命名**必須**使用這裡的詞,
不得另創同義詞(例:不要把 Order 叫成 Purchase、不要把成立叫成 confirm)。

| 詞 | 型態 | 定義 |
|---|---|---|
| `Order` | Aggregate Root | 一筆訂單。一致性邊界:明細與總額永遠一致 |
| `OrderItem` | Aggregate 內部物件 | 訂單的一條明細:商品、數量、單價。只能經由 `Order` 修改 |
| `OrderId` | Value Object | 訂單的識別。以值相等比較 |
| `CustomerId` | Value Object | 顧客的識別。`Order` 只持有 `CustomerId`,**不持有 Customer 物件** |
| `ProductId` | Value Object | 商品的識別 |
| `Money` | Value Object | 金額 = 數值 + 幣別(如 `TWD`)。以值相等比較 |
| `OrderStatus` | 列舉 | 訂單狀態。本規格用到:`DRAFT`(草稿)、`PLACED`(已成立) |
| 下單 / place | 動詞 | 把一筆訂單從草稿變成已成立。成立後明細不可再修改 |
| 已成立 | 狀態的顯示文字 | `PLACED` 在列表頁顯示為「已成立」(`statusLabel`) |
| `OrderRepository` | 介面 | Command 側的儲存介面。**宣告在 usecase 層**,實作在 adapter 層 |
| `OrderQueryRepository` | 介面 | Query 側專用的查詢介面。回傳 View Model,不回傳 `Order` |
| `OrderListItem` | View Model | 列表頁一列的形狀。**定義在 usecase 層** |
| `PlaceOrderUseCase` | Use Case | 下單(Command 側) |
| `OrderListUseCase` | Use Case | 查訂單列表(Query 側) |
| `OrderController` | Adapter | HTTP 進出口。**宣告在 adapter 層** |

## 顧客(Customer)

本系統**沒有** Customer 這個 Aggregate。顧客資料只有一張由外部系統維護的資料表
`customers`(`customer_id`, `name`),啟動時已由 harness 建好並塞入測試資料。
訂單領域對顧客所知的一切,只有 `CustomerId`。
列表頁需要顧客姓名時,由 Query 側自行取得 —— 那是讀取模型的事,不是 `Order` 的事。
