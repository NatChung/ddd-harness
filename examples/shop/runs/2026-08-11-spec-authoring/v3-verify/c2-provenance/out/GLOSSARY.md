# GLOSSARY — ubiquitous language

**命名鐵律:實作命名必須照此表,不得另創同義詞。**

**禁用同義詞清單**(出現即違規,一律改用左欄正名):

| 正名 | 禁用 |
|---|---|
| Order | Purchase、PurchaseOrder、Booking |
| OrderLine | Item、OrderItem、LineItem、Product、Detail |
| Customer | Client、Member、User、Buyer |
| Money | Amount(當型別名)、Price(當型別名) |
| OrderStatus | OrderState、Status(當型別名) |

## 詞表

| 詞 | 型態(DDD) | 定義 | 所屬層 | 出處 |
|---|---|---|---|---|
| Order(訂單) | Aggregate Root | 客人一次下單的結果;成立即鎖定不可變更;持有一組 OrderLine、單一 Currency、系統算出的總額、OrderStatus、下單時間 `orderedAt` | domain | [Q0][Q7][Q8] |
| OrderLine(訂單明細) | Value Object(Order aggregate 內) | 訂單中的一條:品名(自由文字)、單價(Money 的 `unitPriceMinor`)、數量;不獨立存在於 Order 之外 | domain | [Q4][Q6] |
| Customer(顧客) | Entity(屬 CRM context;本系統唯讀參照) | 顧客表的一列:顧客編號 + 姓名。本系統只讀不寫 | domain(唯讀參照)/資料由 adapter 供給 | [Q1][Q2] |
| CustomerId(顧客編號) | Value Object | 顧客的識別碼,對應 CRM 顧客表的顧客編號欄位 | domain | [Q2] |
| Money(金額) | Value Object | 金額 = 最小貨幣單位整數(`amountMinor`,如 cents)+ Currency;**一律整數,禁止浮點** | domain | [Q7][Q11] |
| Currency(幣別) | Value Object | ISO 4217 三碼(如 `TWD`、`USD`);掛在 Order 層級,一張訂單只有一個 | domain | [Q7][Q11] |
| OrderStatus(訂單狀態) | Value Object(enum) | 唯一值 `CREATED`;對外顯示中文「已成立」(映射在 adapter 層,domain 不含顯示字串) | domain(enum)/ adapter(顯示映射) | [Q10][Q11] |
| PlaceOrder(下單) | Use Case | 接收顧客編號 + 明細 + 幣別,驗前置條件、算總額、原子寫入一張 Order | usecase | [Q0][Q3][Q5][Q6] |
| ListOrders(查訂單列表) | Use Case | 回傳所有訂單:誰買的(顧客姓名)、狀態、總額 + 幣別、下單時間 | usecase | [Q0][Q10] |
| OrderRepository | Repository | Order 的儲存介面:介面在 domain,實作在 adapter;只有新增與查詢,無 update/delete | domain(介面)/ adapter(實作) | [Q0][Q8] |
| CustomerRepository | Repository | 顧客表的讀取介面:只有查詢方法,**不得有任何寫入方法** | domain(介面)/ adapter(實作) | [Q1][Q2] |

## 量值表示法(定死,無歧義)

- **金額**:最小貨幣單位整數(cents 等),欄位命名 `unitPriceMinor` / `totalAmountMinor`。[Q11]
- **幣別**:ISO 4217 三碼字串,欄位 `currency`。[Q11]
- **時間**:ISO-8601、UTC,欄位 `orderedAt`。[Q11]
- **數量**:正整數(≥ 1),欄位 `quantity`。[Q5]
