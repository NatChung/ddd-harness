# PROMPT — 給實作 agent 的工作契約

你是實作 agent。依本 spec 包在公司 starter 專案上實作「訂單系統(本輪範圍)」。
驗收方式是自動化測試;讀者與審計者都會拿 SPEC 逐條對照你的產出。

## 讀取順序

1. `GLOSSARY.md` — 命名鐵律與禁用清單,實作命名唯一依據
2. `SPEC.md` — 端點、行為情境(GWT)、領域規則(DbC)、明確不在範圍
3. `ARCHITECTURE.md` — 三層佈局、四條既有 ArchUnit 規則、本案特有規則 A1~A6
4. 疑義時回查 `INTERVIEW-LOG.md` 的對應 `[Qn]`

## 凍結清單(不得修改)

- `GLOSSARY.md`、`SPEC.md`、`ARCHITECTURE.md`、`INTERVIEW-LOG.md`、本檔 `PROMPT.md`
- starter 的 `build.gradle` / `settings.gradle` / 依賴鎖定檔(不得增刪依賴)
- starter 既有的四條 ArchUnit 規則測試(G1~G4)——不得修改、不得弱化;
  A3 要求的自訂規則**另開新測試檔追加**,不動既有檔

## 要填的範圍

- `src/main/java` 下的 `domain/`、`usecase/`、`adapter/` 三層實作
- `src/test/java` 下:
  - SPEC「領域規則」表指名的單元測試(類名/方法名照表,R4/R7/R9 型別面除外)
  - SPEC「行為情境」S-01~S-10 一比一翻成的整合測試(Spring Boot test + H2)
  - A3 的 ArchUnit 自訂規則(新檔)
- H2 設定與測試 seed(`customers` 表模擬 CRM,唯讀;見 ARCHITECTURE A2)
- `ASSUMPTIONS.md`(見下)

## 完成的定義(全部滿足才算完成)

1. `./gradlew test` 全綠。
2. SPEC 指名測試(R1、R2、R3、R5、R6、R8 對應者)全部存在且綠。
3. S-01~S-10 每條有對應的自動化測試且綠;斷言值與 SPEC 完全一致(金額為最小幣值單位整數)。
4. ArchUnit:starter 四條 + A3 自訂規則,全綠。
5. 端點不多不少:只有 `POST /orders`、`GET /orders`。
6. 命名零違規:GLOSSARY 禁用同義詞清單中的名字不得出現在任何識別字。

## 歧義自決規則

- **規格沉默 ≠ 授權展開。**「明確不在範圍」列的項目一律不做;未列出但 SPEC 也沒規定的實作細節(如 orderId 產生方式、JSON 欄位序、package 內部再分包),自行決定。
- 每一條自決,**逐條記入 `ASSUMPTIONS.md`**:決定內容、一句理由、影響的檔案。
- 不得因自決而:新增端點、新增/改名 API 欄位、放寬領域規則、引入禁用同義詞。
- 若遇到「不決定就寫不下去、且決定會改變對外行為」的歧義:停下來回報,不要猜。
