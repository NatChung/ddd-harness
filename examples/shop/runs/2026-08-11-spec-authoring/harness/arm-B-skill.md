---
name: spec-authoring
description: 把 stakeholder 需求訪談成可凍結的 spec 包(GLOSSARY / SPEC / ARCHITECTURE / PROMPT 四份 MD)。
disable-model-invocation: true
---

# 需求 → spec 包

跑 `/grilling` 當訪談引擎。每敲定一條決策,立刻按型態落檔:
**詞 → GLOSSARY、行為 → SPEC 的 GWT、結構 → ARCHITECTURE**;
被否決或延後的需求,落 SPEC 的「明確不在範圍」。

## 產出合約(四份,缺一即未完成)

1. **GLOSSARY.md** — ubiquitous language 表:每詞給型態(用標準 DDD 詞:
   Aggregate Root、Value Object、Repository、…)、一句定義、所屬層。
   開頭寫死:「實作命名必須照此表,不得另創同義詞」。
2. **SPEC.md** — 端點清單(不多不少)+ 行為情境:每條 Given-When-Then 都有
   具體前提資料、單一動作、可斷言的結果(能一比一翻成自動化測試)。
   領域規則(invariant、契約)獨立一節,與情境同等效力。
   結尾「明確不在範圍」:逐項列訪談中否決或延後的需求,收尾「不要做」。
3. **ARCHITECTURE.md** — 從常備模板起筆(package 佈局、相依方向、框架隔離),
   只追加本案特有規則(邊界例外、讀寫佈局),標注哪些由機械檢查強制。
4. **PROMPT.md** — 給實作 agent 的工作契約:凍結清單(不得修改的檔案)、
   要填的範圍、完成的定義(測試全綠)、歧義自決並逐條記 ASSUMPTIONS.md。

## 完成判準

- 訪談的每條決策都能在四份檔案裡指出落點;每條 GWT 的 Then 都可斷言。
- 沒問過 stakeholder 的事 = 規格沉默:寧可入「明確不在範圍」,也不默默展開。
