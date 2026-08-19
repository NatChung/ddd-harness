# GLOSSARY — 訂單系統 ubiquitous language

> **命名鐵律:實作命名必須照此表,不得另創同義詞。** 任何 class、method、欄位、
> API 欄位名,只要概念出現在本表,就必須用本表的英文實作名;本表沒有的概念,
> 先回到訪談(補問)或記入 ASSUMPTIONS.md,不得自創領域詞。

## 禁用同義詞清單

| 概念 | 唯一合法名 | 禁用 |
|---|---|---|
| 訂單 | `Order` | Purchase、Booking、Sale、Deal |
| 訂單明細 | `OrderItem` | LineItem、OrderLine、OrderDetail、Item、Line |
| 顧客 | `Customer` | Member、User、Client、Buyer、Account |
| 單價 | `unitPriceAmount` | price、cost、fee、unitCost |
| 總額 | `totalAmount` | total、sum、grandTotal、totalPrice、amountDue |
| 數量 | `quantity` | qty、count、num、amount(指數量時) |
| 狀態 | `status` / `OrderStatus` | state、phase、stage |
| 幣別 | `currency` | currencyCode(欄位名)、money、ccy |
| 金額型別 | `long`(最小幣值單位) | `double`、`float`、`BigDecimal`(金額一律 long,見下) |

## 詞彙表

| 中文詞 | 實作名 | DDD 型態 | 定義(一句) | 所屬層 | 表示法/單位 | 回鏈 |
|---|---|---|---|---|---|---|
| 訂單 | `Order` | Aggregate Root | 客人一次下單的紀錄;成立即鎖定,不可再變更。 | domain | — | [Q10] |
| 訂單明細 | `OrderItem` | Value Object(屬 Order aggregate 內) | 訂單中的一條購買項目:品名 + 單價 + 數量。 | domain | — | [Q4] |
| 顧客 | `Customer` | Entity(唯讀;identity = `customerId`;資料由 CRM 擁有) | CRM 維護的顧客,本系統只讀不寫。 | domain | — | [Q2][Q3] |
| 顧客編號 | `customerId` | Customer 的 identity(屬性) | CRM 顧客表的唯一編號。 | domain | 非空字串 | [Q3] |
| 顧客姓名 | `customerName` | Customer 屬性 | CRM 顧客表的姓名欄位。 | domain | 非空字串 | [Q3] |
| 品名 | `productName` | OrderItem 屬性 | 該明細購買的商品名稱(無商品主檔,直接帶字串)。 | domain | 非空字串 | [Q4] |
| 金額(通則) | — | 值的表示規約 | **金額一律最小幣值單位(minor units,如 cents)的整數,Java `long`;禁止浮點與 BigDecimal。** | 全層 | `long`,最小幣值單位 | [Q9] |
| 單價 | `unitPriceAmount` | OrderItem 屬性(金額) | 該明細的單件價格。 | domain | `long` ≥ 0,最小幣值單位 | [Q6][Q9] |
| 數量 | `quantity` | OrderItem 屬性 | 該明細購買件數。 | domain | `int` ≥ 1 | [Q6] |
| 總額 | `totalAmount` | Order 推導值(金額) | 系統計算:Σ(quantity × unitPriceAmount),不接受外部傳入。 | domain | `long`,最小幣值單位 | [Q8] |
| 幣別 | `currency` | Order 屬性(Value Object 語意) | 訂單的幣別;掛在 Order 層級,一張訂單只有一種,OrderItem 不帶幣別。 | domain | ISO 4217 三碼大寫字串(如 `TWD`、`USD`) | [Q7][Q9] |
| 訂單狀態 | `OrderStatus` | Value Object(enum) | 訂單目前的狀態;本輪唯一值 `CREATED`。 | domain | enum,唯一值 `CREATED` | [Q13] |
| 狀態顯示文字 | `statusLabel` | 顯示值(presentation) | 給營運主管看的中文狀態;`CREATED` ↔「已成立」,轉換只發生在 adapter 層。 | adapter | 字串「已成立」 | [Q13][Q14] |
| 下單時間 | `createdAt` | Order 屬性 | 訂單成立的時間點。 | domain | ISO-8601 UTC(Java `Instant`,如 `2026-08-12T03:00:00Z`) | [Q9][Q14] |
| 訂單編號 | `orderId` | Order 的 identity | 系統產生的訂單唯一識別。 | domain | 非空字串(系統產生) | [Q9]* |
| 訂單儲存庫 | `OrderRepository` | Repository | Order aggregate 的存取介面;只有新增與查詢,無更新/刪除語意。 | domain(介面)/ adapter(實作) | — | [Q10] |
| 顧客儲存庫 | `CustomerRepository` | Repository(唯讀) | 讀 CRM 顧客表的介面;只有查詢方法,無任何寫入方法。 | domain(介面)/ adapter(實作) | — | [Q2] |
| 建立訂單 | `PlaceOrderUseCase` | Use Case(Application Service) | 客人建立一張訂單的應用流程。 | usecase | — | [Q1] |
| 訂單列表 | `ListOrdersUseCase` | Use Case(Application Service) | 營運主管查看所有訂單的應用流程。 | usecase | — | [Q1][Q14] |

\* `orderId` 的產生方式屬實作細節(Q9「你決定」授權範圍);格式由實作 agent 自決並記 ASSUMPTIONS.md。

## 備註

- 本表所屬層對應 ARCHITECTURE.md 的三層:`domain` / `usecase` / `adapter`。
- 「已成立」這三個中文字**只允許出現在 adapter 層**(顯示轉換),domain/usecase 內一律用 `CREATED`(見 ARCHITECTURE.md A4)。
