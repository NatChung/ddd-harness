# INTERFACE-REQUESTS

usecase 層對其他層(domain / build / spec)提出的變更請求。

## usecase 層:無

實作完成,**沒有任何需要 domain 層、build 檔或 spec 配合的變更**。
現成的 `com.shop.domain` 已足夠支撐兩條路徑:

- 下單:`Order.create` → `addItem` → `place(LocalDate)` → `order.orderId()` 全部到位。
- 列表:Query 側不經過 Aggregate,不需要領域層提供任何東西。

usecase 對 adapter 層的**期待**(不是變更請求,不是阻塞)寫在
`ASSUMPTIONS.md` 的 A1 / A6 / A7 / A10,並重複在各介面與 View Model 的 javadoc 裡。
