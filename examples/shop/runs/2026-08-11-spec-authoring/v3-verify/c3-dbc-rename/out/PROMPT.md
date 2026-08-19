# PROMPT — 給實作 agent 的工作契約

你是實作 agent。依本 spec 包實作「下單/訂單列表」系統;驗收方式是自動化測試。

## 讀取順序

1. `GLOSSARY.md` — 命名鐵律,所有型別/變數/測試命名照表,禁用同義詞清單有列的字不得出現
2. `SPEC.md` — 端點、行為情境(GWT)、領域契約(Design by Contract)、明確不在範圍
3. `ARCHITECTURE.md` — package 佈局、相依方向、本案追加規則 R6–R12

## 凍結清單(不得修改的檔案)

- 本 spec 包五份文件:`GLOSSARY.md`、`SPEC.md`、`ARCHITECTURE.md`、`PROMPT.md`、`INTERVIEW-LOG.md`
- 常備模板(starter)附帶的:四條 ArchUnit 規則測試檔、Gradle build 檔(依賴已鎖死,不得增刪依賴)、既有 package 佈局

發現凍結檔案「有錯」或擋住你 → 不改檔,記入 `ASSUMPTIONS.md` 並用不違反它的方式繞。

## 要填的範圍

- `domain/`:Order(Aggregate Root)、OrderItem、Money、Currency、Quantity、OrderStatus、CustomerId、Customer、OrderRepository port、CustomerRepository port(唯讀)、Clock port(見 R12)
- `usecase/`:PlaceOrder、ListOrders
- `adapter/`:兩個 HTTP 端點(`POST /orders`、`GET /orders`,不多不少)、JPA/H2 持久化實作、CREATED→「已成立」表現層 mapping、transaction 邊界(R10)
- 測試:
  - SPEC 每條情境 S1–S10 各至少一個自動化測試,一比一對應(Given=測試前置資料、When=單一動作、Then=斷言)
  - 領域契約 C1–C9 的**指名測試**:測試類別與方法名必須與 SPEC「領域契約(Design by Contract)」表中所列完全一致(C10 無指名測試,由 R6 結構保證)
  - CRM 顧客表:測試中以預先塞入 H2 的資料代表(本系統唯讀,見 C10/R6)

## 完成的定義

**測試全綠**:模板四條 ArchUnit + S1–S10 情境測試 + C1–C9 指名測試,全部通過;且沒有實作任何「明確不在範圍」列的東西。

## 歧義處理

spec 未寫死的實作細節(如 orderId 產生方式、資料表欄位名、錯誤 body 其餘欄位),**自決並逐條記入 `ASSUMPTIONS.md`**(新建於本目錄):每條寫「遇到的歧義 / 你的決定 / 理由」。不得為了歧義新增端點、新增狀態值、或觸碰「明確不在範圍」清單。
