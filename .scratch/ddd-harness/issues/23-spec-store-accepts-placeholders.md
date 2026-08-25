# 23 — `spec_store.py import` 擋不擋佔位符沒驗過:一格 `TODO` 可能就這樣進了 `spec.db`

**What to build:** import 路徑加「prefill 守衛」:任一格是空字串、`TODO`、`[…]` 方括號佔位、
`<…>` 尖括號佔位、`FIXME`、`???`,整份拒絕匯入,逐格列出。

**Blocked by:** None

**Status:** done —— 2026-08-25 守衛落在 `spec_store.py` 的 `check_placeholders`(`build_store` 開頭、schema 之前),`test_prefill.py` 32 條,pytest 236 → 268 全綠;三份真實 yaml 第 0 階 0 / 0 / 0 命中、離開碼與訊息逐字不變(`23-PREDICTION.md` → `23-RESULT.md`,五條預測全命中)。兩處偏離票文:「空字串」只收 `""`、`[Qn]` 整格放行,都是儀器自己的測試語料逼出來的,理由見檔末〈落地〉。順手驗到 `acceptance_scenario.id` / `proxy_for` 的空白 CHECK 缺口,那是第 1 階的事,另開票。

## 哪裡壞了

`PIPELINE.md` 幕二的兩層檢查(schema CHECK / FK / TRIGGER + 跨列不變式)沒有一條問「這格是不是
還沒填」。`CHECK (length(x) > 0)` 有沒有、涵蓋哪些欄,**沒驗過**。幕二 agent 的完成定義是
「`import` 印 ok」—— 如果 `TODO` 能 ok,它就會交 `TODO`。

對照(驗過,survey §3 第 4 條):fspec `detect_prefill` 對 `[role]` / `[action]` / `TODO:` 等
字串擋所有前進轉移,並印「不要用 Write/Edit 直接替換 prefill」。

## 形狀

- 守衛在 `spec_store.py` 的 yaml → row 那一步,**在 schema 之前**;兩種失敗要分開印:
  「佔位符(第 0 階,連 schema 都還沒到)」vs「schema 拒絕(第 1 階)」。**不要折成同一個訊息**
  (票 14 缺陷一的教訓:兩種「沒東西」折成一種)。
- 佔位符清單寫成模組頂端的常數,**印在拒絕訊息裡**,讓 agent 知道被什麼擋。
- **⚠️ 合法的方括號**:GWT 步驟、wire 欄位名可能真的含 `[`。判準是「整格只有佔位符」
  (`^\s*\[[^\]]*\]\s*$`),不是「含有」。預測檔要釘:對三份真實 yaml
  (`runs/2026-08-18-act2-opus`、`2026-08-18-act2-rerun`、`2026-08-19-act2`)跑,**零命中**。
  有命中就是假陽性或真的漏,兩種都要寫進 RESULT。
- 註解不算格(`spec_store.py` 本來就丟掉註解 —— 票 15 那個問題本票**不碰**)。

## 受測品註記

`spec_store.py` 是幕二 agent 拿得到的輸入。加守衛 = 幕二 agent 從此看得到「什麼算沒填」,
**這是想要的**,但 2026-08-25 之後的第二幕跑不得與之前比基線(`run-meta.json` 已記輸入 blob)。

## 慣例(ADR 0007)

「yaml 不得含佔位符」由本守衛守。佔位符清單本身:prose-only, unenforced(清單漏了什麼只能靠 RESULT 補)。

## 完成的定義

- `test_prefill.py`(新檔):每種佔位符一例被拒;合法方括號一例通過;拒絕訊息含「第 0 階」字樣
  且列出格的路徑(`scenarios[2].given[0]` 這種)。
- `23-PREDICTION.md` → `23-RESULT.md`(三份真實 yaml 零命中那條)。
- `PIPELINE.md` 幕二「檢查兩層」表加第 0 階一列。

---

## 2026-08-25 · 落地

守衛:`spec_store.py` 頂端 `PLACEHOLDER_PATTERNS`(五條,每條頭尾錨)+ `EMPTY_ALLOWED_AT`
(唯一豁免:`acceptance_scenarios[*].rejected_requests[*].customer_id` 可以是 `""`,S7 未登入)
+ `check_placeholders(spec)`;`build_store` 第一件事就呼叫它,有命中就單獨 raise,
`_check_shape` 與 schema 都還沒跑到。訊息每行 `第 0 階 佔位符:<路徑> = <值>(<哪一種>)`,
最後一行印整份清單。離開碼維持 1。

**完成定義逐條**:`test_prefill.py` ✅(14 種寫法各一例被拒、`[Q7] 介面…` / 句中 TODO / 句中 `<orderId>`
放行、訊息含「第 0 階」與 `acceptance_scenarios[i].steps[0].items[0].product_id` 這種路徑、
第 2 階訊息**不含**「第 0 階」、`"   "` 是「schema 擋下來了」不是第 0 階);
PREDICTION → RESULT ✅(三份 0 / 0 / 0);PIPELINE 幕二表 ✅(「兩層」改「三層」,圖那行也補了)。

**兩處偏離票文,都是儀器自己的測試語料抓到的(不是真實 yaml)**:

1. **「空字串」只收恰好 `""`,「只有空白」不收。** `test_harness.py::test_來源為空寫不進去`
   (本票不准動)斷言 `provenance_ref: "   "` 的訊息是「schema 擋下來了」—— 空白格 = 第 1 階,
   這條邊界在本票之前就釘死了。第 0 階再收一次是同一條規則兩份載體。代價:沒有
   `length(trim)` CHECK 的欄(`acceptance_scenario.id`、`proxy_for` 驗過;`expected_text` /
   `field` 推斷)寫 `"   "` 會靜默進庫 —— 那是第 1 階缺口,另開票補 schema。
2. **`[Qn]` 整格放行。** 票釘的 regex `^\s*\[[^\]]*\]\s*$` 把 `provenance_ref: "[Q1]"` 判成佔位符,
   而 `test_glossary.py` / `test_domain_contract.py` 有 40 格拿它當合法值 —— 它是來源標記的寫法,
   是引用不是便條。改成 `^\s*\[(?!Q\d+\])[^\]]*\]\s*$`。對三份真實 yaml,原 regex 與新 regex
   都是 0 命中(真實 yaml 的 `[Q12]` 後面都接本文),差別只在儀器語料。

**慣例(ADR 0007)**:佔位符清單是 prose-only, unenforced —— 清單本身沒有 lint 守,
漏了哪一種寫法只能靠下一次 RESULT 補;守衛本身由 `test_prefill.py` 守。
