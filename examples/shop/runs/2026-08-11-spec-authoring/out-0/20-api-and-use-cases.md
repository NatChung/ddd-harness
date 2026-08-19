# 訂單系統規格 — Use Cases 與 REST API

> `usecase/` 與 `adapter/`(web)的契約。所有 JSON 欄位名、HTTP status code、錯誤碼都是**字面值規格**,驗收測試直接照抄斷言,不得改名。

## Ports(`usecase/` 定義的純 Java interface,`adapter/` 實作)

| Port | 方法(簽名意涵) | Adapter 實作 |
|---|---|---|
| `OrderRepository` | `save(Order)`、`findAll() → List<Order>` | JPA(`adapter/persistence`),`@Entity` 在 adapter,與 domain Order 互轉 |
| `CustomerReader` | `findById(String id) → Optional<Customer>`、`findByIds(Collection<String>) → Map<String,Customer>`(或等價批次查法) | 讀 H2 的 `CRM_CUSTOMER` 表,**唯讀**——adapter 不得提供任何寫入方法 |
| `ClockPort` | `now() → LocalDateTime` | 正式:系統時鐘。測試:固定時鐘(見 §Clock) |

## UC-1 下單(建立訂單)

輸入:`customerId`、`currency`、`items[]`(每條:`productName`、`quantity`、`unitPrice`)。

步驟:

1. 驗證輸入形狀(缺欄位、型別錯 → `VALIDATION_ERROR`)。
2. 以 `CustomerReader.findById(customerId)` 確認顧客存在;不存在 → `CUSTOMER_NOT_FOUND`。
3. 建構 `Order`(id = 新 UUID、`createdAt` = `ClockPort.now()`、status = `CREATED`)。domain invariant 違反(I-1 ~ I-6)→ `VALIDATION_ERROR`。
4. `OrderRepository.save(order)`。
5. 回傳建立結果(含系統算出的 `totalAmount`)。

規則重申:**request 沒有 total 欄位;總額一律由系統計算**(D-08:request 若夾帶未定義欄位,一律忽略)。

## UC-2 看訂單列表

1. `OrderRepository.findAll()` 取全部訂單。
2. 排序:`createdAt` **新到舊**;`createdAt` 相同時以 `id` 字典序遞增(D-09,確保測試可斷言順序)。
3. 每筆以 `CustomerReader` **讀取當下**解析顧客姓名(D-05);顧客已從 CRM 消失時 `customerName` 回 `null`(邊緣情況,不列驗收)。
4. 不分頁,一次回全部(D-09)。

## REST API

Base path:`/api`。Content-Type 一律 `application/json`。

### POST `/api/orders` — 下單

Request body:

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

成功 → **HTTP 201**,response body(不要求 `Location` header):

```json
{
  "orderId": "<UUID 字串,系統產生>",
  "customerId": "C001",
  "customerName": "王小明",
  "status": "CREATED",
  "statusLabel": "已成立",
  "currency": "TWD",
  "totalAmount": 799.00,
  "createdAt": "2026-08-11T10:15:30",
  "items": [
    { "productName": "運動鞋", "quantity": 2, "unitPrice": 350.00 },
    { "productName": "襪子", "quantity": 3, "unitPrice": 33.00 }
  ]
}
```

欄位規格:

| 欄位 | 型別 | 規則 |
|---|---|---|
| `orderId` | string | UUID 格式(測試斷言「非空字串」即可,不斷言值) |
| `customerName` | string | 從 CRM 表即時解析 |
| `status` | string | 恆 `"CREATED"` |
| `statusLabel` | string | 恆 `"已成立"`(映射在 adapter/web,D-06) |
| `totalAmount` | number | JSON number,恆 scale 2(如 `799.00`、`799.10`) |
| `createdAt` | string | ISO-8601 local date-time,格式 `yyyy-MM-dd'T'HH:mm:ss`,不含 timezone(D-10) |

### 建立失敗 → **HTTP 400**

Error body(兩種情況共用同一形狀):

```json
{ "error": "<錯誤碼>", "message": "<人讀的說明,內容不納入測試斷言>" }
```

| 錯誤碼(字面值) | 觸發條件 |
|---|---|
| `CUSTOMER_NOT_FOUND` | `customerId` 在 `CRM_CUSTOMER` 表查無 |
| `VALIDATION_ERROR` | 其他一切輸入不合法:`items` 缺/空、`quantity < 1`、`unitPrice < 0`、`unitPrice` scale > 2、`productName` 空白、`currency` 不符 `^[A-Z]{3}$`、`customerId` 空白、body 不是合法 JSON、缺必填欄位 |

所有建立失敗一律 400(不用 422;D-11)。失敗時**不得**留下任何已存的訂單(整個 UC 是原子的;H2 + 單一 transaction 即可)。

### GET `/api/orders` — 訂單列表

成功 → **HTTP 200**,body 是 JSON array(無訂單時 `[]`),每個元素:

```json
{
  "orderId": "…",
  "customerId": "C001",
  "customerName": "王小明",
  "status": "CREATED",
  "statusLabel": "已成立",
  "currency": "TWD",
  "totalAmount": 799.00,
  "createdAt": "2026-08-11T10:15:30"
}
```

- 列表元素**不含** `items`(主管要的列表欄位:誰買的、狀態、多少錢、哪天下的;明細不在列表需求內)。
- 排序:`createdAt` desc,tie-break `orderId` asc。
- 「誰買的」= `customerName`;「狀態中文」= `statusLabel` 恆 `"已成立"`;「總共多少錢」= `totalAmount` + `currency` 一起呈現(多幣別下缺幣別的金額無意義);「哪天下的」= `createdAt`。

### 不存在的操作

`PUT/PATCH/DELETE /api/orders/**` 一律不實作(成立即鎖定 + 取消修改 out of scope)。不需要為它們寫特殊 handler,Spring 預設的 405/404 行為即可,不列驗收。

## Clock(測試可控時間)

- `usecase/` 依賴 `ClockPort.now()`,不直接呼叫任何 ambient time API。
- 正式組態:實作回 `LocalDateTime.now(clock)`(系統 Clock)。
- 驗收測試組態:以 test configuration 覆蓋為**固定時鐘**,固定值 `2026-08-11T10:15:30`,使 `createdAt` 可精確斷言。需要區分先後順序的測試(排序測試)由測試自行對固定時鐘做遞增控制(例如可變的 test double,每次下單前撥快;見 `30-acceptance-tests.md` T-10)。
