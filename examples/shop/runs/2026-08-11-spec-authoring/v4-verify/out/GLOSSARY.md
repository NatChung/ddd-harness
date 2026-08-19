# GLOSSARY — ubiquitous language

**實作命名必須照此表,不得另創同義詞。**

**禁用同義詞清單**(出現即違規):
- `Purchase` / `PurchaseOrder` / `Booking` → 一律用 **Order**
- `Item` / `LineItem` / `Product` / `OrderItem` → 一律用 **OrderLine**
- `Member` / `Client` / `User` / `Buyer` → 一律用 **Customer**
- `Price` / `Amount` / `Cost`(作為型別名)→ 金額型別一律用 **Money**
- `total` / `sum` / `grandTotal` → 訂單總額一律用 **totalAmount**
- `State` / `Phase` → 訂單狀態一律用 **OrderStatus**;不得自創 `CONFIRMED` / `COMPLETED` 等未定義狀態值

| 詞 | 型態(DDD) | 定義 | 所屬層 |
|---|---|---|---|
| **Order**(訂單) | Aggregate Root | 客人一次下單成立的交易,含顧客編號、明細、幣別、總額、狀態、下單時間;成立後不可變。[Q1] | domain |
| **OrderLine**(訂單明細) | Value Object(隸屬 Order) | 訂單內一條要買的東西:品項名稱(`itemName`)、數量(`quantity`)、單價(`unitPrice`)。[Q8] | domain |
| **Customer**(顧客) | Entity(外部擁有,唯讀) | CRM 維護的顧客,本系統只讀:顧客編號(`customerId`)、姓名(`name`)兩欄。[Q2][Q3] | domain |
| **CustomerRepository** | Repository(唯讀 port) | 依 `customerId` 查詢 Customer;只宣告查詢方法,無任何寫入方法。[Q2][Q14] | domain(介面)/ adapter(實作) |
| **OrderRepository** | Repository(port) | 儲存 Order、列出全部 Order。[開場][Q13] | domain(介面)/ adapter(實作) |
| **Money**(金額) | Value Object | 金額 = `amountCents`(最小幣別單位整數,Java `long`,禁用浮點)+ `currency`。[Q12] | domain |
| **Currency**(幣別) | Value Object 屬性 | ISO 4217 三碼(如 `USD`、`TWD`)。一張訂單內所有明細與總額幣別一致。[Q4][Q12] | domain |
| **quantity**(數量) | 量值 | 整數,最小 1;無單位(件數)。[Q8][Q9] | domain |
| **unitPrice**(單價) | 量值(Money) | 每單位品項的金額,cents 整數,≥ 0;由下單方於下單時提供。[Q8][Q9][Q12] | domain |
| **totalAmount**(訂單總額) | 導出值(Money) | 系統計算:Σ(每條明細 `quantity` × `unitPrice`),cents 整數;不接受外部傳入。[Q7] | domain |
| **OrderStatus**(訂單狀態) | Value Object(enum) | 本案唯一狀態值 `CREATED`;對營運方顯示中文「已成立」,轉換在 adapter 層。[Q1][Q5][Q6][Q12] | domain(enum)/ adapter(顯示值) |
| **placedAt**(下單時間) | 量值 | 訂單成立時刻,ISO-8601 UTC(Java `Instant`),由系統於成立時記錄。[Q5][Q12] | domain |
| **CreateOrderUseCase**(建單) | Use Case | 收下單請求,驗證後成立 Order 並持久化;單一交易。[開場][Q15] | usecase |
| **ListOrdersUseCase**(訂單列表) | Use Case | 回傳所有 Order,依 `placedAt` 新到舊。[開場][Q11] | usecase |
