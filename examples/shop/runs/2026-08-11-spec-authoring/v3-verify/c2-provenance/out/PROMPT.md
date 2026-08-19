# PROMPT — 給實作 agent 的工作契約

你是實作 agent。依本 spec 包實作下單系統;驗收方式是自動化測試,沒有人工驗收。

## 讀件順序

1. `GLOSSARY.md` — 命名鐵律,先讀。
2. `SPEC.md` — 端點、GWT 情境、領域規則(DbC)、明確不在範圍。
3. `ARCHITECTURE.md` — 模板既定 + 本案自決規則。

## 凍結清單(不得修改)

- `GLOSSARY.md`、`SPEC.md`、`ARCHITECTURE.md`、`INTERVIEW-LOG.md`、本檔 `PROMPT.md`。
- 公司 starter 模板既有內容:Gradle build 設定(鎖死依賴)、四條 ArchUnit 規則、
  `domain/ usecase/ adapter/` package 骨架。可新增測試,不得修改或刪除既有規則與 build 約束。

## 要填的範圍

- `src/main/java` 之 `domain/`、`usecase/`、`adapter/` 下的實作。
- `src/test/java` 下 SPEC 指名的全部測試(名字照 SPEC,一比一)。
- 必要的 `src/main/resources` / `src/test/resources`(H2 schema、顧客表 seed 資料)。
- 有歧義時新建 `ASSUMPTIONS.md`(見下)。

## 完成的定義(全部滿足才算完成)

1. SPEC.md 八個指名測試全數存在且**全綠**:
   `place_order_computes_total_and_persists`、`client_supplied_total_is_ignored`、
   `unknown_customer_rejected_no_residue`、`empty_lines_rejected_no_residue`、
   `quantity_below_one_rejected_no_residue`、`negative_unit_price_rejected_no_residue`、
   `list_shows_buyer_status_total_date`、`mutation_attempts_rejected_order_unchanged`。
2. 模板四條 ArchUnit 規則全綠。
3. Gradle build 成功。
4. 端點恰為 `POST /orders`、`GET /orders` 兩個,無多無少。
5. 「明確不在範圍」各項一律未實作。

## 歧義處理

- **不回頭問人。** 遇到 spec 未定的技術細節,自行決定,並在 `ASSUMPTIONS.md`
  逐條記錄:編號、遇到的歧義、你的決定、一句理由、影響的檔案。
- 命名歧義不存在自決空間:一律照 GLOSSARY,禁用清單上的詞出現即違規。
- 領域行為歧義(spec 沒說的行為)不得自行展開:視同「規格沉默」,不做,
  並記入 `ASSUMPTIONS.md` 註明「未實作,規格沉默」。
