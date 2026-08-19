# SPEC — 下單系統

命名一律照 GLOSSARY.md;出處 `[Qn]` 回鏈 INTERVIEW-LOG.md。

## 端點清單(不多不少)

| Method | Path | 用途 | 出處 |
|---|---|---|---|
| POST | `/orders` | 下單(PlaceOrder) | [Q0][Q11] |
| GET | `/orders` | 查所有訂單列表(ListOrders) | [Q0][Q10][Q11] |

除上述兩個端點外,不得存在其他端點。

## 行為情境(Given-When-Then)

### S1 成功下單,系統算總額 [Q0][Q4][Q6][Q7][Q11]

- **Given** 顧客表有一列:顧客編號 `C001`、姓名 `王小明`;系統中沒有任何訂單。
- **When** `POST /orders`,body:
  ```json
  {
    "customerId": "C001",
    "currency": "TWD",
    "lines": [
      { "productName": "筆記本", "unitPriceMinor": 5000, "quantity": 2 },
      { "productName": "鋼筆", "unitPriceMinor": 150000, "quantity": 1 }
    ]
  }
  ```
- **Then** HTTP 201;回應含訂單識別碼、`totalAmountMinor = 160000`(= 5000×2 + 150000×1)、`currency = "TWD"`;且後續 `GET /orders` 回傳恰 1 筆。
- 指名測試:`place_order_computes_total_and_persists`

### S2 client 傳入的總額不採信 [Q6][Q11]

- **Given** 同 S1 的顧客表。
- **When** `POST /orders`,body 同 S1 但額外夾帶 `"totalAmountMinor": 1`。
- **Then** HTTP 201;回應 `totalAmountMinor = 160000`(系統算的為準,未知欄位忽略)。
- 指名測試:`client_supplied_total_is_ignored`

### S3 查無顧客,整筆拒絕不留殘骸 [Q3][Q11]

- **Given** 顧客表**沒有** `C999`;系統中沒有任何訂單。
- **When** `POST /orders`,body 同 S1 但 `customerId = "C999"`。
- **Then** HTTP 422;且後續 `GET /orders` 回傳 0 筆(無任何訂單或明細殘骸)。
- 指名測試:`unknown_customer_rejected_no_residue`

### S4 空明細,整筆拒絕不留殘骸 [Q5][Q11]

- **Given** 顧客表有 `C001`;系統中沒有任何訂單。
- **When** `POST /orders`,`lines = []`。
- **Then** HTTP 422;且後續 `GET /orders` 回傳 0 筆。
- 指名測試:`empty_lines_rejected_no_residue`

### S5 數量小於 1,整筆拒絕不留殘骸 [Q5][Q11]

- **Given** 顧客表有 `C001`;系統中沒有任何訂單。
- **When** `POST /orders`,兩條明細其中一條 `quantity = 0`。
- **Then** HTTP 422;且後續 `GET /orders` 回傳 0 筆(合法的另一條也不得留下)。
- 指名測試:`quantity_below_one_rejected_no_residue`

### S6 負單價,整筆拒絕不留殘骸 [Q5][Q11]

- **Given** 顧客表有 `C001`;系統中沒有任何訂單。
- **When** `POST /orders`,一條明細 `unitPriceMinor = -1`。
- **Then** HTTP 422;且後續 `GET /orders` 回傳 0 筆。
- 指名測試:`negative_unit_price_rejected_no_residue`

### S7 列表:誰買的、狀態(中文)、總額、日期 [Q2][Q7][Q10][Q11]

- **Given** 顧客表有 `C001 王小明`、`C002 李大華`;已成立兩張訂單:
  C001 的 TWD 訂單(總額 160000)、C002 的 USD 訂單(1 條明細 `unitPriceMinor = 2500, quantity = 4`,總額 10000)。
- **When** `GET /orders`。
- **Then** HTTP 200;回傳恰 2 筆,每筆含:
  - `customerName`(誰買的):分別為 `"王小明"`、`"李大華"`;
  - `status = "已成立"`(中文字串,兩筆皆同);
  - `totalAmountMinor` + `currency`:分別為 `160000`/`"TWD"`、`10000`/`"USD"`;
  - `orderedAt`:ISO-8601(UTC)字串。
- 指名測試:`list_shows_buyer_status_total_date`

### S8 訂單成立即鎖定,無任何修改路徑 [Q8][Q11]

- **Given** 已成立 S1 的訂單。
- **When** 對 `/orders` 依序各發一次 `PUT`、`PATCH`、`DELETE`(同一動作對三個 method 重複)。
- **Then** 每次皆回 HTTP 405;且後續 `GET /orders` 內容與 S1 成立後完全相同(筆數、總額不變)。
- 指名測試:`mutation_attempts_rejected_order_unchanged`

## 領域規則(與情境同等效力,逐條 DbC)

| # | 規則 | DbC 型態 | 配套測試 / 說明 | 出處 |
|---|---|---|---|---|
| R1 | Order 成立後不可變更:系統不提供任何修改/刪除訂單的操作,`OrderRepository` 無 update/delete | invariant | `mutation_attempts_rejected_order_unchanged` | [Q8] |
| R2 | 下單的 `customerId` 必須存在於顧客表 | precondition | `unknown_customer_rejected_no_residue` | [Q3] |
| R3 | Order 至少 1 條 OrderLine;每條 `quantity ≥ 1`;每條 `unitPriceMinor ≥ 0` | precondition | `empty_lines_rejected_no_residue`、`quantity_below_one_rejected_no_residue`、`negative_unit_price_rejected_no_residue` | [Q5] |
| R4 | 一張 Order 只有一個 Currency,明細不得混幣別 | invariant | 由結構強制(currency 只存在於 Order 層級、OrderLine 不帶幣別欄位),不配獨立測試;S1/S7 順帶覆蓋 | [Q7][Q11] |
| R5 | `totalAmountMinor = Σ(quantity × unitPriceMinor)`,由系統計算,不採信 client 傳入值 | postcondition | `place_order_computes_total_and_persists`、`client_supplied_total_is_ignored` | [Q6] |
| R6 | **每條失敗路徑的狀態保證(原子性)**:PlaceOrder 任一前置條件違反(R2、R3)或任何錯誤中止時,系統不得留下任何 Order 或 OrderLine 殘骸;Order 與其全部 OrderLine 的寫入為全有或全無 | postcondition | 由 S3–S6 的四個 `*_no_residue` 測試共同驗證(每個失敗情境的 Then 皆斷言 `GET /orders` 為 0 筆) | [Q3][Q5] |
| R7 | OrderStatus 唯一值為 `CREATED`;對外一律顯示中文「已成立」 | invariant | `list_shows_buyer_status_total_date` | [Q10][Q11] |

## 明確不在範圍

逐項列,每項標來源:

1. 修改訂單 —— 訪談否決 [Q8][Q9]。
2. 取消訂單 —— 訪談否決 [Q9]。
3. 會員系統 / 顧客資料的新增、修改、刪除 —— 訪談否決 [Q1](CRM 維護,本系統唯讀)。
4. 商品目錄 / 商品主檔 —— 訪談否決 [Q4](品名自由填寫)。
5. 查單筆訂單(`GET /orders/{id}`)—— 規格沉默。
6. 列表的分頁、排序、篩選 —— 規格沉默。
7. 付款、出貨、庫存 —— 規格沉默。
8. 認證、授權、多使用者權限 —— 規格沉默。
9. 幣別換算 / 匯率 —— 規格沉默。
10. 訂單狀態流轉(CREATED 以外的任何狀態)—— 規格沉默 + 訪談否決 [Q9]。

以上各項:**不要做**。
