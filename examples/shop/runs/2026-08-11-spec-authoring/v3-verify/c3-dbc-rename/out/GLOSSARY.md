# GLOSSARY — ubiquitous language 表

> **命名鐵律:實作命名必須照此表,不得另創同義詞。**
>
> **禁用同義詞清單**(出現即違規):
> - `Purchase` / `Booking` / `SalesOrder` → 一律用 **Order**
> - `Client` / `Member` / `User` / `Buyer` → 一律用 **Customer**
> - `LineItem` / `OrderLine` / `Line` / `Detail` → 一律用 **OrderItem**
> - `Price` / `Amount` / `Cost` 單獨混用 → 金額值一律用 **Money**;明細單價用 **UnitPrice**;訂單總額用 **TotalAmount**
> - 狀態值 `PLACED` / `CONFIRMED` / `ACTIVE` → 一律用 **CREATED**(顯示字面「已成立」)
> - `Qty` / `Count` → 一律用 **Quantity**

| 詞 | 型態(DDD) | 定義 | 所屬層 | 出處 |
|---|---|---|---|---|
| Order(訂單) | Aggregate Root | 客人一次下單的結果;成立即鎖定,之後不可變(immutable) | domain | [Q0][Q1] |
| OrderItem(訂單明細) | Value Object | Order 內的一條明細:ProductName + Quantity + UnitPrice;無獨立生命週期,隨 Order 建立且不可變 | domain | [Q7][Q12] |
| ProductName(品名) | Value Object | 明細買的東西的名稱,非空字串;不對應商品主檔 | domain | [Q12] |
| Quantity(數量) | Value Object | 明細的購買數量,整數,**最小值 1** | domain | [Q9] |
| UnitPrice(單價) | Money | 明細單價,**不得為負,0 允許** | domain | [Q10] |
| Money(金額) | Value Object | 金額值 = 整數 amount + Currency。**單位定死:amount 一律為該幣別最小單位(minor units)的整數**(例:USD 250.00 → `25000`),不用浮點數 | domain | [Q4][Q15] |
| Currency(幣別) | Value Object | ISO 4217 三字母代碼(如 `TWD`、`USD`),不限定清單 | domain | [Q4][Q14] |
| TotalAmount(總額) | 衍生值(Order 屬性,Money) | 系統計算,= Σ(每條明細 Quantity × UnitPrice);幣別同明細 | domain | [Q7] |
| OrderStatus(訂單狀態) | Value Object(enum) | 訂單狀態;本版唯一值 **CREATED**,對外顯示字面固定為中文「**已成立**」 | domain(值)/ adapter(中文字面) | [Q5] |
| OrderDate(下單日) | 衍生表示(日期) | 訂單建立時間的日期表示,**格式定死 `YYYY-MM-DD`**;內部以建立時間戳(timestamp)記錄供排序 | domain(時間戳)/ adapter(日期字串) | [Q5][Q13][Q15] |
| Customer(顧客) | 外部唯讀參照資料(external read model) | CRM 維護的顧客;本系統只讀不寫。長相:一張表,CustomerId + Name | domain(介面)/ adapter(讀取實作) | [Q2][Q3] |
| CustomerId(顧客編號) | Value Object | CRM 顧客表的編號,Order 以此參照 Customer(跨 aggregate 以 id 參照) | domain | [Q3] |
| OrderRepository | Repository | Order aggregate 的持久化 port(儲存、列出全部) | domain(介面)/ adapter(實作) | [Q0][Q15] |
| CustomerRepository | Repository(唯讀) | Customer 的讀取 port;**介面不得含任何寫入方法** | domain(介面)/ adapter(實作) | [Q2][Q15] |
| PlaceOrder(下單) | Use Case | 客人下單:驗前提 → 算總額 → 存 Order | usecase | [Q0] |
| ListOrders(查詢訂單列表) | Use Case | 列出所有訂單(誰買的、狀態、總額、下單日),新到舊 | usecase | [Q0][Q5][Q13] |
