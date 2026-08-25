# 25-RESULT —— 對答案(2026-08-25)

第一次跑 `exam.py`:**20 case、命中 20、落空 0;已知假陽性 3 筆(釘住)**;
修一個 exam.py 自己的 bug 之後 pytest **267**(預測 267)。

## 預測 vs 實際

| 預測項 | 預測 | 實際 | 命中 |
|---|---|---|---|
| 20 case 的離開碼 | 見 PREDICTION 表 | **20/20 跟 expected 一樣**,一個字串都沒抄錯 | ✅ |
| 落空數 | 0–3,全是我抄錯 / 手算錯 | 0 | ✅(在區間內,但見下) |
| 把握「中」的三個(provenance clean、derived-value、contract clean) | 最可能落空 | 全命中:手算的 2 / 5 / 3 筆都對 | ✅ |
| 已知假陽性三筆今天會印 | 會 | 會,exam 列在「假陽性」欄、case 算命中 | ✅ |
| 無考卷佇列 | **剛好一支** `package_landing_check` | **兩支**:多了 `test_landing_check` | ❌ |
| pytest | 267 | 267(修完佇列 bug 之後) | ✅ |

## 落空的那一條:`*_check.py` 把測試檔也認成檢查器

`CHECKER_GLOBS = ("*_check.py", "*_triage.py")` —— `test_landing_check.py` 長得一模一樣,
第一次跑就被列進「無考卷」佇列。**這是 `exam.py` 的 bug,不是檢查器的**;修法是 `checkers()`
扣掉 `test_` 開頭的檔(改的是 exam.py,四支檢查器一個字都沒動)。修完佇列剛好一支。

這條值得記:「掃目錄認形狀」這種判準,**第一次跑就撞到一個形狀相同的鄰居** ——
跟 `landing_check` 的 `**Qn.` 是同一類病(判準卡在一個字面形狀上)。預測沒想到,
因為我在腦裡列檢查器時列的是「檢查器」,不是「符合 glob 的檔」。

## 「一個 case 都沒落空」要怎麼讀

票說「不落空反而要懷疑考卷太簡單」。老實寫:

- **這張考卷釘的是我讀原始碼讀出來的行為。** 20 個 expected.json 全是從讀 `landing_check.py` 等
  四支的判準 + 印字推出來的,fixture 一個都沒先跑過 —— 所以「全命中」證明的是**我讀對了
  原始碼**,以及**考卷的字串對得上今天的報表**。它證得了「行為沒變」,證不了「行為是對的」。
- **考卷會不會抓到壞掉的檢查器 —— 驗過(突變,不落地)**:把 `landing_check` 的閘門改成
  無條件 `return 0` → `missing-two-rounds` 翻紅(離開碼 1 → 0);把 `provenance_check` 的
  比對改成一律放行 → `fed-then-attested` 與 `derived-value-false-positive` 翻紅(該印沒印 +
  已知假陽性消失)。兩個突變都在複製到 tmp 的副本上做,repo 裡的檢查器沒動。
  `test_exam.py` 另外有一支 `落空真的會回1` 釘住閘門本身。
- **考卷太簡單的地方(推斷,沒驗)**:每支只有 4–6 個 case,而且陽性都是 PIPELINE 已經寫過的
  那幾個。真實 run 裡沒被抽的失效形狀(例:`landing_check` 的輪次斷號 `gap`、`glossary_check`
  的 wire_field 填成散文註記)這裡都沒有考卷。這一版刻意只做票上點名的,不多編。

## 已知假陽性:釘成「今天會印」,不是軟報告

`provenance_check/derived-value-false-positive` 的三筆(120 推導值、`YYYY-MM-DD`、
`QUANTITY_OUT_OF_RANGE`)是票 03 reopened 那類(opus 重跑 52/60、真陽性 0)。
考卷把它們寫在 `false_positives`:**印了才算命中**,但報表單獨列成「假陽性 3 筆,已知、釘住」。
票 03 修好那天這個 case 會翻紅 —— 那是要人去改 expected 的紅,不是壞掉。
沒有選「印成 FYI 不影響離開碼」:那樣票 03 修好時考卷靜靜地不再適用,沒有人會發現。

## 語料出處對不上任務說明的地方

- 任務說明寫 provenance 的 100/120 在 `2026-08-18-act2-opus/`。**不對**:那是第二幕的落檔 run
  (prompt + agent-acceptance.yaml),沒有答案語料。100/120 在 `2026-08-18-act1-interview/`
  (票 03 與 `test_provenance.py` 都指這裡;實跑 2/2 命中 L115)。fixture 從那裡抽。
- `2026-08-18-act2-rerun/` 沒用到:`glossary_check` 的已知陽性用的是凍結那組
  (`examples/shop/harness/glossary.yaml` + `acceptance.yaml`,PIPELINE 幕二表格第一列),
  因為 act2-rerun 那組要配 `act2-from-interview/glossary.yaml`(11 條 + 10 列禁用),
  抽最小片段抽不出「0/7」那個數字的精神 —— 凍結那組的「撞名不是對譯」一條 OrderId 就講完了。
- `glossary_check/clean`、`orphan-term`、`contract_triage/clean` 是**合成**的(expected.json 的
  `source` 逐個標了):真實語料裡沒有一份對譯 0 差額、或契約全部指得到測試。

## 沒做到的

- `acceptance_gwt.py` / `vacuous_tests.py` / `verify_generated.py` 不在 `*_check.py` /
  `*_triage.py` 的形狀裡,**不掃、不進佇列**(`CHECKER_GLOBS` 一行的決定,寫在 exam.py 檔頭)。
- 「每支至少 clean / 陽性 / 不適用三個 case」只對第一批四支有測試守
  (`test_第一批四支各自蓋到三個離開碼`);新檢查器那半 **prose-only, unenforced** ——
  exam.py 認不出哪個 case 是哪一種,只認離開碼。
