# 實作假設與設計決定

## 總結

共 7 項設計決定與假設：

## 決定列表

### 1. OrderId 生成策略

**決定：使用 UUID 字首化生成**

訂單 ID 生成策略採用 `"ORD-" + UUID.randomUUID().substring(0, 8).toUpperCase()`。

**理由：**
- 規格沒有指定 ID 生成策略，所以由 adapter 層自主決定
- UUID 保證全域唯一性，符合生產環境需求
- 字首 "ORD-" 使 ID 易於識別和調試

### 2. JPA Entity 層次設計

**決定：OrderEntity + OrderItemEntity（@OneToMany 關係）**

OrderItem 作為完整的 JPA entity（而非 Embeddable），透過 @OneToMany 與 OrderEntity 建立關係。

**理由：**
- 支援多條明細的靈活查詢和操作
- OrderItemEntity 不直接暴露給 usecase 層，維持封裝
- 適合 CQRS 架構中的 Query 側直接查詢

### 3. Query 側實作方法

**決定：使用 JdbcTemplate 直接查詢 SQL，不經過 JPA entity 再轉換**

OrderQueryRepository 透過 JdbcTemplate 執行 SQL 聯接 orders 與 customers 表，直接組成 OrderListItem View Model。

**理由：**
- 符合 CQRS 原則：Query 側專用、效率高
- 避免將 Order Aggregate 從資料庫再讀出並轉換的額外開銷
- 直接聯接 customers 表取得顧客姓名，無須經過領域層

### 4. Command 側的狀態轉移

**決定：save() 時填入 placedAt 日期為 LocalDate.now()**

當訂單狀態是 PLACED 時，設定 placedAt 為當前日期。

**理由：**
- 規格要求 placedAt 是 ISO 日期格式（YYYY-MM-DD）
- 訂單在 use case 層的 Order.place() 時狀態已變成 PLACED
- adapter 層在保存時記錄該時刻的日期，無須額外參數

### 5. StatusLabel 對應規則

**決定：OrderStatus.PLACED → "已成立"，DRAFT → "草稿"**

OrderQueryRepository 中的 mapToOrderListItem 方法根據 JPA 的 status 欄位值決定 statusLabel。

**理由：**
- 規格明確要求 PLACED 顯示為「已成立」
- DRAFT 作為內部狀態存在，但根據規格不會在列表中出現（一律成立後才存）

### 6. 控制器 DTO 層次

**決定：OrderController 內部定義 request/response DTO，與 usecase 層的請求物件分開**

- PlaceOrderRequestDto / OrderItemRequestDto：用於 HTTP 請求解析
- OrderListItemDto：用於 HTTP 回應序列化
- 內部轉換為 PlaceOrderRequest / OrderListItem（usecase 層的物件）

**理由：**
- 隔離 HTTP 層與業務層的詞彙
- HTTP DTO 可靈活調整序列化邏輯（如日期格式）
- usecase 層不知道 HTTP 存在

### 7. 依賴注入與配置

**決定：使用 Spring @Component + @Configuration 進行自動配置**

- OrderEntityRepository：Spring Data JPA 自動掃描
- JpaOrderRepository：@Component，自動注入 OrderEntityRepository
- JpaOrderQueryRepository：@Component，自動注入 JdbcTemplate
- AdapterConfiguration：定義 usecase bean，注入 repository 實作

**理由：**
- 充分利用 Spring Boot 自動配置
- 相依性倒轉原則：usecase 層只看到介面（OrderRepository、OrderQueryRepository），不知道 JPA 實作
- 測試時易於替換實現

## 規格與 schema 無修改

- 未修改 data.sql 或 application.properties（都是 harness 提供）
- 未修改任何驗收測試或 ArchitectureTest
- domain 層和 usecase 層的任何程式碼都未改動
