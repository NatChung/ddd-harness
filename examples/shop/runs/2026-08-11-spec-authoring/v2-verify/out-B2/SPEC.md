# SPEC — 訂單系統(本輪範圍)

命名一律依 GLOSSARY.md;每條規則/情境的 `[Qn]` 回鏈 INTERVIEW-LOG.md。

## 範圍摘要

兩個行為,不多不少 [開場][Q1][Q17]:

1. 客人建立訂單(POST /orders)
2. 營運主管查看所有訂單(GET /orders)

顧客資料由 CRM 擁有,本系統唯讀 [Q2];無商品主檔,明細直接帶品名/單價/數量 [Q4]。

## 端點清單(不多不少,共 2 個)

| # | Method | Path | 用途 | 回鏈 |
|---|---|---|---|---|
| E1 | POST | `/orders` | 建立訂單 | [Q1] |
| E2 | GET | `/orders` | 訂單列表(全部訂單,依 `createdAt` 新到舊) | [Q1][Q14][Q15] |

**除此之外不得有任何其他端點**(無單筆查詢、無修改、無刪除;見「明確不在範圍」)。

### E1 POST /orders

Request body(JSON):

```json
{
  "customerId": "C001",
  "currency": "TWD",
  "items": [
    { "productName": "經典帆布鞋", "unitPriceAmount": 250000, "quantity": 2 }
  ]
}
```

- `unitPriceAmount`:最小幣值單位(minor units)整數;測試一律以整數值直接斷言,不做任何幣別換算 [Q9]。
- `currency`:ISO 4217 三碼大寫 [Q9]。
- **request 不含 totalAmount 欄位**——總額一律系統算 [Q8];多餘/未定義欄位的處理屬實作自決,依 PROMPT.md 記 ASSUMPTIONS.md。

成功 response:HTTP `201`,body:

```json
{
  "orderId": "<系統產生,非空字串>",
  "customerId": "C001",
  "currency": "TWD",
  "status": "CREATED",
  "totalAmount": 500000,
  "createdAt": "2026-08-12T03:00:00Z",
  "items": [
    { "productName": "經典帆布鞋", "unitPriceAmount": 250000, "quantity": 2 }
  ]
}
```

失敗 response:HTTP `400`,body `{"error": "<錯誤碼>"}` [Q9]。錯誤碼:

| 錯誤碼 | 條件 | 對應規則 |
|---|---|---|
| `CUSTOMER_NOT_FOUND` | `customerId` 不在 CRM 顧客表 | R6 |
| `EMPTY_ITEMS` | `items` 為空或缺 | R1 |
| `INVALID_QUANTITY` | 任一明細 `quantity` < 1 或非整數 | R2 |
| `INVALID_UNIT_PRICE` | 任一明細 `unitPriceAmount` < 0 或非整數 | R3 |
| `INVALID_CURRENCY` | `currency` 非 ISO 4217 三碼大寫格式 | R9 |

### E2 GET /orders

無參數(無分頁、無篩選——見「明確不在範圍」)。Response:HTTP `200`,JSON array,
依 `createdAt` 新到舊排序 [Q15];每列 [Q14]:

```json
[
  {
    "orderId": "<字串>",
    "customerName": "王小明",
    "statusLabel": "已成立",
    "totalAmount": 500000,
    "currency": "TWD",
    "createdAt": "2026-08-12T03:00:00Z"
  }
]
```

- 「誰買的」= `customerName`(以訂單的 `customerId` 從 CRM 顧客表取姓名)[Q3][Q14]。
- 「狀態給我看中文」= `statusLabel`,`CREATED` 一律顯示「已成立」[Q13][Q14]。
- 「哪天下的」= `createdAt`(ISO-8601 UTC;前端如何格式化非本輪範圍)[Q9][Q14]。

## 行為情境(Given-When-Then)

每條可一比一翻成自動化測試;金額皆為最小幣值單位整數。

### 建立訂單

**S-01 成功建立單筆明細訂單** [Q7][Q8][Q9]
- Given:CRM 顧客表有 (`customerId`=`C001`, `customerName`=`王小明`);系統內無任何訂單
- When:POST /orders,body = {customerId:"C001", currency:"TWD", items:[{productName:"經典帆布鞋", unitPriceAmount:250000, quantity:2}]}
- Then:HTTP 201;body.orderId 為非空字串;body.status = "CREATED";body.totalAmount = 500000;body.currency = "TWD";body.createdAt 為合法 ISO-8601 UTC 時間戳

**S-02 多條明細總額為各條(數量×單價)之和** [Q8]
- Given:CRM 顧客表有 (`C001`, `王小明`)
- When:POST /orders,items = [{productName:"帽 T", unitPriceAmount:120000, quantity:1}, {productName:"襪子", unitPriceAmount:45000, quantity:3}],currency:"TWD",customerId:"C001"
- Then:HTTP 201;body.totalAmount = 255000(= 120000×1 + 45000×3)

**S-03 顧客不存在則拒絕** [Q2][Q3][Q9]
- Given:CRM 顧客表**沒有** `C999`
- When:POST /orders,customerId:"C999",currency:"TWD",items = [{productName:"帽 T", unitPriceAmount:120000, quantity:1}]
- Then:HTTP 400;body = {"error":"CUSTOMER_NOT_FOUND"};且 GET /orders 回空陣列(未留下任何訂單)

**S-04 明細為空則拒絕** [Q5][Q9]
- Given:CRM 顧客表有 (`C001`, `王小明`)
- When:POST /orders,customerId:"C001",currency:"TWD",items = []
- Then:HTTP 400;body = {"error":"EMPTY_ITEMS"}

**S-05 數量小於 1 則拒絕** [Q6][Q9]
- Given:CRM 顧客表有 (`C001`, `王小明`)
- When:POST /orders,items = [{productName:"帽 T", unitPriceAmount:120000, quantity:0}]
- Then:HTTP 400;body = {"error":"INVALID_QUANTITY"}

**S-06 單價為負則拒絕** [Q6][Q9]
- Given:CRM 顧客表有 (`C001`, `王小明`)
- When:POST /orders,items = [{productName:"帽 T", unitPriceAmount:-1, quantity:1}]
- Then:HTTP 400;body = {"error":"INVALID_UNIT_PRICE"}

**S-07 幣別格式不合法則拒絕** [Q9]
- Given:CRM 顧客表有 (`C001`, `王小明`)
- When:POST /orders,customerId:"C001",currency:"NT$",items = [{productName:"帽 T", unitPriceAmount:120000, quantity:1}]
- Then:HTTP 400;body = {"error":"INVALID_CURRENCY"}

### 訂單列表

**S-08 列表欄位齊全且狀態顯示中文** [Q3][Q13][Q14]
- Given:CRM 顧客表有 (`C001`, `王小明`);已成功建立一張訂單(C001、TWD、totalAmount=500000、createdAt=T1)
- When:GET /orders
- Then:HTTP 200;array 長度 1;第 0 列 = {orderId 非空, customerName:"王小明", statusLabel:"已成立", totalAmount:500000, currency:"TWD", createdAt:T1}

**S-09 多幣別並列、依下單時間新到舊** [Q7][Q15]
- Given:CRM 顧客表有 (`C001`, `王小明`)、(`C002`, `李大華`);先建立 TWD 訂單(C001, totalAmount=500000, createdAt=T1),再建立 USD 訂單(C002, totalAmount=8000, createdAt=T2, T2 > T1)
- When:GET /orders
- Then:HTTP 200;array 長度 2;第 0 列 currency = "USD"(較新),第 1 列 currency = "TWD";各列金額不換算、各帶自己的幣別

**S-10 無訂單時回空陣列** [Q1][Q14]
- Given:CRM 顧客表有資料,但系統內無任何訂單
- When:GET /orders
- Then:HTTP 200;body = []

## 領域規則(與情境同等效力;每條標 DbC 型態)

| # | 規則 | DbC 型態 | 回鏈 | 指名測試 / 不配測試的理由 |
|---|---|---|---|---|
| R1 | Order 至少含一條 OrderItem | invariant | [Q5] | `OrderTest.rejectsEmptyItems`;API 層由 S-04 覆蓋 |
| R2 | OrderItem.quantity 為整數且 ≥ 1 | invariant | [Q6] | `OrderItemTest.rejectsQuantityBelowOne`;API 層由 S-05 覆蓋 |
| R3 | OrderItem.unitPriceAmount 為整數且 ≥ 0(最小幣值單位) | invariant | [Q6][Q9] | `OrderItemTest.rejectsNegativeUnitPrice`;API 層由 S-06 覆蓋 |
| R4 | 一張 Order 只有一種 currency;OrderItem 不帶幣別 | invariant | [Q7] | 不配測試:currency 只存在於 Order 層級、OrderItem 無幣別欄位,結構上不可能違反(由 GLOSSARY 命名與 code review 保證) |
| R5 | Order.totalAmount = Σ(quantity × unitPriceAmount),由系統計算,不接受外部傳入 | postcondition(建立訂單) | [Q8] | `OrderTest.totalIsSumOfQuantityTimesUnitPrice`;API 層由 S-01/S-02 覆蓋 |
| R6 | 建立訂單時 customerId 必須存在於 CRM 顧客表 | precondition(建立訂單) | [Q2][Q3] | `PlaceOrderUseCaseTest.rejectsUnknownCustomer`;API 層由 S-03 覆蓋 |
| R7 | Order 成立後不可變更(整個 aggregate 鎖定) | invariant | [Q10] | 不配行為測試:本輪不存在任何修改端點/方法可觸發違反(端點清單即強制);domain 物件實作為 immutable,由 code review 與端點清單保證 |
| R8 | OrderStatus 唯一值 `CREATED`;對營運顯示一律「已成立」 | invariant | [Q13][Q14] | `OrderStatusLabelTest.createdMapsToChineseLabel`;API 層由 S-08 覆蓋 |
| R9 | 金額一律最小幣值單位整數(`long`),禁止浮點;currency 為 ISO 4217 三碼大寫 | invariant | [Q9] | 格式面:S-07;型別面不配行為測試——由型別系統(`long`)與 ARCHITECTURE A3 的機械檢查保證 |

## 明確不在範圍

逐項列,每項標來源。**以下全部不要做:**

| 項目 | 來源 |
|---|---|
| 修改訂單(任何欄位、任何形式) | 訪談否決 [Q10][Q11] |
| 取消訂單 | 訪談否決 [Q11] |
| 會員系統/顧客資料的新增、修改、刪除(CRM 擁有,本系統唯讀) | 訪談否決 [Q2] |
| 商品主檔、商品目錄、庫存 | 訪談否決 [Q4] |
| 出貨、完成等後續狀態流轉(本輪唯一狀態「已成立」) | 訪談否決 [Q13] |
| 登入、認證、授權、權限管控 | 訪談否決 [Q16] |
| 客服代客下單等其他角色/行為 | 訪談否決 [Q1] |
| 單筆訂單查詢(GET /orders/{id}) | 規格沉默 |
| 刪除訂單 | 規格沉默 |
| 幣別換算、匯率、跨幣別加總 | 規格沉默 |
| 列表分頁、篩選、搜尋 | 規格沉默 |
| 通知(email/簡訊)、報表匯出 | 規格沉默 |
| 前端畫面(本輪交付為 API;「列表頁」由 API 供資料) | 規格沉默 |

**不要做。** 規格沉默處若實作中發現必須決定,依 PROMPT.md:自決並記 ASSUMPTIONS.md,但不得新增端點或欄位。
