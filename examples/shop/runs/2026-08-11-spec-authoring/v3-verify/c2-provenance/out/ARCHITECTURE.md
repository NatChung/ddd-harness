# ARCHITECTURE — 下單系統

每條規則標出處:**「模板既定」**(逐字有據於公司常備模板 / 工程前提)或
**「本案自決」**(附 [Qn] 或 ASSUMPTIONS 依據)。並標注是否由機械檢查強制。

## 一、模板既定(逐字承自常備 starter,不得增刪)

| # | 規則 | 機械檢查 |
|---|---|---|
| T1 | 技術棧:Java 17、Spring Boot、Spring Data JPA、H2、Gradle | build(鎖死依賴) |
| T2 | 三層 package 佈局:`domain/ usecase/ adapter/` | ArchUnit(下列規則以此佈局為前提) |
| T3 | domain 不 import 框架 | ArchUnit(模板四條之一) |
| T4 | usecase 不 import 框架 | ArchUnit(模板四條之一) |
| T5 | domain 不 import 上層 | ArchUnit(模板四條之一) |
| T6 | usecase 不 import adapter | ArchUnit(模板四條之一) |
| T7 | 鎖死依賴的 build | Gradle build |

模板既定條目僅上述七條;**本檔其餘一切規則皆為本案自決**,不得把推論偽裝成既定。

## 二、本案自決(僅追加本案特有規則)

| # | 規則 | 依據 | 機械檢查 |
|---|---|---|---|
| A1 | Repository 介面(`OrderRepository`、`CustomerRepository`)放 domain,實作放 adapter | 本案自決 [Q0][Q1](需存訂單、讀顧客表);落點是 T3/T5 相依方向約束下的設計選擇 | 佈局本身無機械檢查;其 import 後果由 T3–T6 覆蓋 |
| A2 | `CustomerRepository` 只有查詢方法,**不得有任何寫入方法**;系統永不寫入顧客表 | 本案自決 [Q1][Q2](CRM 維護、我們唯讀) | 無機械檢查;實作 agent 自律,違反即違規 |
| A3 | 顧客表在本系統以 H2 的表 + seed 資料模擬 CRM 供讀(測試自備顧客資料) | 本案自決 [Q1][Q2] + ASSUMPTIONS(CRM 實際介接方式規格沉默,本輪以本地表代) | SPEC 各情境的 Given 由測試強制 |
| A4 | Order 寫入後不再修改:`OrderRepository` 不暴露 update/delete;不存在任何修改端點 | 本案自決 [Q8][Q9] | 部分由指名測試 `mutation_attempts_rejected_order_unchanged` 強制;介面形狀靠實作 agent 自律 |
| A5 | OrderStatus 在 domain 為 enum `CREATED`;中文顯示「已成立」的映射放 adapter(回應組裝),domain / usecase 不含顯示字串 | 本案自決 [Q10][Q11] | 顯示值由 `list_shows_buyer_status_total_date` 強制;放置位置靠自律 |
| A6 | 金額在 domain 一律最小貨幣單位整數(Money VO),禁止浮點 | 本案自決 [Q11] | 數值正確性由 S1/S2/S7 測試覆蓋;型別選擇靠自律 |
| A7 | 寫入原子性:Order 與其全部 OrderLine 屬同一 aggregate,一次寫入(全有或全無);交易邊界落在 adapter 層(usecase 依 T4 不得 import 框架,故不得使用 `@Transactional` 等框架註記) | 本案自決 [Q3][Q5](SPEC R6);交易邊界落點是 T4 約束下的設計選擇 | 由四個 `*_no_residue` 指名測試強制 |
| A8 | 讀寫佈局:PlaceOrder(寫)與 ListOrders(讀)為兩個獨立 use case,列表所需的顧客姓名在讀取路徑組裝(join 顧客表),不冗餘存進 Order | 本案自決 [Q0][Q10];組裝位置屬技術歧義,實作 agent 可另決並記 ASSUMPTIONS | 輸出形狀由 `list_shows_buyer_status_total_date` 強制 |
