# 訂單系統規格 — Domain Model

> `domain/` package 的內容物與規則。全部是純 Java(Java 17),不 import 任何框架。

## Ubiquitous language

| 中文 | 英文(code 用) | 定義 |
|---|---|---|
| 訂單 | `Order` | Aggregate root。客人一次下單的結果,成立後不可變。 |
| 訂單明細 | `OrderItem` | 訂單內的一條品項:品名、數量、單價。Value object,只存在於 Order 之內。 |
| 訂單狀態 | `OrderStatus` | Enum。目前只有一個值 `CREATED`(對外顯示「已成立」,顯示映射在 adapter,見 D-06)。 |
| 顧客 | `Customer` | CRM 維護的讀取模型:顧客編號 + 姓名。**不是**本系統的 aggregate,本系統唯讀。 |
| 幣別 | currency | ISO 4217 三碼大寫(如 `TWD`、`USD`)。訂單層級屬性。 |
| 總額 | total amount | 系統計算:Σ(明細數量 × 單價),normalize 到 scale 2。 |
| 下單時間 | `createdAt` | 訂單建立當下的時間,由 Clock port 提供。 |

## Aggregate:Order

### 欄位

| 欄位 | 型別 | 說明 |
|---|---|---|
| `id` | `String` | 系統產生的 UUID 字串(D-07)。 |
| `customerId` | `String` | CRM 顧客編號。Order 只持有編號,**不 snapshot 姓名**(D-05)。 |
| `currency` | `String` | ISO 4217 三碼大寫。訂單層級單一幣別——幣別放訂單層而非明細層,「一張訂單不混幣別」由結構保證(D-04)。 |
| `items` | `List<OrderItem>` | 至少 1 條。不可變 list。 |
| `status` | `OrderStatus` | 恆為 `CREATED`。 |
| `createdAt` | `LocalDateTime` | 建構時傳入(來自 Clock port)。 |

### OrderItem(value object)

| 欄位 | 型別 | 說明 |
|---|---|---|
| `productName` | `String` | 自由文字品名,非空白(D-03)。 |
| `quantity` | `int` | 整數,≥ 1。 |
| `unitPrice` | `BigDecimal` | ≥ 0,小數位數(scale)≤ 2。 |

### 行為

- `Order.totalAmount()`:回傳 `BigDecimal` = Σ(`quantity` × `unitPrice`),以 `setScale(2)` normalize(quantity 是整數、unitPrice scale ≤ 2,乘加不會產生 scale > 2,故 `setScale(2)` 不涉及捨入)。總額**只能算出來**,不能由外部設定——Order 沒有 total 欄位的 setter,建構參數也沒有 total。
- **不可變**:Order 與 OrderItem 建構完成後沒有任何 mutator(對應「成立即鎖定」)。建議用 `record` 或 final 欄位 + 防禦性複製實作。

### Invariant(建構時強制,違反丟 domain exception)

| # | Invariant |
|---|---|
| I-1 | `items` 非 null 且至少 1 條 |
| I-2 | 每條明細 `quantity ≥ 1` |
| I-3 | 每條明細 `unitPrice ≥ 0` 且 scale ≤ 2 |
| I-4 | 每條明細 `productName` 非 null、trim 後非空 |
| I-5 | `currency` 符合 `^[A-Z]{3}$`(只驗格式,不驗 ISO 4217 清單;D-04) |
| I-6 | `customerId` 非 null、trim 後非空 |

違反 invariant 時丟一個 domain 層的 unchecked exception(例如 `InvalidOrderException`,純 Java,放 `domain/`)。「顧客必須存在於 CRM」**不是** domain invariant——domain 看不到 CRM,存在性檢查在 usecase 做(見 `20-api-and-use-cases.md` UC-1 步驟 2)。

## OrderStatus

```java
public enum OrderStatus { CREATED }
```

只有一個值。**不要**加 `CANCELLED`、`MODIFIED` 等「以後可能用到」的值(out of scope,見總覽)。中文標籤「已成立」不放在 domain enum 上——那是顯示關注點,映射表放 adapter(D-06)。

## Customer(讀取模型)

```java
// domain/,純 Java
public record Customer(String id, String name) {}
```

代表 CRM 那張表的一列。本系統對它沒有任何寫入行為、沒有 invariant 要維護(資料品質由 CRM 負責)。取得方式:usecase 的 `CustomerReader` port(見 `20-api-and-use-cases.md` §Ports)。
