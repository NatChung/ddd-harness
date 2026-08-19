# 架構規則(簡潔架構三原則的落地)

package 佈局固定如下,不得增減頂層 package:

```
com.shop
├── domain/     Entities 層        Order, OrderId, OrderItem, Money, …
├── usecase/    Use Cases 層       PlaceOrderUseCase, OrderListUseCase,
│                                  OrderRepository(介面), OrderQueryRepository(介面),
│                                  OrderListItem(View Model)
└── adapter/    Interface Adapters OrderController, JpaOrderRepository,
                                   持久化模型與其對映
```

## 相依方向(機械檢查會擋)

以下由 `architecture/ArchitectureTest.java` 強制,違反則建置失敗:

- `domain/` 不得 import 任何框架(Spring、JPA、Jackson)。
- `usecase/` 不得 import 任何框架。
- `domain/` 不得 import `usecase/` 或 `adapter/`。
- `usecase/` 不得 import `adapter/`(`OrderRepository` 介面宣告在 usecase,
  `JpaOrderRepository` 實作在 adapter —— 相依性倒轉)。

## 持久化(adapter 層自己的事)

- 持久化用 Spring Data JPA + H2(依賴已在 `build.gradle`,不要加新依賴)。
- **領域物件不得直接作為 JPA entity**:`Order` 上不得出現任何 JPA/Jackson
  annotation。adapter 層建立自己的持久化模型(如 `OrderEntity`),並負責
  與 `Order` 之間的對映。
- `customers` 表已由 harness 建好(見 `app/src/main/resources/data.sql`),
  **不要**為它建立領域物件;Query 側可直接查它。

## Query 側(第 6 課)

- `GET /orders` 走 Query 側:`OrderQueryRepository` 直接組出 `OrderListItem`,
  **不得**經由 `Order` Aggregate 再轉換(不要 findAll 再逐筆 map 領域物件)。
- `OrderListItem` 定義在 usecase 層,是往外傳的資料結構,不是領域模型。

## 往外傳的形狀

- Controller 不得回傳 `Order` 或任何 `domain/` 型別;HTTP 回應一律用
  usecase 層定義的 View Model 或 adapter 層自己的 response 物件。
