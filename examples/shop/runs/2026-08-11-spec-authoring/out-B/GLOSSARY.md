# GLOSSARY — 訂單系統 ubiquitous language

**實作命名必須照此表,不得另創同義詞。**(類別、方法、變數、資料表、JSON 欄位,一律以本表英文名為準;對外顯示文字以本表「顯示文字」欄為準。)

| 詞(英文名) | 中文 | 型態(DDD) | 定義(一句) | 所屬層 |
|---|---|---|---|---|
| Order | 訂單 | Aggregate Root | 客人一次下單的結果;成立即鎖定,之後不可變更(訪談 Q6)。 | domain |
| OrderId | 訂單編號 | Value Object | Order 的唯一識別碼,由系統產生。 | domain |
| OrderItem | 訂單明細 | Value Object(Order 聚合內) | 訂單中的一條購買項目:品名(productName)、數量(quantity)、單價(unitPrice);不獨立於 Order 存在。 | domain |
| Money | 金額 | Value Object | 數值(amount)+ 幣別(Currency)的組合;同幣別才可相加。 | domain |
| Currency | 幣別 | Value Object | ISO 4217 三碼大寫代號(如 USD、TWD);一張 Order 只有一種(訪談 Q3、Q3b)。 | domain |
| TotalAmount | 訂單總額 | 導出值(Order 上的計算結果,型別為 Money) | 由系統計算:Σ(每條 OrderItem 的 quantity × unitPrice);不接受外部指定(訪談 Q2)。 | domain |
| OrderStatus | 訂單狀態 | Value Object(enum) | 本版唯一值 `CONFIRMED`;顯示文字固定為中文「已成立」(訪談 Q1)。 | domain |
| Customer | 顧客 | 外部 Read Model(CRM 擁有,本系統唯讀) | CRM 維護的顧客資料,僅兩個欄位:CustomerId、name;本系統不得寫入(訪談 Q4)。 | domain(介面)/ adapter(實作) |
| CustomerId | 顧客編號 | Value Object | CRM 顧客表的識別碼;Order 以此參照 Customer。 | domain |
| OrderRepository | 訂單儲存庫 | Repository(介面) | Order 聚合的存取入口:儲存新訂單、查詢全部訂單。 | domain(介面)/ adapter(JPA 實作) |
| CustomerReader | 顧客查詢器 | Repository(唯讀介面) | 依 CustomerId 讀取 Customer;**只有讀方法,永無寫方法**(CRM 邊界)。 | domain(介面)/ adapter(實作) |
| PlaceOrder | 下單 | Use Case(Application Service) | 接收下單請求,驗證顧客存在與明細規則,建立並儲存 Order。 | usecase |
| ListOrders | 查詢訂單列表 | Use Case(Application Service) | 回傳全部訂單的列表資料:顧客姓名、狀態顯示文字、總額與幣別、下單日期;下單日期新→舊。 | usecase |
| OrderSummary | 訂單列表項 | Value Object(讀取用 DTO) | ListOrders 的單筆輸出:customerName、statusText(「已成立」)、totalAmount、currency、orderDate。 | usecase |
| orderDate | 下單日期 | Order 的屬性(Value) | 訂單成立當下由系統記錄的日期時間。 | domain |

## 顯示文字對照

| 內部值 | 顯示文字 |
|---|---|
| OrderStatus.CONFIRMED | 已成立 |

## 命名邊界提醒

- 不得出現 `Member`、`User`、`Client`、`Buyer` 等 Customer 的同義詞。
- 不得出現 `modifyOrder`、`updateOrder`、`cancelOrder` 等違反 Order 不變性的命名。
- 「總額」只叫 TotalAmount,不得另創 `grandTotal`、`sum`、`price` 等別名。
