# 25 — 檢查器沒有考卷:`landing_check` / `provenance_check` 只對三四份真實 run 驗過,沒有已知陽性 + 已知陰性的固定語料

**What to build:** `tools/harness/fixtures/exams/<checker>/<case>/`,每個 case 一份輸入 + `expected.json`;
一支 `exam.py` 跑全部並印命中 / 落空 / 假陽性;進 pytest。

**Blocked by:** None

**Status:** needs-triage —— 2026-08-25 Nat 拍板要做(survey §9 #9),尚未開工。

## 哪裡壞了

`PIPELINE.md` 每支檢查器的「驗過沒有」寫的是「對 N 份真實 run 驗過」—— 那是一次性的手動比對,
改了檢查器之後**沒有東西會自動再比一次**。幕五的定義「改了但沒重跑 = 沒閉環」,
對檢查器本身今天做不到。

對照(驗過,survey §3 第 12 條與 §6 判斷 6):Agentheim `evals/verifier-catch-rate/fixtures/`
16 個埋已知缺陷的 case(`vocab-violation`、`stale-readme`、`scope-creep`、`missing-ac`、
`clean`…),重跑量命中率,抓到過 gate 措辭的洞、改完能重跑證明。**抄考卷,不抄他們的 LLM verifier。**

## 形狀

- 第一批四支:`landing_check`、`provenance_check`、`glossary_check`、`contract_triage`。
  每支至少:1 個 `clean`(預期 0)、1 個已知陽性(預期 1 且命中指定項)、1 個不適用(預期 3)。
- **已知陽性從真實 run 抽最小片段**,不複製整個 run 目錄(`examples/**/runs/` 不動;
  fixture 是**新的、精簡的**檔)。例:haiku roleplay 那兩輪整段消失的 8 題 → 一個
  `landing_check/missing-two-rounds/`;opus 那場 100/120 的來源標記 → `provenance_check/fed-then-attested/`。
- 題號寫法漂掉(`**Q1:`)那個 case **必須有**(`PIPELINE.md` 幕一 2026-08-18 那段的實測)。
- `expected.json`:`{"exit": 3, "must_print": ["不適用"], "must_not_print": ["通過"]}` 這種形狀,
  **離開碼與字串都釘**。
- `exam.py` 印一張表:checker / case / 預期 / 實際 / 命中;任何落空離開碼 1;
  沒有任何 case 離開碼 3。

## 慣例(ADR 0007)

「每支檢查器要有考卷」—— 由 `exam.py` 守一半:它列出 `tools/harness/*_check.py` / `*_triage.py`
裡**沒有** `fixtures/exams/<name>/` 的,印成「無考卷」佇列(不是判決)。

## 完成的定義

- `test_exam.py`(新檔)跑 `exam.py`,全部命中。
- `25-PREDICTION.md`:寫下每個 case 預期的離開碼**再**跑;預期至少一個 case 會落空
  (不落空反而要懷疑考卷太簡單,寫進 RESULT)。→ `25-RESULT.md`。
- `PIPELINE.md` 每支檢查器的「驗過沒有」加一行「考卷:N case」。
