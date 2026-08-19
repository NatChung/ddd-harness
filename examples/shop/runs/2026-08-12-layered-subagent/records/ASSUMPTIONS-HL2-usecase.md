# ASSUMPTIONS.md — Usecase 層實作決策

## 1. OrderId 生成責任

**決策**: `PlaceOrderUseCase` 依賴 `OrderRepository` 介面中的生成方法 (`generateOrderId()`)，由 adapter 層實作。

**理由**: OrderId 的生成策略（UUID、自增等）不應耦合在 usecase 層，應由 adapter 層（持久化層）決定。

## 2. Order 的 placedAt 時間戳

**決策**: Order Aggregate 本身不持有 `placedAt`；改由 adapter 層在持久化時記錄。

**理由**: 
- 規格要求「placedAt 是一個 ISO 日期(YYYY-MM-DD)」，只在列表頁回傳，不是 Order 本體的一部分。
- domain 層（Order）的職責是維護訂單的領域規則，不需要知道何時被持久化。
- OrderQueryRepository 在組合 OrderListItem 時，直接從 orders 表的 placed_at 欄位取得。

## 3. OrderListItem 的 placedAt 型別

**決策**: `placedAt` 使用 `java.time.LocalDate` 型別，JSON 序列化時自動轉為 `YYYY-MM-DD` 格式。

**理由**: LocalDate 是標準的日期型別，Spring 會自動序列化為 ISO 日期字符串。

## 4. customerName 的來源

**決策**: OrderQueryRepository 在組合 OrderListItem 時，直接與 `customers` 表 join，取得顧客姓名。

**理由**: 
- Order 本體只持有 CustomerId，不持有 Customer 物件（per GLOSSARY）。
- Query 側可以直接查詢 customers 表，這是讀取模型的職責。
- usecase 層（OrderListUseCase）不關心 customerName 的具體來源，只負責協調 OrderQueryRepository。

## 5. statusLabel 的獲取

**決策**: OrderQueryRepository 從 orders 表讀取 status 欄位（存為 ENUM），然後調用 `OrderStatus.getLabel()` 轉換為顯示文字。

**理由**: statusLabel 是 Order 狀態的顯示層表示，OrderStatus enum 已提供 `getLabel()` 方法。

## 6. OrderRepository.save() 的簽名

**決策**: 
```java
OrderId save(Order order);
```

save() 返回 orderId，便於 PlaceOrderUseCase 直接取得。

**理由**: usecase 層不需要知道持久化細節，只需要訂單被保存後的 orderId。

## 7. 訂單總額在 adapter 層的重新驗證

**決策**: adapter 層反序列化時，不再重新驗證 Order 的一致性；信任 Order Aggregate 在 usecase 層已經維護正確。

**理由**: 
- Order 的一致性邊界由 Aggregate 本身維護。
- adapter 層只負責持久化和重建，不應重複檢查領域規則。

## 8. OrderListUseCase 的查詢返回

**決策**: 
```java
List<OrderListItem> listAllOrders();
```

不提供分頁、排序、篩選（per SPEC「明確不在範圍內」）。

**理由**: SPEC 明確指出「分頁、排序」不在範圍。

## 9. Exception 處理策略

**決策**: 
- usecase 層拋出業務異常（如 `IllegalArgumentException`、`IllegalStateException`）給 adapter/controller 捕捉。
- adapter 層負責轉換為 HTTP 響應（4xx / 5xx）。

**理由**: usecase 層不知道 HTTP，純業務邏輯異常由外層處理。
