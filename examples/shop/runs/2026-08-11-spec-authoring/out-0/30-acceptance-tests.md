# 訂單系統規格 — 驗收測試

> 這是驗收的**最終依據**。實作完成的定義:`./gradlew test` 全綠,其中包含本檔全部測試 + starter 的四條 ArchUnit 規則。
> 本檔的字面值(欄位名、錯誤碼、金額、seed 資料)與 `20-api-and-use-cases.md` 一致;若有出入,以本檔為準。

## 測試基礎設施

- 測試型態:`@SpringBootTest` + `MockMvc`(整條 HTTP → usecase → H2 走真的),H2 in-memory。
- **CRM seed**(`src/main/resources/data.sql`,正式與測試共用;表 `CRM_CUSTOMER`,欄位:顧客編號、姓名):

| 顧客編號 | 姓名 |
|---|---|
| `C001` | `王小明` |
| `C002` | `陳大文` |
| `C003` | `林美玲` |

- **訂單隔離**:每個測試開始時訂單表為空(`@Transactional` rollback 或 `@BeforeEach` 清表皆可)。CRM seed 恆在。
- **固定時鐘**:測試組態以 test double 覆蓋 `ClockPort`,初始值 `2026-08-11T10:15:30`,並可由測試撥動(後述 T-10 需要)。
- 下述「下單(X)」= `POST /api/orders`,`Content-Type: application/json`。

### 標準合法 request(後續以「標準單」代稱,測試可自行微調)

```json
{
  "customerId": "C001",
  "currency": "TWD",
  "items": [
    { "productName": "運動鞋", "quantity": 2, "unitPrice": 350.00 },
    { "productName": "襪子", "quantity": 3, "unitPrice": 33.00 }
  ]
}
```

## 測試清單

### T-01 下單成功

下單(標準單)→ **201**,body 斷言:
- `orderId` 非空字串
- `customerId = "C001"`、`customerName = "王小明"`
- `status = "CREATED"`、`statusLabel = "已成立"`
- `currency = "TWD"`
- `totalAmount = 799.00`(2×350.00 + 3×33.00;斷言數值等於 799.0 即可,JSON number)
- `createdAt = "2026-08-11T10:15:30"`(固定時鐘)
- `items` 長度 2,內容 = request 的 items

### T-02 總額計算(小數)

下單(C002、`USD`、items = [{`quantity: 3`, `unitPrice: 19.99`, productName 任意}])→ 201,`totalAmount = 59.97`,`customerName = "陳大文"`。

### T-03 client 夾帶 total 被忽略

下單(標準單 + 額外欄位 `"totalAmount": 1.00`)→ **201** 且回傳 `totalAmount = 799.00`。系統算的才算數(D-08:未定義欄位忽略)。

### T-04 顧客不存在

下單(`customerId = "C999"`,其餘同標準單)→ **400**,`error = "CUSTOMER_NOT_FOUND"`。

### T-05 明細為空

下單(`items: []`)→ **400**,`error = "VALIDATION_ERROR"`。缺 `items` 欄位 → 同樣 400 `VALIDATION_ERROR`。

### T-06 數量不合法

下單(某條明細 `quantity: 0`)→ **400**,`error = "VALIDATION_ERROR"`。(`-1` 亦同,擇一測即可。)

### T-07 單價不合法

- 下單(某條明細 `unitPrice: -1.00`)→ **400**,`error = "VALIDATION_ERROR"`。
- 下單(某條明細 `unitPrice: 1.999`,scale 3)→ **400**,`error = "VALIDATION_ERROR"`。

### T-08 幣別不合法

下單(`currency: "twd"`)→ **400**,`error = "VALIDATION_ERROR"`。(`"NT$"`、`"TWDD"` 亦同,擇一即可。)

### T-09 品名空白

下單(某條明細 `productName: "  "`)→ **400**,`error = "VALIDATION_ERROR"`。

### T-10 列表:內容與排序

固定時鐘從 `2026-08-11T10:15:30` 起,每次下單前撥快 1 分鐘,依序下三張單:
1. C001、TWD、1×100.00(`createdAt = 10:16:30`)
2. C002、USD、2×25.50(`createdAt = 10:17:30`)
3. C003、TWD、1×49.90(`createdAt = 10:18:30`)

`GET /api/orders` → **200**,array 長度 3,斷言:
- 順序為 **新到舊**:`[0]` = C003 那張、`[1]` = C002、`[2]` = C001。
- `[0]`:`customerName = "林美玲"`、`statusLabel = "已成立"`、`totalAmount = 49.90`、`currency = "TWD"`、`createdAt = "2026-08-11T10:18:30"`。
- `[1]`:`customerName = "陳大文"`、`totalAmount = 51.00`、`currency = "USD"`。
- `[2]`:`customerName = "王小明"`、`totalAmount = 100.00`。
- 每個元素都有 `status = "CREATED"` 且 `statusLabel = "已成立"`;元素**不含** `items` 欄位。

### T-11 列表:空

未下任何單,`GET /api/orders` → **200**,body = `[]`。

### T-12 失敗的下單不留殘骸

下單(`customerId = "C999"`)→ 400;隨後 `GET /api/orders` → `[]`。

### T-13 domain 不可變 + 總額只能算(單元測試,不走 HTTP)

- `domain/` 的 `Order` 建構後,`totalAmount()` 回傳 Σ(quantity × unitPrice) 且 scale = 2(給 `[2×350.00, 3×33.00]` 斷言 `new BigDecimal("799.00")`,用 `compareTo` 或 equals on scale-2 皆可)。
- `Order` 與 `OrderItem` 沒有任何公開 mutator(以 API 設計保證;此條靠 code review / ArchUnit 之外的常識,不強制寫反射測試)。
- 違反 invariant(如 `quantity = 0`)時 `Order` 建構丟 domain exception(`InvalidOrderException`)。

### T-14 架構規則(starter 既有)

`./gradlew test` 需同時通過 starter 的四條 ArchUnit 規則:domain 不 import 框架、usecase 不 import 框架、domain 不 import 上層、usecase 不 import adapter。這決定了 `@Entity` 只能在 `adapter/`(見 `00-overview.md` §架構約束)——不要為了讓 JPA 方便而把註解掛進 domain。

## 明確不驗收(避免過度實作)

- `PUT/PATCH/DELETE /api/orders/**` 的行為(不實作,交給 Spring 預設)。
- 顧客在下單後從 CRM 消失的列表行為(seed 恆在,情境不會發生)。
- 分頁、篩選、GET 單筆訂單。
- `message` 欄位的文字內容。
