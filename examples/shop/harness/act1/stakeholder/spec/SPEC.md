# 規格:下單與訂單列表

一個最小的訂單系統:一條 Command 路徑(下單)、一條 Query 路徑(訂單列表)。
詞彙見 [GLOSSARY.md](./GLOSSARY.md),架構規則見 [ARCHITECTURE.md](./ARCHITECTURE.md)。

## 端點(共 2 個,不多不少)

### `POST /orders` —— 下單(Command)

Request body:

```json
{
  "customerId": "C-001",
  "items": [
    { "productId": "P-100", "quantity": 2, "unitPriceCents": 1500, "currency": "TWD" }
  ]
}
```

Response:`201 Created`,body 至少含 `orderId`(字串)。

### `GET /orders` —— 訂單列表(Query)

Response:`200 OK`,JSON 陣列,每列的形狀即 `OrderListItem`:

```json
[
  {
    "orderId": "…",
    "customerName": "Alice",
    "statusLabel": "已成立",
    "totalCents": 5100,
    "placedAt": "2026-08-11"
  }
]
```

## 情境(Given-When-Then)

驗收套件 `app/src/test/java/acceptance/OrderAcceptanceTest.java` 是這些情境的
可執行版本,**以它為準**;下面是人讀的版本。

1. **Given** 一位存在的顧客 **When** 送出一筆含單一明細的訂單
   **Then** 回 `201` 並帶回 `orderId`。
2. **Given** 一筆已成立的訂單 **When** 查詢訂單列表
   **Then** 該筆出現在列表中,`statusLabel` 為「已成立」。
3. **Given** 訂單只持有 `CustomerId` **When** 查詢訂單列表
   **Then** 列表仍顯示顧客姓名(`customerName`,來自 `customers` 表)。
4. **Given** 一筆含多個明細的訂單 **When** 查詢訂單列表
   **Then** `totalCents` 等於各明細「數量 × 單價」的加總。
5. **Given** 一筆已成立的訂單 **When** 查詢訂單列表
   **Then** `placedAt` 是一個 ISO 日期(`YYYY-MM-DD`)。

## 領域規則(Aggregate 與契約)

這些規則是規格的一部分,與上面的情境同等效力:

- `Order` 是 Aggregate Root。**明細與總額的一致性由 `Order` 自己維護**:
  任何改變明細的操作,總額必須在同一個方法內重算。外部程式碼不得直接更動
  明細集合或總額。
- **`Order` 不得有任何 setter。** 狀態改變只能經由具領域意義的方法
  (如 `addItem(...)`、`place()`),而這些方法自己守自己的前置條件。
- **`Order.items()` 必須回傳複本**(如 `List.copyOf`),呼叫端拿到的集合
  改不到 `Order` 本體。
- `addItem(ProductId, int, Money)`:訂單非 `DRAFT` 時呼叫,丟
  `IllegalStateException` —— 這是呼叫方的 bug,不是業務例外。
- **`Money` 不同幣別不能相加**:對兩個幣別不同的 `Money` 做加法,必須丟例外。
  金額運算一律走 `Money`,不得把金額拆成裸的 `long` 在領域內傳遞。
- `Order` 只持有 `CustomerId`,不持有 Customer 物件(見 GLOSSARY「顧客」一節)。

## 明確不在範圍內

取消訂單、修改訂單、分頁、排序、查單筆訂單、庫存、驗證框架(Bean Validation)、
安全機制、OpenAPI 文件。**不要做。**
