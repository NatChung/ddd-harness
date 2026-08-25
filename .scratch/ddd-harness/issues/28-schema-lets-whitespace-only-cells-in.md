# 28 — schema 的空字串 CHECK 只擋 `""`:`acceptance_scenario.id` 寫 `"   "` 會靜默進庫

**What to build:** `schema.sql` 對所有「不得為空」的文字欄改成 `CHECK (length(trim(x)) > 0)`;
補一支測試釘每個欄位。

**Blocked by:** None

**Status:** needs-triage —— 2026-08-25 票 23 落地時發現(`23-RESULT.md` 探針),尚未開工。

## 哪裡壞了

票 23 的第 0 階守衛原本想連「只有空白」一起擋,但 `test_harness.py::test_來源為空寫不進去`
釘死 `provenance_ref: "   "` 的訊息是「schema 擋下來了」—— 那格是第 1 階的事。
守衛因此只收恰好 `""`。**驗過**(票 23 探針):`acceptance_scenario.id` 與 `proxy_for` 寫 `"   "`
會靜默進庫。**推斷**未驗:`expected_text` / `field` 同樣沒擋。

也就是 schema 對「空」的定義不一致:有的欄 `length(x) > 0`,有的欄有 `trim`,有的欄沒 CHECK。
第 1 階應該一致,不然第 0 階永遠不知道自己該擋到哪。

## 形狀

- 先列表:`schema.sql` 每個 TEXT 欄的 CHECK 現況(有 / 無 / 有 trim),寫進 `28-PREDICTION.md`。
- 一律改成 `length(trim(x)) > 0`;選填欄明寫 `NULL` 允許、空字串不允許。
- 測試放新檔 `test_schema_blank.py`,每欄一例 `"   "` 被拒。
- ⚠️ 動 `schema.sql` = 動幕二受測輸入,`PIPELINE.md` 幕二那句「2026-08-25 起不得與之前比基線」已涵蓋。

## 慣例(ADR 0007)

「文字欄不得只有空白」由 schema CHECK 守;`harness_lint` 規則名:無(這是 schema 的事,不是票的規約)。
