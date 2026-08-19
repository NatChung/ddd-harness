# SPEC — 訂單系統

詞彙一律依 GLOSSARY.md;本文件的情境與領域規則同等效力,實作驗收 = 全部情境可一比一翻成自動化測試並通過。

## 端點清單(不多不少,恰好兩個)

| # | Method | Path | 用途 |
|---|---|---|---|
| E1 | POST | `/orders` | PlaceOrder:客人下單 |
| E2 | GET | `/orders` | ListOrders:列出所有訂單 |

除上述兩個端點外,**不得**存在任何其他訂單相關端點(含 `/orders/{id}`、PUT/PATCH/DELETE)。

### E1 請求/回應形狀

請求 JSON:

```json
{
  "customerId": "C001",
  "currency": "TWD",
  "items": [
    { "productName": "鞋A", "quantity": 2, "unitPrice": 1500 }
  ]
}
```

成功回應:HTTP 201,body 含 `orderId`、`customerId`、`currency`、`totalAmount`、`status`(內部值 `CONFIRMED`)、`orderDate`、`items`。
失敗回應:HTTP 400,body 含機器可斷言的 `error` 代碼(見各情境)。

### E2 回應形狀

HTTP 200,JSON array,每筆為 OrderSummary:

```json
{
  "customerName": "王小明",
  "statusText": "已成立",
  "totalAmount": 5000,
  "currency": "TWD",
  "orderDate": "2026-08-11T10:00:00"
}
```

## 領域規則(invariant,與情境同等效力)

- **R1 訂單不變性**:Order 一經成立即鎖定,系統不提供任何修改或刪除訂單的途徑(訪談 Q6)。
- **R2 單一幣別**:一張 Order 只有一種 Currency;Currency 定義在 Order 層級,所有明細金額皆屬該幣別(訪談 Q3)。Currency 必須是 ISO 4217 三碼大寫代號(訪談 Q3b,PM 自決)。
- **R3 總額由系統計算**:TotalAmount = Σ(quantity × unitPrice),只由 domain 計算;請求中任何外部指定的總額一律忽略(訪談 Q2)。
- **R4 顧客必須存在**:CustomerId 必須存在於 CRM 顧客表,查無此人即拒單(訪談 Q5,PM 建議獲採納)。
- **R5 明細規則**:每張 Order 至少一條 OrderItem;quantity ≥ 1;unitPrice ≥ 0(訪談 Q9,PM 建議獲採納)。
- **R6 狀態唯一**:本版 OrderStatus 唯一值 `CONFIRMED`,對外顯示文字固定「已成立」(訪談 Q1)。
- **R7 CRM 唯讀**:本系統對顧客資料只讀不寫;程式中不得存在任何寫入 Customer 的路徑(訪談 Q4)。

## 行為情境(Given-When-Then)

### S1 下單成功

- **Given** CRM 顧客表有 `C001 / 王小明`
- **When** POST `/orders`,body:customerId=`C001`、currency=`TWD`、items=[{鞋A, quantity=2, unitPrice=1500}, {鞋B, quantity=1, unitPrice=2000}]
- **Then** 回 201;回應的 `totalAmount` = 5000、`currency` = `TWD`、`status` = `CONFIRMED`、`orderId` 非空、`orderDate` 非空;且該訂單可在 E2 列表中查到。

### S2 外部傳入總額被忽略(R3)

- **Given** CRM 顧客表有 `C001 / 王小明`
- **When** POST `/orders`,body 同 S1 但額外帶 `"totalAmount": 999`
- **Then** 回 201,回應與儲存的 `totalAmount` = 5000(系統計算值,非 999)。

### S3 顧客不存在拒單(R4)

- **Given** CRM 顧客表**沒有** `C999`
- **When** POST `/orders`,customerId=`C999`,其餘同 S1
- **Then** 回 400,`error` = `CUSTOMER_NOT_FOUND`;且 E2 列表筆數不變(未建立任何訂單)。

### S4 空明細拒單(R5)

- **Given** CRM 顧客表有 `C001 / 王小明`
- **When** POST `/orders`,items = `[]`
- **Then** 回 400,`error` = `EMPTY_ITEMS`;未建立訂單。

### S5 數量不合法拒單(R5)

- **Given** CRM 顧客表有 `C001 / 王小明`
- **When** POST `/orders`,items 含 {鞋A, quantity=0, unitPrice=1500}
- **Then** 回 400,`error` = `INVALID_QUANTITY`;未建立訂單。(quantity 為負數同此。)

### S6 單價不合法拒單(R5)

- **Given** CRM 顧客表有 `C001 / 王小明`
- **When** POST `/orders`,items 含 {鞋A, quantity=1, unitPrice=-10}
- **Then** 回 400,`error` = `INVALID_UNIT_PRICE`;未建立訂單。

### S7 幣別格式非法拒單(R2)

- **Given** CRM 顧客表有 `C001 / 王小明`
- **When** POST `/orders`,currency=`新台幣`(非 ISO 4217 三碼大寫)
- **Then** 回 400,`error` = `INVALID_CURRENCY`;未建立訂單。

### S8 列表欄位與排序

- **Given** 已成立兩張訂單:先是 `C001 / 王小明`、TWD、總額 5000、orderDate=T1;後是 `C002 / 李大華`、USD、總額 80、orderDate=T2(T2 晚於 T1)
- **When** GET `/orders`
- **Then** 回 200,恰好兩筆;第一筆是 T2 那張(新→舊,訪談 Q11);每筆恰含 `customerName`、`statusText`、`totalAmount`、`currency`、`orderDate`;兩筆的 `statusText` 均為字串 `已成立`(訪談 Q1)。

### S9 無修改/刪除途徑(R1)

- **Given** 系統已啟動
- **When** 對 `/orders` 發 PUT、PATCH、DELETE;對 `/orders/{任意id}` 發任何 method
- **Then** 前者回 405(Method Not Allowed),後者回 404(路徑不存在)——兩者皆不得改變任何既有訂單。

## 明確不在範圍(不要做)

| 項目 | 來源 |
|---|---|
| 會員系統(顧客的註冊/登入/資料維護)——顧客資料由 CRM 維護,本系統唯讀 | 訪談 Q4,stakeholder 否決 |
| 取消訂單 | 訪談 Q7,stakeholder 延後(「先不用,以後再說」) |
| 修改訂單 | 訪談 Q6+Q7,stakeholder 否決/延後 |
| 商品目錄、庫存管理 | 訪談 Q8,PM 建議延後獲採納 |
| 單筆訂單查詢端點/明細頁(`GET /orders/{id}`) | 訪談 Q10,PM 建議延後獲採納 |
| 登入/權限控管 | 未問過(規格沉默),不默默展開 |
| 列表分頁 | 未問過(規格沉默),不默默展開 |
| 報表、匯出、通知(email 等) | 未問過(規格沉默),不默默展開 |
| 幣別換算、跨幣別加總 | 未問過(規格沉默);R2 已保證單張訂單不混幣 |

以上各項:**不要做**。實作 agent 若認為必要,只能記入 ASSUMPTIONS.md 提出,不得實作。
