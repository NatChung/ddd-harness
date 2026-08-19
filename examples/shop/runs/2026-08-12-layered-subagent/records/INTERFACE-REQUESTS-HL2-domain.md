# 界面需求

本檔案記錄領域層實作時對其他層的需求或阻礙。

## 當前狀態

**無需求。領域層實作獨立完成，不依賴外層。**

## 說明

- 領域層只包含 Value Objects（OrderId、CustomerId、ProductId、Money）、Entities（Order、OrderItem）、Enum（OrderStatus）
- 領域層不知曉 repository、usecase、adapter 等外層概念
- 外層（usecase、adapter）會依賴領域層定義的這些類型，並基於它們構建上層業務邏輯
- 領域層內部無框架依賴，ArchitectureTest 全綠

## 預期的下一層需求

以下是 usecase 層會需要實作的內容（但不是對領域層的需求）：

- `OrderRepository` 介面（定義在 usecase 層）
  - 用於 Place Order Use Case 存儲新建立的 Order
- `OrderQueryRepository` 介面（定義在 usecase 層）
  - 用於 Order List Use Case 查詢訂單列表，直接組成 `OrderListItem` View Model
- `OrderListItem` View Model（定義在 usecase 層）
  - 用於 GET /orders 端點回傳的列表形狀

這些都在領域層之上，不會迴向要求領域層修改。
