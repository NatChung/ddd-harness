# SPEC — 下單系統

讀者:AI 實作 agent。驗收:自動化測試(指名測試須存在且全綠)。
命名一律照 GLOSSARY.md;`[Qn]` 回鏈 INTERVIEW-LOG.md。

## 端點清單(不多不少)

只有以下兩個端點,**不得新增其他端點**:

| 方法 | 路徑 | 用途 | 回鏈 |
|---|---|---|---|
| `POST` | `/orders` | 下單(PlaceOrder) | [Q0] |
| `GET` | `/orders` | 查詢所有訂單(ListOrders) | [Q0] |

### `POST /orders` request(形狀)[Q8][Q13]

```json
{
  "customerId": "C001",
  "currency": "USD",
  "lines": [
    { "productName": "跑鞋", "quantity": 2, "unitPriceCents": 2500 }
  ]
}
```

- 幣別定義在訂單層,明細**不帶**幣別欄位(單一幣別由結構保證)[Q4]。
- request **沒有** total 欄位——總額一律系統計算 [Q7]。

### 成功回應 `201`(形狀)

```json
{
  "orderId": "<系統產生>",
  "customerId": "C001",
  "customerName": "王小明",
  "status": "已成立",
  "totalCents": 5000,
  "currency": "USD",
  "placedAt": "<UTC ISO-8601>",
  "lines": [ { "productName": "跑鞋", "quantity": 2, "unitPriceCents": 2500 } ]
}
```

### 失敗回應 [Q13]

- 業務規則違反 → `422`,body `{"error": "<訊息>"}`。
- 系統內部失敗(如持久化失敗)→ `500`,body `{"error": "<訊息>"}`。

### `GET /orders` 回應 `200`(形狀)[Q5][Q13]

依 `placedAt` 新到舊排序的陣列;每列:

```json
{
  "orderId": "<id>",
  "customerName": "王小明",
  "status": "已成立",
  "totalCents": 5000,
  "currency": "USD",
  "placedAt": "<UTC ISO-8601>"
}
```

## 領域規則(與情境同等效力)

每條標 DbC 型態,並註明配哪個指名測試(或為何不配)。

| # | 規則 | DbC 型態 | 指名測試 | 回鏈 |
|---|---|---|---|---|
| R1 | Order 成立後不可變更:Order 類別不得暴露任何改變狀態的公開方法;系統無更新/刪除端點 | invariant | `OrderImmutabilityTest`(反射斷言 Order 無公開 mutator;端點「不多不少」由 S1–S10 隱含) | [Q1][Q6] |
| R2 | 一張 Order 至少一條 OrderLine | precondition(PlaceOrder)/ invariant(Order 建構) | `PlaceOrderRejectsEmptyLinesTest`(= S3) | [Q8] |
| R3 | `customerId` 必須存在於 CRM 顧客表,否則拒單 | precondition(PlaceOrder) | `PlaceOrderRejectsUnknownCustomerTest`(= S4) | [Q10] |
| R4 | 每條明細 `Quantity` ≥ 1(整數) | precondition(PlaceOrder)/ invariant(OrderLine) | `PlaceOrderRejectsInvalidQuantityTest`(= S5) | [Q11] |
| R5 | 每條明細 `UnitPrice` ≥ 0,cents 整數 | precondition(PlaceOrder)/ invariant(OrderLine) | `PlaceOrderRejectsNegativeUnitPriceTest`(= S6) | [Q11][Q13] |
| R6 | 一張 Order 只有一個 `Currency`(所有明細金額共用訂單幣別) | invariant | 不配指名測試——幣別只存在於 Order 層、OrderLine 無幣別欄位,違反狀態在型別結構上不可表示 | [Q4] |
| R7 | `TotalAmount` = Σ(`Quantity` × `UnitPrice`),由系統計算;外部傳入的任何 total 值不得影響結果 | postcondition(PlaceOrder)/ invariant(Order) | `OrderTotalCalculationTest`(= S1、S2 的 Then) | [Q7] |
| R8 | **原子性/不留殘骸**:PlaceOrder 的**每一條失敗路徑**(R2–R5 違反、幣別格式錯、持久化中途失敗)結束後,系統狀態與下單前完全相同——訂單數不變、不存在任何孤兒 OrderLine、`GET /orders` 看不到任何殘缺資料。PlaceOrder 為單一交易,全有全無 | postcondition(每條失敗路徑的狀態保證) | `PlaceOrderAtomicityTest`(= S8,模擬持久化中途失敗);S3–S7 每條失敗情境的 Then 亦各自斷言「訂單數不變」 | [Q9] |
| R9 | `OrderStatus` 唯一值為 `CREATED`;兩端點回應的 `status` 欄一律回中文「已成立」 | invariant(狀態值)+ postcondition(回應內容) | `OrderStatusDisplayTest`(= S1、S9 的 Then) | [Q1][Q5][Q13] |

## 行為情境(Given-When-Then)

共同 Given:CRM 顧客表(唯讀)已有兩列:`("C001", "王小明")`、`("C002", "李大同")`。[Q3]

### S1 成功下單(單條明細)[Q0][Q7][Q5]

- **Given** 系統中沒有任何訂單
- **When** `POST /orders`:`customerId="C001"`, `currency="USD"`, lines=[{"跑鞋", quantity=2, unitPriceCents=2500}]
- **Then** 回 `201`;`totalCents=5000`;`status="已成立"`;`orderId` 非空;`placedAt` 為 UTC ISO-8601;`GET /orders` 回 1 列。
- 測試:`OrderTotalCalculationTest` / `OrderStatusDisplayTest`

### S2 成功下單(多條明細,總額加總)[Q7]

- **Given** 系統中沒有任何訂單
- **When** `POST /orders`:`customerId="C002"`, `currency="USD"`, lines=[{"跑鞋", 1, 2500}, {"襪子", 3, 300}]
- **Then** 回 `201`;`totalCents=3400`(2500×1 + 300×3)。
- 測試:`OrderTotalCalculationTest`

### S3 空明細拒單 [Q8][Q9]

- **Given** 系統中沒有任何訂單
- **When** `POST /orders`:`customerId="C001"`, `currency="USD"`, `lines=[]`
- **Then** 回 `422` 且 body 含 `error`;**系統中訂單數仍為 0,無任何 OrderLine 落地**。
- 測試:`PlaceOrderRejectsEmptyLinesTest`

### S4 顧客不存在拒單 [Q10][Q9]

- **Given** 系統中沒有任何訂單;顧客表無 `"C999"`
- **When** `POST /orders`:`customerId="C999"`, `currency="USD"`, lines=[{"跑鞋", 1, 2500}]
- **Then** 回 `422`;**訂單數仍為 0,無任何 OrderLine 落地**。
- 測試:`PlaceOrderRejectsUnknownCustomerTest`

### S5 數量不合法拒單 [Q11][Q9]

- **Given** 系統中沒有任何訂單
- **When** `POST /orders`:`customerId="C001"`, `currency="USD"`, lines=[{"跑鞋", quantity=0, unitPriceCents=2500}]
- **Then** 回 `422`;**訂單數仍為 0,無任何 OrderLine 落地**。
- 測試:`PlaceOrderRejectsInvalidQuantityTest`

### S6 單價為負拒單 [Q11][Q9]

- **Given** 系統中沒有任何訂單
- **When** `POST /orders`:`customerId="C001"`, `currency="USD"`, lines=[{"跑鞋", 1, unitPriceCents=-100}]
- **Then** 回 `422`;**訂單數仍為 0,無任何 OrderLine 落地**。
- 測試:`PlaceOrderRejectsNegativeUnitPriceTest`

### S7 幣別格式錯拒單 [Q13][Q9]

- **Given** 系統中沒有任何訂單
- **When** `POST /orders`:`customerId="C001"`, `currency="us"`(非 3 個大寫字母), lines=[{"跑鞋", 1, 2500}]
- **Then** 回 `422`;**訂單數仍為 0,無任何 OrderLine 落地**。
- 測試:`PlaceOrderRejectsBadCurrencyFormatTest`

### S8 持久化中途失敗,不留殘骸(原子性)[Q9]

- **Given** 系統中已有 1 張訂單(S1 的資料);OrderRepository 被替換為「**先把訂單列真實寫入、在明細寫入完成前丟出例外**」的假件(test double,委派真實 repository 完成部分寫入後失敗)——確保失敗發生在交易內**已有部分寫入之後**,測試不可因「什麼都沒寫」而空洞地通過
- **When** `POST /orders`:`customerId="C002"`, `currency="USD"`, lines=[{"跑鞋", 1, 2500}]
- **Then** 回 `500`;**部分寫入必須被回滾:`GET /orders` 仍只回原本那 1 列;資料庫中訂單數 = 1,OrderLine 數 = 原數,無孤兒明細**。
- 測試:`PlaceOrderAtomicityTest`

### S9 列表內容與排序 [Q5][Q13]

- **Given** 先後成功建立兩張訂單:第一張 `C001`(totalCents=5000, USD),第二張 `C002`(totalCents=3400, USD),第二張 `placedAt` 較晚
- **When** `GET /orders`
- **Then** 回 `200`,陣列長度 2,**第一列是較晚的那張**(新到舊);每列含 `customerName`(第一列 `"李大同"`、第二列 `"王小明"`)、`status="已成立"`、`totalCents`、`currency`、`placedAt`。
- 測試:`ListOrdersContentAndSortingTest` / `OrderStatusDisplayTest`

### S10 空列表 [Q0]

- **Given** 系統中沒有任何訂單
- **When** `GET /orders`
- **Then** 回 `200`,body 為空陣列 `[]`。
- 測試:`ListOrdersEmptyTest`

## 明確不在範圍

逐項列,每項標來源:

| 項目 | 來源 |
|---|---|
| 修改訂單 | 訪談否決 [Q1][Q6] |
| 取消訂單 | 訪談否決 [Q6] |
| 會員系統 / 顧客資料的新增、修改、刪除(CRM 維護,本系統唯讀) | 訪談否決 [Q2] |
| 一張訂單混多種幣別 | 訪談否決 [Q4] |
| 幣別換算、跨幣別加總 | 規格沉默 |
| 幣別代碼白名單驗證(只驗 3 大寫字母格式,不驗是否為真實幣別) | 規格沉默 [Q13] |
| 列表分頁、篩選、自訂排序參數 | 規格沉默 |
| 認證、授權、使用者登入 | 規格沉默 |
| 商品主檔 / 庫存檢查(ProductName 只是字串) | 規格沉默 |
| 訂單成立後的通知(email 等) | 規格沉默 |
| 訂單狀態流轉(唯一狀態「已成立」,無其他狀態) | 訪談否決 [Q1][Q6] + 規格沉默 |

以上各項:**不要做。**
