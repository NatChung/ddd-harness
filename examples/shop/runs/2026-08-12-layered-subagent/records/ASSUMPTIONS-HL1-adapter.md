# 實作假設(Adapter 層)

## 1. 持久化模型設計

### 表結構
- `orders` 表：存儲 Order aggregate，欄位包括：
  - `order_id` (PK, VARCHAR): 訂單編號（由 OrderId 提供的 UUID 字串）
  - `customer_id` (FK, VARCHAR): 顧客編號（由 CustomerId 提供）
  - `status` (VARCHAR): 訂單狀態（DRAFT / PLACED）
  - `placed_at` (DATE): 下單日期（usecase 供給的 LocalDate）

- `order_items` 表：存儲 OrderItem，欄位包括：
  - `order_item_id` (PK, auto-increment)
  - `order_id` (FK): 所屬訂單
  - `product_id` (VARCHAR): 商品編號
  - `quantity` (INT): 數量
  - `unit_price_cents` (LONG): 單價（分單位）
  - `currency` (VARCHAR): 幣別

### JPA Entity 設計
- `OrderEntity`: 對應 Order domain 物件，宣告 `@Table("orders")`，持有 `OrderItemEntity` 的 List
- `OrderItemEntity`: 對應 OrderItem domain 物件，宣告 `@Table("order_items")`
- 不會建立 Customer entity（顧客資料由 harness 的 data.sql 供給，查詢時直接 SQL join）

## 2. Repository 實作策略

### JpaOrderRepository (實作 OrderRepository)
- 依賴 Spring Data JPA 的底層 CrudRepository
- `save(Order, LocalDate)` 方法：
  1. 將 Order aggregate 轉換為 OrderEntity（包括其 OrderItem 明細）
  2. 設置 placedAt 日期
  3. 呼叫 JPA save
  
### JpaOrderQueryRepository (實作 OrderQueryRepository)
- `findAllOrders()` 方法：
  1. 使用 JPQL 或 native SQL 直接組出 OrderListItem view model
  2. JOIN `orders` 與 `customers` 表
  3. 聚合計算總金額（SUM of quantity * unitPrice）
  4. 轉換 status 為中文標籤（PLACED → "已成立"）
  5. 轉換 placedAt 為 ISO 日期字串

## 3. HTTP Controller (OrderController)

### `POST /orders` 端點
- 接收 JSON request（含 customerId 和 items 陣列）
- 組裝 PlaceOrderCommand
- 呼叫 PlaceOrderUseCase.placeOrder(...)
- 回傳 201 Created，body 為 `{"orderId": "..."}`

### `GET /orders` 端點
- 呼叫 OrderListUseCase.listOrders()
- 回傳 200 OK，body 為 OrderListItem JSON 陣列

## 4. Spring 組態

使用 `@Configuration` 類別進行 bean 裝配：
- 宣告 PlaceOrderUseCase 和 OrderListUseCase 的 @Bean
- 將 Repository 實作注入 usecase
- 由於 Application 宣告 `@SpringBootApplication`，會自動掃描 `com.shop` 包下的組件

## 5. 資源檔案

- 不修改 `data.sql` 和 `application.properties`（均由 harness 提供）
- 由 JPA 的 `ddl-auto=create-drop` 自動建表（无需另寫 schema.sql）

## 6. 日期處理

- OrderItem 不儲存 placedAt（只在 OrderEntity 層級儲存）
- Query 側從 database 讀出 DATE 後轉換為 ISO 字串格式 `YYYY-MM-DD`

## 7. View Model 轉換

OrderListItem 中的欄位對應：
- `orderId`: Order.getOrderId().getValue()
- `customerName`: 從 customers 表 JOIN 取得（非 Order aggregate 的責任）
- `statusLabel`: Order.getStatus() == PLACED ? "已成立" : "草稿"
- `totalCents`: SUM(quantity * unitPrice) for all items of this order
- `placedAt`: DateTimeFormatter.ISO_DATE.format(Date)

## 8. 內層介面契約

使用 usecase 層已定義的介面（OrderRepository、OrderQueryRepository），
不新增或變動方法簽名。

## 9. 命名慣例

- Entity 類別名稱後綴 `Entity`（如 OrderEntity、OrderItemEntity）
- Repository 實作使用 `Jpa` 前綴（如 JpaOrderRepository）
- Controller 使用 `OrderController` 按詞彙表
- 資料庫表名小寫帶下線（如 `orders`、`order_items`）

## 10. 例外處理

- Controller 層捕捉 usecase 層拋出的 IllegalArgumentException 和 IllegalStateException
- 回傳 400 Bad Request 或 409 Conflict（根據業務規則決定）
- 不在 spec 範圍內的額外例外處理不做

## 11. 幣別標準化

- Money.getCurrency() 回傳的字串已自動轉為大寫（見 Money.java 建構子）
- OrderItemEntity 儲存時保持原樣

## 12. 明細複本保護

- Order.items() 已回傳 List.copyOf（不可改集合）
- OrderEntity 持有的 List<OrderItemEntity> 需確保：
  1. equals/hashCode/lazy-loading 正確（避免 Hibernate 陷阱）
  2. 不暴露可修改的集合給外部
