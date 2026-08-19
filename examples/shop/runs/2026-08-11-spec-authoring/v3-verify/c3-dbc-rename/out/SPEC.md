# SPEC — 下單 / 訂單列表

命名一律依 GLOSSARY.md;每條規則的 `[Qn]` 回鏈 INTERVIEW-LOG.md。

## 端點清單(不多不少,共 2 個)

| # | Method | Path | Use Case | 出處 |
|---|---|---|---|---|
| 1 | `POST` | `/orders` | PlaceOrder(客人下單) | [Q0] |
| 2 | `GET` | `/orders` | ListOrders(看所有訂單) | [Q0][Q5] |

HTTP 形狀(狀態碼、JSON 欄位、錯誤碼)為技術自決 [Q15]。

### POST /orders

Request body:

```json
{
  "customerId": "C001",
  "items": [
    { "productName": "跑鞋", "quantity": 2, "unitPrice": 250000, "currency": "TWD" }
  ]
}
```

- `unitPrice` 為該幣別 minor units 整數(GLOSSARY「Money」)。
- 成功:`201`,body `{ "orderId": "<非空字串>", "totalAmount": 500000, "currency": "TWD" }`。
- 失敗:`422`,body `{ "error": "<錯誤碼>" }`;錯誤碼見各情境。

### GET /orders

- 成功:`200`,body 為陣列,每筆:

```json
{ "customerName": "王小明", "status": "已成立", "totalAmount": 500000, "currency": "TWD", "orderDate": "2026-08-11" }
```

- 排序:下單時間新到舊 [Q13]。`status` 字面固定為中文「已成立」[Q5]。

## 行為情境(Given-When-Then)

### S1 成功下單(單一明細) [Q0][Q7][Q12]

- **Given** CRM 顧客表有 `C001 / 王小明`;系統內沒有任何訂單
- **When** `POST /orders`,body:`customerId="C001"`,items = `[{productName:"跑鞋", quantity:2, unitPrice:250000, currency:"TWD"}]`
- **Then** 回 `201`;`totalAmount = 500000`、`currency = "TWD"`;`orderId` 為非空字串

### S2 成功下單(多條明細,總額 = Σ 數量×單價) [Q7]

- **Given** CRM 顧客表有 `C001 / 王小明`
- **When** `POST /orders`,items = `[{productName:"跑鞋", quantity:2, unitPrice:250000, currency:"TWD"}, {productName:"襪子", quantity:3, unitPrice:10000, currency:"TWD"}]`
- **Then** 回 `201`;`totalAmount = 2×250000 + 3×10000 = 530000`

### S3 下單失敗:顧客不在 CRM 名單 [Q11]

- **Given** CRM 顧客表**沒有** `C999`
- **When** `POST /orders`,`customerId="C999"`,items 合法(同 S1)
- **Then** 回 `422`,`error = "CUSTOMER_NOT_FOUND"`;不建立任何訂單

### S4 下單失敗:明細為空 [Q8]

- **Given** CRM 顧客表有 `C001`
- **When** `POST /orders`,`customerId="C001"`,`items = []`
- **Then** 回 `422`,`error = "EMPTY_ORDER"`;不建立任何訂單

### S5 下單失敗:數量小於 1 [Q9]

- **Given** CRM 顧客表有 `C001`
- **When** `POST /orders`,items 含 `{productName:"跑鞋", quantity:0, unitPrice:250000, currency:"TWD"}`
- **Then** 回 `422`,`error = "INVALID_QUANTITY"`;不建立任何訂單

### S6 下單失敗:單價為負 [Q10]

- **Given** CRM 顧客表有 `C001`
- **When** `POST /orders`,items 含 `{productName:"跑鞋", quantity:1, unitPrice:-100, currency:"TWD"}`
- **Then** 回 `422`,`error = "INVALID_UNIT_PRICE"`;不建立任何訂單

### S7 下單失敗:一張訂單混多幣別 [Q4]

- **Given** CRM 顧客表有 `C001`
- **When** `POST /orders`,items = `[{productName:"跑鞋", quantity:1, unitPrice:250000, currency:"TWD"}, {productName:"襪子", quantity:1, unitPrice:5000, currency:"USD"}]`
- **Then** 回 `422`,`error = "MIXED_CURRENCY"`;不建立任何訂單

### S8 列表:四欄 + 新到舊 [Q5][Q13]

- **Given** 已成功下單兩張:訂單 A(`C001 / 王小明`,總額 `500000 TWD`,下單時間 `2026-08-10T10:00:00Z`)、訂單 B(`C002 / 李大同`,總額 `30000 TWD`,下單時間 `2026-08-11T09:00:00Z`)
- **When** `GET /orders`
- **Then** 回 `200`,陣列長度 2,第一筆為訂單 B:`{customerName:"李大同", status:"已成立", totalAmount:30000, currency:"TWD", orderDate:"2026-08-11"}`,第二筆為訂單 A:`{customerName:"王小明", status:"已成立", totalAmount:500000, currency:"TWD", orderDate:"2026-08-10"}`

### S9 列表:無訂單 [Q0]

- **Given** 系統內沒有任何訂單
- **When** `GET /orders`
- **Then** 回 `200`,body = `[]`

### S10 失敗下單不留殘骸(原子性) [Q11][Q15]

- **Given** 系統內沒有任何訂單;CRM 顧客表沒有 `C999`;且已對 `POST /orders`(`customerId="C999"`,items 同 S1)發出請求並得到 `422`
- **When** `GET /orders`
- **Then** 列表回 `200`,body = `[]`(失敗的下單沒有留下任何訂單或明細資料)

## 領域契約(Design by Contract)

與上述情境同等效力。每條標 DbC 型態,並註明配哪個指名測試(或說明為何不配)。

| 編號 | DbC 型態 | 契約內容 | 指名測試 | 出處 |
|---|---|---|---|---|
| C1 | precondition | PlaceOrder 的 `customerId` 必須存在於 CRM 顧客表,否則拒絕 | `PlaceOrderUseCaseTest#rejectsUnknownCustomer`(對應 S3) | [Q11] |
| C2 | precondition | Order 至少含一條 OrderItem | `PlaceOrderUseCaseTest#rejectsEmptyItems`(對應 S4) | [Q8] |
| C3 | precondition | 每條 OrderItem 的 Quantity ≥ 1 | `PlaceOrderUseCaseTest#rejectsQuantityBelowOne`(對應 S5) | [Q9] |
| C4 | precondition | 每條 OrderItem 的 UnitPrice ≥ 0(minor units 整數) | `PlaceOrderUseCaseTest#rejectsNegativeUnitPrice`(對應 S6) | [Q10] |
| C5 | invariant | 同一張 Order 內所有 OrderItem 的 Currency 一致;Order 全生命週期維持 | `OrderInvariantTest#rejectsMixedCurrencies`(對應 S7) | [Q4] |
| C6 | invariant | `Order.totalAmount = Σ(Quantity × UnitPrice)`,Currency 同明細;由系統計算,不接受外部傳入 | `OrderInvariantTest#totalIsSumOfQuantityTimesUnitPrice`(對應 S1/S2) | [Q7] |
| C7 | invariant | Order 成立後不可變:Order/OrderItem 無任何 mutator,系統無任何修改端點 | `OrderImmutabilityTest#orderExposesNoMutators`(反射檢查無 setter、欄位 final;端點面由「端點清單不多不少」+ S 系列整合測試覆蓋) | [Q1] |
| C8 | postcondition | PlaceOrder 成功 ⇒ Order 已持久化、OrderStatus = CREATED、TotalAmount 已算定,且隨後 ListOrders 查得到這張單 | `PlaceOrderUseCaseTest#createdOrderIsPersistedAndListable`(對應 S1+S8) | [Q0][Q5] |
| C9 | postcondition | PlaceOrder 失敗(違反 C1–C5 任一條)⇒ **系統狀態不變:不留任何殘骸**——無 Order、無 OrderItem 被寫入,ListOrders 結果與下單前完全相同。每一條失敗路徑(S3/S4/S5/S6/S7)都適用此狀態保證 | `PlaceOrderAtomicityTest#failedPlaceOrderLeavesNoTrace`(對應 S10;逐一觸發 S3–S7 五條失敗路徑後斷言列表不變) | [Q11][Q15] |
| C10 | invariant | Customer 資料唯讀:本系統任何路徑都不得寫入/修改 CRM 顧客資料 | 不配指名測試——由 CustomerRepository 介面**不含寫入方法**在編譯期保證(結構性保證,見 ARCHITECTURE R6) | [Q2] |

## 明確不在範圍

逐項列,每項標來源:

- 取消訂單、修改訂單(**訪談否決** [Q6]「先不用,以後再說」;另 [Q1] 成立即鎖定)
- 會員系統/顧客資料的建立、修改(**訪談否決** [Q2],CRM 維護,本系統唯讀)
- 商品主檔、庫存管理(**訪談否決(fallback 採 PM 建議)** [Q12],明細只記品名字串)
- 訂單狀態流轉(出貨、完成、退貨等其他狀態)(**規格沉默**——訪談中只出現「已成立」一種狀態 [Q5])
- 單筆訂單查詢端點(`GET /orders/{id}`)(**規格沉默**)
- 列表分頁、篩選、搜尋(**規格沉默**)
- 認證、授權、多使用者權限(**規格沉默**)
- 幣別換算、跨幣別加總(**規格沉默**;且 [Q4] 一張訂單不混幣別)
- 通知(email/簡訊)、金流付款(**規格沉默**)

以上各項:**不要做**。
