# 25-PREDICTION —— 考卷跑之前,每個 case 我預期看到什麼

寫於 2026-08-25,**在第一次跑 `exam.py` 之前**。fixture 與 `expected.json` 全部從讀檢查器原始碼
推出來,一個 fixture 都沒先拿檢查器跑過(真實 run 有跑過 —— 那是 PIPELINE 已記的事實,
用來挑片段,不是用來調 expected)。

## 預測的形狀

`expected.json` 釘離開碼 + `must_print` + `must_not_print`(+ 已知假陽性 `false_positives`)。
下表「預期」是我寫進 expected.json 的;「把握」是我對**整個 case 命中**的把握,
不是對離開碼單獨的把握 —— 字串釘得很細,漏一個標點就落空。

| checker | case | 預期 exit | 把握 | 最可能落空在哪 |
|---|---|---|---|---|
| landing_check | clean | 0 | 高 | 「小計」那句的空白 / 全形標點抄錯 |
| landing_check | question-mark-drift | 3 | 高 | 「第 1 輪:Q1…  —— 判準只認」那行是兩個空白,抄錯就落空 |
| landing_check | missing-two-rounds | 1 | 高 | 截短後 r3 的表仍在問題之前,應該不變;風險是我把 8 題算錯 |
| landing_check | answers-only-old-run | 3 | 高 | — |
| landing_check | usage-error | 2 | 高 | `找不到` 印在 stderr,exam 合併 stdout+stderr 才看得到 |
| provenance_check | fed-then-attested | 0 | 高 | 「2 筆;…2 筆」那句的粗體星號 |
| provenance_check | clean | 0 | **中** | L86 那行的 `≥ 1` 或 `[Q3]`/`推導自[Q18]` 是否又冒出一個我沒算到的值 → 變 3 筆 |
| provenance_check | derived-value-false-positive | 0 | **中** | 總筆數 5 / 找不到 3 是手算的;`Asia/Taipei`、`400`、`< 1` 任何一個被 VALUE 吃到就落空 |
| provenance_check | not-applicable | 3 | 高 | `本案自決 [Q1][Q2]…` 那行若被算成 claim(不會,沒有值) |
| provenance_check | usage-error | 2 | 高 | — |
| glossary_check | clean | 0 | 高 | 合成 11 條詞,`provenance_ref` 形狀若被 spec_store 擋 → store 匯不進去(fixture 壞,不是檢查器) |
| glossary_check | frozen-collision-not-translation | 1 | 高 | 「5 條」留的是不是剛好那三個撞名的:OrderId / CustomerId / ProductId |
| glossary_check | orphan-term | 1 | 高 | — |
| glossary_check | not-applicable-no-glossary | 3 | 高 | — |
| glossary_check | not-applicable-no-contract | 3 | 高 | 只有兩條詞的 store 匯不匯得進去(「只有詞彙表的一份檔不算空的」有測試,應該可以) |
| glossary_check | usage-error | 2 | 高 | — |
| contract_triage | clean | 0 | **中** | `named_tests: [S1]` 而沒寫 `no_named_test_reason`、沒寫 `crosses_aggregate` —— spec_store 第 2 階是否要求什麼我沒填的 |
| contract_triage | crossing-and-unnamed | 1 | 高 | `>-` 折行後的 disposition 是否跟我釘的子字串逐字一致 |
| contract_triage | not-applicable | 3 | 高 | — |
| contract_triage | usage-error | 2 | 高 | — |

**20 case。預期命中 17–20;最可能落空的三個是把握「中」的那三個。**
票說「預期至少一個 case 會落空,不落空反而要懷疑考卷太簡單」—— 我的預測是**落空 0–3 個,
而且全是我抄字串 / 手算筆數的錯,不是檢查器的錯**。要是真的一個都不落空,RESULT 要寫:
這張考卷釘的是我讀原始碼讀出來的行為,它證得了「行為沒變」,證不了「行為是對的」。

## 已知假陽性(釘住,不是預測會修好)

`provenance_check/derived-value-false-positive`:120(推導值)、`YYYY-MM-DD`(格式字串)、
`QUANTITY_OUT_OF_RANGE`(錯誤碼常數)三筆**今天會印**。票 03 reopened 說的就是這一類
(opus 重跑 52/60、真陽性 0)。預期:三筆都印、exam 把它們列在「假陽性」欄、case 算命中。

## 無考卷佇列

預期剛好一支:`package_landing_check`(`*_check.py` 裡唯一沒考卷的)。
`acceptance_gwt.py` / `vacuous_tests.py` / `verify_generated.py` 不在 `*_check.py` / `*_triage.py`
的形狀裡,**這一版不掃**,所以不會出現在佇列 —— 這是 `CHECKER_GLOBS` 的決定,不是它們有考卷。

## pytest

236 → 236 + 20(每 case 一支)+ 11(機制)= **267**,全綠(前提是上面 20 個全命中;
落空幾個就紅幾支,修 expected 之後才綠 —— 修的是 expected,不是檢查器)。

## 交付之外、跑之前就知道做不到的

- 票的例子 `provenance_check/fed-then-attested` 指的是 opus **那場**(`2026-08-18-act1-interview`),
  任務說明寫的 `2026-08-18-act2-opus` 是第二幕的落檔 run,裡面沒有答案語料 —— 100/120 的
  已知陽性只能從 act1-interview 抽。RESULT 會再寫一次。
- `glossary_check/clean` 與 `contract_triage/clean` 是**合成**的:真實語料裡沒有任何一份
  對譯 0 差額、或契約全部指得到測試。合成的 case 只證明「回 0 那條路真的存在」。
