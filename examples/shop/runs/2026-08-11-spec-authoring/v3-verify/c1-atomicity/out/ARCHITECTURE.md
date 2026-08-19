# ARCHITECTURE — 下單系統

技術棧(已定):Java 17、Spring Boot、Spring Data JPA、H2、Gradle。

## 常備模板(starter,原樣沿用)

### Package 佈局(三層)

```
<root>/
├── domain/     # Order、OrderLine、Money、Currency、OrderStatus、Repository 介面
├── usecase/    # PlaceOrder、ListOrders
└── adapter/    # REST controller、JPA 實作、DB schema、顯示轉換
```

### 相依方向與框架隔離(四條通用 ArchUnit 規則,starter 內建)

| 規則 | 機械檢查 |
|---|---|
| domain 不 import 框架(Spring/JPA/Jakarta 等) | ✅ ArchUnit(starter) |
| usecase 不 import 框架 | ✅ ArchUnit(starter) |
| domain 不 import 上層(usecase、adapter) | ✅ ArchUnit(starter) |
| usecase 不 import adapter | ✅ ArchUnit(starter) |

Repository 介面宣告在 domain,JPA 實作在 adapter(依賴反轉)。build 已鎖死依賴,不得增刪。

## 本案特有規則(只追加,不重複模板)

| # | 規則 | 說明 | 機械檢查 | 回鏈 |
|---|---|---|---|---|
| A1 | **Customer 唯讀邊界** | 顧客資料由 CRM 維護;本系統只有一張唯讀 `customers` 表(欄位:`customer_id`, `customer_name`),以 schema/測試 fixture 建立。`CustomerRepository` 介面**只宣告查詢方法**,不得存在任何寫入 Customer 的 code path;系統不提供任何顧客端點 | ⛔ 非機械——由 SPEC 端點清單「不多不少」+ PROMPT 凍結的介面形狀 + code review 把關 | [Q2][Q3] |
| A2 | **交易邊界在 usecase** | `PlaceOrder` 是單一交易單位:驗證 + 建立 Order + 持久化(orders + order_lines)全有全無;任何失敗路徑回滾,不留孤兒列 | ✅ 測試強制:`PlaceOrderAtomicityTest`(SPEC S8)+ S3–S7 的「訂單數不變」斷言 | [Q9] |
| A3 | **金額表示** | 全系統金額為 cents 整數(Java `long`/`int`);domain、DB、API 三處皆整數,禁止 `double`/`float`/`BigDecimal` 表示金額 | ⛔ 非機械——由 GLOSSARY 命名鐵律(`unitPriceCents`/`totalCents`)+ 測試中的整數斷言把關 | [Q13] |
| A4 | **顯示轉換放 adapter** | domain 的 `OrderStatus` 為 enum `CREATED`,不含中文字串;「已成立」的中文顯示值只存在於 adapter 層的回應轉換 | ✅ 部分機械:starter ArchUnit 已保證 domain 純淨;中文值正確性由 `OrderStatusDisplayTest`(SPEC S1/S9)斷言 | [Q5][Q13] |
| A5 | **Order 不可變** | domain 的 `Order` 建構完成後無公開 mutator;JPA mapping 細節(如框架要求的存取方式)放 adapter 或以 JPA 慣用手法處理,不得因此在 domain 開放公開變更方法 | ✅ 測試強制:`OrderImmutabilityTest`(SPEC R1) | [Q1] |
| A6 | **讀寫佈局** | 寫入路徑只有 `PlaceOrder`;讀取路徑 `ListOrders` 需要 join `customers` 取姓名——此 join 屬查詢組裝,放 adapter/usecase 的讀取側,不得為此在 Order aggregate 裡冗餘存姓名 | ⛔ 非機械——code review 把關 | [Q5][Q3] |

## 資料表(H2)

- `customers`(唯讀,fixture 預載):`customer_id`(PK)、`customer_name` [Q3]
- `orders`:`order_id`(PK)、`customer_id`、`currency`、`total_cents`、`status`、`placed_at` [Q13]
- `order_lines`:隸屬 `orders`(FK,隨訂單同交易寫入)、`product_name`、`quantity`、`unit_price_cents` [Q8]

幣別只存在 `orders` 層,`order_lines` 無幣別欄位(單一幣別由結構保證,SPEC R6)。[Q4]
