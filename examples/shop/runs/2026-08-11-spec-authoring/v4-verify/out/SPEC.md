# SPEC — 訂單系統

讀者:AI 實作 agent。驗收:自動化測試。命名一律照 `GLOSSARY.md`。
每條規則的 `[Qn]` 回鏈 `INTERVIEW-LOG.md`。

## 端點清單(不多不少)[Q13]

| # | Method | Path | 用途 |
|---|---|---|---|
| 1 | `POST` | `/orders` | 客人下單(建單)[開場] |
| 2 | `GET` | `/orders` | 看所有訂單(列表)[開場] |

除此之外不得有任何其他端點(含顧客 CRUD、訂單修改/取消/單筆查詢)。[Q2][Q6][Q13]

### 請求/回應格式 [Q12][Q13]

- `POST /orders` 請求 body(JSON):
  `{ "customerId": "...", "currency": "USD", "lines": [ { "itemName": "...", "quantity": 2, "unitPriceCents": 1500 } ] }`
  - 金額一律 cents 整數欄位(`unitPriceCents`);不接受 `totalAmount`(系統算)。[Q7][Q12]
- 成功回 `201`,body 含:`orderId`、`customerId`、`currency`、`lines[]`、`totalAmountCents`、`status`(`CREATED`)、`placedAt`(ISO-8601 UTC)。
- 驗證失敗回 `400` + 錯誤訊息;查無顧客回 `404`;系統中途失敗回 `500`。[Q9][Q10][Q15]
- `GET /orders` 回 `200`,body 為陣列,每筆:`customerName`(誰買的)、`statusText`(中文,`"已成立"`)、`totalAmountCents`、`currency`、`placedAt`;依 `placedAt` 新到舊。[Q5][Q11]

## 行為情境(Given-When-Then)

### S1 成功建單,系統算總額 [開場][Q7][Q8][Q12]

- **Given** 顧客表有顧客 `C001`(姓名「王小明」);系統無任何訂單。
- **When** `POST /orders`:`customerId=C001`、`currency=USD`、明細兩條:(`itemName="鞋"`, `quantity=2`, `unitPriceCents=1500`)、(`itemName="襪"`, `quantity=3`, `unitPriceCents=200`)。
- **Then** 回 `201`;`totalAmountCents = 2×1500 + 3×200 = 3600`;`status = "CREATED"`;`placedAt` 為 ISO-8601 UTC 時刻;系統內恰有 1 筆訂單、2 條明細。

### S2 查無顧客,拒單 [Q10]

- **Given** 顧客表只有 `C001`;系統無任何訂單。
- **When** `POST /orders`:`customerId=C999`,其餘同 S1 合法內容。
- **Then** 回 `404`(查無此顧客);系統內訂單數為 0(無殘留)。

### S3 空明細,拒單 [Q9]

- **Given** 顧客表有 `C001`;系統無任何訂單。
- **When** `POST /orders`:`customerId=C001`、`currency=USD`、`lines=[]`。
- **Then** 回 `400`;系統內訂單數為 0。

### S4 數量不合法,拒單 [Q9]

- **Given** 顧客表有 `C001`;系統無任何訂單。
- **When** `POST /orders`:一條明細 `quantity=0`(另測 `quantity=-1`),單價合法。
- **Then** 回 `400`;系統內訂單數為 0。

### S5 單價為負,拒單 [Q9]

- **Given** 顧客表有 `C001`;系統無任何訂單。
- **When** `POST /orders`:一條明細 `unitPriceCents=-100`,數量合法。
- **Then** 回 `400`;系統內訂單數為 0。(`unitPriceCents=0` 合法,不拒。[Q9])

### S6 混幣別,拒單(domain 層級)[Q4]

註:API 層以「訂單層級單一 `currency` 欄位」結構化落實此規則(混幣別在 API 上無法表達);本情境驗 domain 防線本身。

- **Given** 準備建構一個 Order:訂單幣別 `USD`,兩條明細,其中一條的 `unitPrice` 為 `Money(500, TWD)`(與訂單幣別不一致)。
- **When** 建構/成立該 Order。
- **Then** 建構被拒(domain 例外),無 Order 產生。(對應指名測試 `OrderTest#rejectsMixedCurrencies`)

### S7 列表欄位與排序 [Q5][Q11]

- **Given** 顧客表有 `C001`(王小明)、`C002`(李大華);已成立兩筆訂單:訂單 A(`C001`,總額 3600 cents USD,`placedAt=2026-08-01T10:00:00Z`)、訂單 B(`C002`,總額 500 cents TWD,`placedAt=2026-08-02T10:00:00Z`)。
- **When** `GET /orders`。
- **Then** 回 `200`,陣列長度 2,第一筆為訂單 B(較新);每筆含 `customerName`(「李大華」/「王小明」)、`statusText="已成立"`、`totalAmountCents`、`currency`、`placedAt`。

### S8 空系統列表 [開場]

- **Given** 系統無任何訂單。
- **When** `GET /orders`。
- **Then** 回 `200`,body 為空陣列 `[]`。

### S9 持久化中途失敗,不留殘骸 [Q15]

- **Given** 顧客表有 `C001`;系統無任何訂單;OrderRepository 被替換為「寫入中途拋例外」的測試替身(在部分資料已寫入後失敗)。
- **When** `POST /orders` 送 S1 的合法內容。
- **Then** 回 `500`;交易回滾後系統內訂單數為 0、明細數為 0(以資料庫實查斷言);且測試必須先斷言失敗確實被觸發(替身拋出例外),不得空洞通過。

## 領域契約(Design by Contract)

與上述情境同等效力。每條標 DbC 型態,並註明配哪個指名測試(或為何不配)。

| 編號 | 型態 | 契約 | 指名測試 |
|---|---|---|---|
| **C1** | precondition | 建單時 `customerId` 必須存在於顧客表,否則拒單。[Q10] | `CreateOrderUseCaseTest#rejectsUnknownCustomer`(對應 S2) |
| **C2** | precondition | 建單時明細至少一條;每條 `quantity ≥ 1`、`unitPriceCents ≥ 0`。[Q9] | `CreateOrderUseCaseTest#rejectsEmptyLines` / `#rejectsNonPositiveQuantity` / `#rejectsNegativeUnitPrice`(對應 S3–S5) |
| **C3** | invariant | 一張 Order 內所有明細與總額幣別一致(單張不混幣別)。[Q4] | `OrderTest#rejectsMixedCurrencies`(對應 S6) |
| **C4** | invariant | `totalAmount = Σ(quantity × unitPrice)`,恆成立;由系統計算,任何外部傳入的總額一律忽略或拒絕。[Q7] | `OrderTest#computesTotalFromLines`(對應 S1 的總額斷言) |
| **C5** | invariant | Order 成立後不可變:類別不暴露任何改變狀態的方法,欄位不可重新賦值。[Q1] | `OrderImmutabilityTest#orderExposesNoMutatingMethods`(反射檢查無 setter/mutator;搭配「端點清單不多不少」堵住 API 層修改路徑) |
| **C6** | postcondition | 建單成功路徑:Order 已持久化、`status = CREATED`、`placedAt` 已由系統記錄、回應含完整訂單內容。[開場][Q12] | `CreateOrderUseCaseTest#persistsCreatedOrder`(對應 S1) |
| **C7** | postcondition | **失敗路徑狀態保證(原子性)**:任何建單失敗——含 C1/C2/C3 違反,以及**系統中途失敗(如持久化中途失敗)**——系統狀態不變,不留部分訂單或孤兒明細。[Q15][Q9][Q10] | 驗證前的失敗路徑由 S2–S5 各測試的「訂單數為 0」斷言與 S6 的「無 Order 產生」斷言覆蓋;**中途失敗由指名測試 `CreateOrderAtomicityTest#midPersistenceFailureLeavesNoResidue` 覆蓋(對應 S9:模擬部分寫入後拋例外,先斷言例外確實發生,再實查訂單/明細筆數為 0)** |
| **C8** | postcondition | 列表回傳系統內全部 Order,依 `placedAt` 新到舊;狀態以中文顯示值「已成立」呈現。[開場][Q5][Q11] | `ListOrdersUseCaseTest#returnsAllOrdersNewestFirst`(對應 S7、S8) |

失敗路徑清單(C7 涵蓋範圍):查無顧客 [Q10]、空明細/數量不合法/單價為負 [Q9]、混幣別 [Q4]、**持久化中途失敗 [Q15]**。

## 明確不在範圍

逐項列,每項標來源:

1. **修改訂單** — 訪談否決 [Q1][Q6]。
2. **取消訂單** — 訪談否決 [Q6]。
3. **會員系統 / 顧客資料維護(新增、修改、刪除顧客)** — 訪談否決 [Q2]。
4. **CRM → 顧客表的同步機制** — 規格沉默(訪談僅確認「讀得到就好」,同步方式未談)[Q2][Q14]。
5. **商品目錄 / 品項主檔** — 規格沉默(單價由下單方提供,無目錄需求被提出)[Q8]。
6. **訂單單筆查詢端點(`GET /orders/{id}`)** — 規格沉默 [Q13]。
7. **分頁、篩選、搜尋** — 規格沉默(列表僅要求全列 + 排序)[Q5][Q11]。
8. **登入 / 權限 / 認證** — 規格沉默(訪談未提)。
9. **幣別換算 / 多幣別加總報表** — 規格沉默(僅確認單張不混幣別)[Q4]。
10. **已成立以外的任何訂單狀態值** — 規格沉默(唯一狀態「已成立」)[Q5][Q6]。

以上各項:**不要做**。
