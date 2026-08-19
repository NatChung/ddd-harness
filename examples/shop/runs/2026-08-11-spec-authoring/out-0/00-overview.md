# 訂單系統規格 — 總覽

> 讀者:AI 實作 agent。驗收方式:自動化測試(見 `30-acceptance-tests.md`)。
> 需求來源:2026-08 營運主管訪談逐字稿。逐字稿沒講到、由規格作者自行裁定的事項,全部集中在 `DECISIONS.md`。

## 文件地圖

| 檔案 | 內容 |
|---|---|
| `00-overview.md`(本檔) | 範圍、技術棧、架構約束、out of scope |
| `10-domain-model.md` | Ubiquitous language、aggregate、invariant |
| `20-api-and-use-cases.md` | Use case、REST API 契約(含所有欄位與錯誤碼的字面值) |
| `30-acceptance-tests.md` | 驗收測試清單(逐條、含斷言用的字面值)與 CRM seed 資料 |
| `DECISIONS.md` | 逐字稿之外的規格決定,逐條附理由 |

實作時以本組文件為唯一需求來源。四份規格文件若有衝突,以 `30-acceptance-tests.md` 的字面值為準(它是驗收的最終依據)。

## 需求範圍(逐字稿有依據的部分)

1. **下單**:客人能建立訂單。
2. **看列表**:能看到所有訂單,每筆顯示:誰買的、狀態(中文「已成立」)、總金額、下單日期。
3. **成立即鎖定**:訂單一旦建立就不可變。不提供任何修改/取消功能。
4. **顧客資料讀 CRM**:顧客名單由 CRM 維護,本系統**只讀**。資料形狀:一張表,顧客編號 + 姓名。本系統不做會員系統、不寫入顧客資料。
5. **幣別**:訂單有幣別;一張訂單內只有一種幣別(不混)。
6. **總額由系統計算**:每條明細 `數量 × 單價` 加總。client 不提供總額。

## Out of scope(明確不做,不要預留)

- 取消訂單、修改訂單(主管:「先不用,以後再說」)——**不要**預先建 `CANCELLED` 之類的狀態、不要留 update/delete endpoint、不要做狀態機。
- 會員系統、註冊/登入、認證授權。
- 商品目錄(product catalog)——逐字稿沒有商品主檔的需求,明細品名為自由文字(見 DECISIONS D-03)。
- 分頁、搜尋、篩選(見 DECISIONS D-09)。
- 寫入 CRM 顧客表。

## 技術棧(已定,不可改)

- Java 17、Spring Boot、Spring Data JPA、H2(in-memory)、Gradle。
- 使用公司常備 starter:三層 package 佈局 + ArchUnit 規則 + 鎖死依賴的 build。

## 架構約束(starter 的 ArchUnit 規則,實作必須通過)

Package 佈局三層:`domain/`、`usecase/`、`adapter/`。四條規則:

1. `domain` 不 import 框架(Spring、JPA、Jackson 等一律禁止)。
2. `usecase` 不 import 框架。
3. `domain` 不 import 上層(`usecase`、`adapter`)。
4. `usecase` 不 import `adapter`。

**由此推導出的強制實作方式**(這是最容易踩的坑,明確寫死):

- JPA `@Entity`、`@Table` 等註解的 class **只能放在 `adapter/`**(persistence adapter),並與 `domain/` 的純 Java 物件互相轉換(mapping)。**禁止**在 domain 物件上加任何 JPA/Spring/Jackson 註解。
- Spring Data repository interface(`extends JpaRepository` 等)屬於框架,只能在 `adapter/`。
- `usecase/` 定義純 Java 的 port interface(如 `OrderRepository`、`CustomerReader`、`ClockPort`),`adapter/` 提供實作並由 Spring 組裝。依賴方向:`adapter → usecase → domain`。
- `@RestController`、request/response DTO、JSON 序列化都在 `adapter/`。
- 時間取得走 `usecase/` 的 port(見 `20-api-and-use-cases.md` §Clock),不得在 domain/usecase 直接呼叫 `LocalDateTime.now()` 之類的 ambient time——驗收測試需要固定時鐘。

## 資料庫

- H2 in-memory,兩張表:
  - `CRM_CUSTOMER`(顧客編號、姓名)——模擬 CRM 那張表,本系統**唯讀**。正式啟動時由 `src/main/resources/data.sql` 灌 seed(seed 內容與驗收測試共用,字面值定義在 `30-acceptance-tests.md` §CRM seed)。
  - 訂單相關表(orders / order_items)——本系統擁有、可寫。
- Schema 由 JPA 自動建立即可(H2 + `ddl-auto`),不需要 migration 工具。
