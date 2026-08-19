# 內層介面變更要求

## 無變更要求

adapter 層實作完全符合既有的 domain 層與 usecase 層介面，**無需對內層做任何修改**。

### 既有介面使用總結

#### Domain 層（唯讀使用）

所有 domain 類別都按既有的公開方法使用：

- **Order**
  - `Order.create(OrderId, CustomerId)` - 建立新訂單（已提供）
  - `getOrderId()`, `getCustomerId()`, `items()`, `getTotal()`, `getStatus()` - 查詢方法（已提供）
  - `addItem(ProductId, int, Money)` - 新增明細（已提供）
  - `place()` - 成立訂單（已提供）

- **OrderId**, **CustomerId**, **ProductId**, **Money**
  - `of(String)` / `of(long, String)` - 工廠方法（已提供）
  - `getValue()` / `getAmountCents()` / `getCurrency()` - 取值方法（已提供）

- **OrderStatus**
  - `DRAFT`, `PLACED` - 列舉值（已提供）
  - `getLabel()` - 標籤取值（已提供）

#### Usecase 層（實作介面）

- **OrderRepository** (interface, 由 adapter 實作)
  - `generateOrderId()` - 生成新 ID
  - `save(Order)` - 保存訂單

- **OrderQueryRepository** (interface, 由 adapter 實作)
  - `findAllOrders()` - 查詢所有訂單，回傳 List<OrderListItem>

- **PlaceOrderUseCase**, **OrderListUseCase** - 使用 adapter 層組裝的實例

#### 未使用的方法

- `Order.reconstruct()` - 雖然簽名存在但本實作未使用（因只在 save() 時轉換，不需讀回重建）

## 設計驗證

所有設計決定都在 adapter 層內部進行，未對內層提出要求，符合「相依性倒轉」原則：
- domain 層保持完全不知道 adapter 的存在
- usecase 層只依賴介面定義（OrderRepository、OrderQueryRepository），不知道 JPA 實作
- adapter 層依賴 domain 層和 usecase 層的介面，實現聚合適配
