# ASSUMPTIONS.md — UseCase 層實作

本檔案記錄 usecase 層實作的設計決定與模糊處理結果。

## 1. Order.placedAt 日期儲存策略

**決定**: `OrderRepository.save(Order order, LocalDate placedAt)` 簽名，由 usecase 層供給日期。

**理由**:
- `Order` aggregate 沒有 `placedAt` 欄位（domain 層唯讀）。
- `OrderListItem` view model 需要 `placedAt`。
- 這個日期是寫側(下單時的事實時間)的所有權問題。由 usecase 層決定「何時下單」比 adapter 層決定更符合業務邏輯。
- `LocalDate.now()` 是 JDK stdlib（無框架依賴），符合 usecase 層的約束。

**實作細節**:
- `PlaceOrderUseCase.placeOrder()` 呼叫 `repository.save(order, LocalDate.now())`。
- Adapter 層會以此日期作為持久化的 `placed_at` 欄位值。

## 2. 空明細驗證

**決定**: 在 usecase 層拒絕空明細（`items` 為 null 或 empty）。

**理由**:
- `Order.total()` 在明細為空時拋 `IllegalStateException`，表示「空訂單無法計算總額」。
- 允許建立空訂單再下單後，任何查詢總額的操作都會爆炸。
- 這是業務規則層級的驗證：「訂單必須至少有一個明細才能成立」。
- 在 usecase 層驗證（而非讓 domain 層拋例外）更清楚地表達意圖。

**實作細節**:
- `PlaceOrderUseCase.placeOrder()` 起頭驗證 `command.items()` 不為 null 且非空。
- 違反時拋 `IllegalArgumentException`（呼叫方的 bug，不是業務例外）。

## 3. 命令 DTO 設計

**決定**: 定義 `PlaceOrderCommand` 和 `PlaceOrderCommand.PlaceOrderItem` 作為命令 DTO。

**理由**:
- 不在 GLOSSARY 中，因此是實作細節。
- 使用 record（Java 17）：immutable，無 setter，自動 equals/hashCode。
- 巢狀 `PlaceOrderItem` 以表達「明細屬於命令」的語義。
- Primitive 欄位（`String`, `int`, `long`）對應 HTTP 請求體的自然形狀。

**欄位**:
- `PlaceOrderCommand`: `customerId` (String), `items` (List<PlaceOrderItem>)
- `PlaceOrderItem`: `productId` (String), `quantity` (int), `unitPriceCents` (long), `currency` (String)

## 4. UseCase 方法名稱

**決定**: 
- `PlaceOrderUseCase.placeOrder(PlaceOrderCommand)` → 回傳 `String` (orderId)
- `OrderListUseCase.listOrders()` → 回傳 `List<OrderListItem>`

**理由**:
- 方法名對應業務動詞（下單、列表查詢）。
- 不在 GLOSSARY 中，實作自由度大；遵循 Java 慣例（動詞命名）。

## 5. 輸入驗證策略

**決定**: 在 usecase 層驗證所有輸入（command、items、各欄位）。

**理由**:
- usecase 層是應用邏輯的把關者。
- 驗證失敗拋 `IllegalArgumentException`（呼叫方 bug，非業務異常）。
- 這樣 adapter 層的 controller 負責 HTTP 層面轉換，usecase 負責邏輯層面驗證。

## 6. OrderQueryRepository 的單一方法

**決定**: `List<OrderListItem> findAllOrders()`，不支援分頁、排序、篩選。

**理由**:
- SPEC 「明確不在範圍內」包括「分頁、排序」。
- 最小化設計：僅提供 SPEC 需要的：所有訂單列表。
- Adapter 層可自由實作，usecase 層不關心實作細節（JOIN 或 SQL 或在記憶體組裝）。

## 7. View Model OrderListItem

**決定**: 使用 Java 17 record（immutable）。

**理由**:
- 往外傳的資料結構，不需要邏輯或狀態變化。
- record：無 setter，JDK-only（無框架依賴），自動生成 equals/hashCode/toString。
- 欄位對應 SPEC 的 JSON 形狀：`orderId`, `customerName`, `statusLabel`, `totalCents`, `placedAt`。

## 8. statusLabel 映射

**決定**: 映射邏輯（PLACED → 「已成立」）在 adapter 層（OrderQueryRepository 實作）。

**理由**:
- ARCHITECTURE 明確指示：「OrderQueryRepository 直接組出 OrderListItem」。
- usecase 層只定義 View Model 的形狀，不負責狀態文字國際化。
- adapter 層知道持久化儲存的 `OrderStatus` enum，負責轉譯。

## 9. 測試策略

**決定**: 手寫 fake 物件（無 Mockito）。

**理由**:
- 簡單清楚：看得見假物件的行為。
- 無額外依賴。
- `OrderItem` 建構子 package-private，Mockito 也無法直接構造；手寫 fake 更自然。
- 通過 fake 的 public 欄位（如 `savedOrder`, `savedDate`）驗證行為。

## 10. 架構檢查合規性

- ✅ usecase 層無框架 import（Spring、JPA、Jackson）
- ✅ usecase 層無 adapter 層 import（只依賴自己定義的介面）
- ✅ usecase 層無 domain 層改動（唯讀使用）
- ✅ 介面宣告在 usecase 層（OrderRepository、OrderQueryRepository）
- ✅ View Model 定義在 usecase 層（OrderListItem）
