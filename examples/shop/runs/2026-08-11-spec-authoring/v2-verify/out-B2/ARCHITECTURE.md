# ARCHITECTURE — 訂單系統(本輪)

技術棧:Java 17、Spring Boot、Spring Data JPA、H2、Gradle。
本檔前半為公司常備模板(starter)既定內容,後半只追加本案特有規則。

## 常備模板(starter 既定,不得偏離)

### Package 佈局(三層)

```
<root>
├── domain/     # Entity、Value Object、Aggregate、Repository 介面、領域規則
├── usecase/    # Use Case(Application Service)、輸入/輸出 DTO、交易邊界
└── adapter/    # REST controller、JPA 實作、Spring 設定、顯示轉換
```

### 相依方向

`adapter → usecase → domain`,只准往內,不准往外、不准跳層往回。

### 框架隔離

- Spring、Spring Data JPA、Jakarta 等框架 import **只允許出現在 `adapter/`**。
- `domain/` 與 `usecase/` 為純 Java;usecase 的 bean 註冊由 adapter 層的
  `@Configuration` 完成,usecase 類別本身不掛框架 annotation。
- Repository 介面定義在 `domain/`,JPA 實作放 `adapter/`。

### 機械檢查(starter 既有四條 ArchUnit 規則)

| # | 規則 | 強制方式 |
|---|---|---|
| G1 | domain 不 import 框架 | ArchUnit(starter 既有) |
| G2 | usecase 不 import 框架 | ArchUnit(starter 既有) |
| G3 | domain 不 import 上層(usecase/adapter) | ArchUnit(starter 既有) |
| G4 | usecase 不 import adapter | ArchUnit(starter 既有) |

依賴版本由 starter 的 build 鎖死,實作不得增刪依賴(見 PROMPT.md 凍結清單)。

## 本案特有規則(只此追加)

| # | 規則 | 說明 | 強制方式 | 回鏈 |
|---|---|---|---|---|
| A1 | `CustomerRepository` 唯讀 | 介面**只有查詢方法**(如 `findById`),不得有 save/update/delete;JPA 實作亦不得暴露寫入。 | 介面形狀 + code review;**本案追加**、建議自訂 ArchUnit 規則(CustomerRepository 之方法不得以 save/delete/update 開頭),非 starter 既有 | [Q2] |
| A2 | `customers` 表由 CRM 擁有 | 本系統視其為外部資料:不遷移、不寫入;測試以 seed SQL 建表與資料模擬 CRM(H2)。JPA mapping 標記唯讀。 | code review + 測試 seed 慣例 | [Q2][Q3] |
| A3 | 金額型別鎖 `long`(最小幣值單位) | domain/usecase/adapter 全線金額欄位用 `long`;**禁止 `float`/`double`/`BigDecimal` 表示金額**。 | **本案追加**:實作 agent 需新增一條 ArchUnit 自訂規則——`domain/` 與 `usecase/` 內禁止出現 `float`/`double` 型別欄位與參數;此規則檔屬新增,不動 starter 既有四條;`BigDecimal` 不易機械檢查,由 code review 把關 | [Q9] |
| A4 | 中文顯示屬 adapter 層 | 「已成立」字面**只允許出現在 `adapter/`**(`CREATED` → statusLabel 的顯示轉換);domain/usecase 一律用 enum `CREATED`。 | code review(無機械檢查) | [Q13][Q14] |
| A5 | Order 無更新語意 | `OrderRepository` 只有新增(save-on-create)與查詢;無 update/delete 方法。Order 與 OrderItem 實作為 immutable(欄位 final、無 setter)。 | 介面形狀 + code review(無機械檢查);API 面由端點清單(SPEC E1/E2,不多不少)強制 | [Q10] |
| A6 | 讀寫佈局:不另建 read model | 列表查詢走 `ListOrdersUseCase`,於 usecase 內以 `CustomerRepository` 取 `customerName` 組合輸出 DTO;本輪規模不建 CQRS/read model。 | code review | [Q14][Q15] |

## 邊界例外

無。本案沒有允許跨層的例外;實作中若覺得需要開例外,停下來回報,不得先斬後奏。
