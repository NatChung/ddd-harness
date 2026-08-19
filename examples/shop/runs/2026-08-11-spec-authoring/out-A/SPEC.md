# SPEC — 訂單系統(第一版)

讀者:AI 實作 agent。驗收方式:自動化測試。
術語一律以 `CONTEXT.md` 的 canonical term 為準;範圍與邊界決策見 `docs/adr/`。
每條規則後的 `[Qn]` 對應 `INTERVIEW-LOG.md` 的問答編號,是該規則的唯一事實來源——規格與 log 衝突時以 log 為準。

## 1. 範圍

兩個 use case,僅此兩個:

1. **PlaceOrder** — 客人以顧客編號下單,成立一張 Order。
2. **ListOrders** — 營運方檢視所有 Order 的列表。

**明確不做**(explicit no,測試不得出現這些功能):

- 客人查自己的訂單 [Q1]
- 會員系統/顧客資料維護(見 ADR 0002)[Q2]
- 商品主檔(見 ADR 0003)[Q5]
- 取消訂單、修改訂單(見 ADR 0001)[Q9, Q10]

## 2. 領域規則

- **R1** Order 至少 1 條 OrderLine。[Q6]
- **R2** 每條 OrderLine:品名(自由文字、非空白)、數量、單價。[Q4, Q5]
- **R3** 數量為整數且 ≥ 1。[Q6]
- **R4** 單價 ≥ 0(允許 0,拒絕負數)。[Q7]
- **R5** 一張 Order 只有一種 Currency;下單時所有明細必須同一幣別,混幣拒絕。[Q8]
- **R6** Total 由系統計算 = Σ(數量 × 單價),不接受外部傳入的總額。[Q4]
- **R7** 下單者的顧客編號必須存在於 CRM 顧客名單,查無此人拒絕下單。[Q3]
- **R8** Order 成立後即鎖定:狀態唯一為 Confirmed,無任何後續狀態轉移,內容不可變更。[Q9, Q10]
- **R9** Order 記錄下單時間(系統時鐘,成立當下)。[Q11]

違反 R1–R5、R7 任一條:Order 不得成立,回拒絕(見 §4)。

## 3. 資料

- **CRM 顧客名單**:一張唯讀表,欄位 `customer_id`(顧客編號)、`name`(姓名)[Q2a]。本系統只讀不寫;測試以 seed 資料模擬 CRM 名單(例如 `data.sql`)。同步/介接機制不在本版範圍。
- **Order / OrderLine**:依 §2 持久化;欄位型別見 §5 技術決策。

## 4. API(對外行為)

### PlaceOrder — `POST /orders`

Request(JSON):

```json
{
  "customerId": "C001",
  "currency": "TWD",
  "lines": [
    { "productName": "藍色馬克杯", "quantity": 2, "unitPrice": 150 }
  ]
}
```

- 成功:`201`,回傳成立的 Order(含系統算出的 `total`、狀態、下單時間)。
- 拒絕:`422`(語意違規:R1–R5、R7),`400`(格式錯誤)。錯誤回應需含可判別的錯誤代碼,測試據此斷言拒絕原因。
- 不提供 `PUT`/`PATCH`/`DELETE /orders/**`(R8;若被呼叫回 `405` 或 `404` 皆可,但絕不能改變資料)。

### ListOrders — `GET /orders`

回傳所有 Order,依下單時間新→舊排序 [Q12],每筆至少含:

| 欄位 | 內容 | 來源 |
|---|---|---|
| `customerName` | 誰買的(以顧客編號 join CRM 名單取姓名) | [Q11] |
| `statusLabel` | 中文字串 `"已成立"` | [Q11] |
| `total` + `currency` | 系統算的總額與幣別 | [Q4, Q8] |
| `orderedAt` | 下單時間(ISO-8601) | [Q11] |

第一版不做分頁與篩選(未被要求,保持最小)。

## 5. 技術決策(PM 自決,未涉 stakeholder)

- 技術棧照公司 starter:Java 17、Spring Boot、Spring Data JPA、H2、Gradle;package 佈局 `domain/ usecase/ adapter/`,遵守 starter 的四條 ArchUnit 規則(domain 不 import 框架、usecase 不 import 框架、domain 不 import 上層、usecase 不 import adapter)。
- 金額用 `BigDecimal`;幣別用 ISO 4217 字串(如 `"TWD"`,格式驗證即可,不必窮舉幣別)。
- 狀態內部表示為 enum `CONFIRMED`,僅在對外呈現層轉為 `"已成立"`;中文顯示是 presentation 責任,不進 domain。
- 顧客編號、品名皆為字串;`orderedAt` 用 UTC instant。
- 對外介面選 REST/JSON:驗收是自動化測試,HTTP 介面最利於黑箱測試。

## 6. 驗收測試清單

實作完成的定義:以下情境全部有自動化測試且通過。

1. 下單成功:seed 顧客 `C001 王小明`;POST 兩條明細(2×150 + 1×200,TWD)→ `201`,`total = 500`、`currency = "TWD"`、狀態 Confirmed、有下單時間。(R2, R6)
2. 單價 0 可下單:含一條 `unitPrice: 0` 的明細 → `201`,總額只算其他明細。(R4)
3. 顧客不存在 → `422` 拒絕,無資料寫入。(R7)
4. 明細為空陣列 → `422`。(R1)
5. 數量 0 或負數 → `422`。(R3)
6. 單價負數 → `422`。(R4)
7. 明細幣別與訂單幣別不一致(或明細間混幣,依實作的 request 形狀)→ `422`。(R5)
8. request 夾帶 `total` 欄位 → 忽略之,總額仍為系統計算值。(R6)
9. 對既有 Order 呼叫 `PUT`/`PATCH`/`DELETE` → `405` 或 `404`,且資料不變。(R8)
10. 列表:seed 多張不同時間、不同幣別的 Order → `GET /orders` 回全部,新→舊排序,每筆含 `customerName`、`statusLabel = "已成立"`、`total`、`currency`、`orderedAt`。(§4 ListOrders)
11. ArchUnit 四條規則通過(starter 既有)。
