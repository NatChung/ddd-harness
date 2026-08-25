# 23 — `spec_store.py import` 擋不擋佔位符沒驗過:一格 `TODO` 可能就這樣進了 `spec.db`

**What to build:** import 路徑加「prefill 守衛」:任一格是空字串、`TODO`、`[…]` 方括號佔位、
`<…>` 尖括號佔位、`FIXME`、`???`,整份拒絕匯入,逐格列出。

**Blocked by:** None

**Status:** needs-triage —— 2026-08-25 Nat 拍板要做(survey §9 #4),尚未開工。

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
