# 26 — 對答案(2026-08-25)

預測檔 `26-PREDICTION.md` commit `7734c0d`,**在對真實素材跑之前**(儀器本體那時已寫好、
測試與考卷已綠,但還沒 commit —— 預測釘的是對真實素材的結果,不是儀器的合成行為)。
跑的腳本與完整 log 在 session scratchpad(`26-run.sh` / `26-run.log`),不進 repo。
真實素材唯讀;runner 那條用 `cp -R` 到 scratchpad 的複本跑(`check.py` 會寫帳本)。

## 逐條

| # | 預期 | 實際 | |
|---|---|---|---|
| **P1** | `na_ratio.py examples` → exit 3;「帳本 0 份、0 筆;舊 run(沒帳本)18 張」;表裡沒有任何檢查器;沒有 ⚠️ | exit 3;「帳本 0 份、0 筆;舊 run(沒帳本)18 張,**不進分母**;讀不動 0 行」;表印「(沒有紀錄)」;「❌ **一份 check-ledger.jsonl 都沒有 —— 整份不適用,不是通過**」;沒有 ⚠️ 那種行(「沒有超過門檻的」那句的 ⚠️ 是說明,不是警告) | ✅ 命中 |
| P2 | `--brief --checker landing_check examples` → exit 3,只一行 | exit 3;`na_ratio:不適用 —— 沒有任何 check-ledger.jsonl(舊 run 18 張沒帳本,不進分母)` | ✅ 命中 |
| P3 | `--brief --checker acceptance_gwt examples` → 同 P2 一字不差 | 一字不差 | ✅ 命中 |
| P4 | `na_ratio.py .`(repo root)→ exit **0**;帳本 12 份、舊 run 23 張;`landing_check` ⚠️(10 跑 5 次 = 50%) | exit 0;「帳本 12 份、13 筆;舊 run(沒帳本)23 張;讀不動 4 行」;`landing_check 10 / 5 / 0 / 5 / 50% / 連續 2 ⚠️` | ✅ 命中(側預測 50% 也對) |
| P5 | opus-rerun 複本:`check.py landing_check` 0 → `ACT2_DRY_RUN=1 run_act2.sh` 走預設根 → runner 0;「上一幕的檢查證據齊了」之後出現 P2 那行(18 張) | 檢查器 0;runner 0;stdout 第 2 行「上一幕的檢查證據齊了:」、第 4 行 `na_ratio:不適用 —— …(舊 run 18 張沒帳本,不進分母)`;`work5/run-meta.json` 在 | ✅ 命中 |
| P6 | `NA_RATIO_ROOT=<不存在>` → runner 仍 0;stderr **一行** `na_ratio:用法錯誤 —— 找不到目錄:…`,沒有 docstring | runner 0;stderr 1 行,正是那句;stdout 零個 `na_ratio:` | ✅ 命中 |
| P7 | `git status --porcelain`:`examples/` 零變動 | ` M exam.py / M run_act2.sh / M run_act4.sh / ?? fixtures/exams/na_ratio/ / ?? na_ratio.py / ?? test_na_ratio.py`;`examples/` 零變動 | ✅ 命中 |

**命中 7 / 落空 0 / 不適用 0。**

## 這一票對真實素材量到什麼

**什麼都量不到,而且這是預期的**:18 張 run 全在票 21 之前(或票 21 是在 scratchpad 複本上跑的,
原位沒留帳本),一份 `check-ledger.jsonl` 都沒有 → 儀表回 3「不適用」。儀器的行為(門檻、連續
不適用、loss-tolerant、零帳本 → 3)全靠合成帳本釘:`fixtures/exams/na_ratio/` 6 個 case
(`exam.py` 26 case 全命中)+ `test_na_ratio.py` 34 條。**趨勢要等票 21 之後的跑累積了帳本才看得到。**

## 對票的偏離(都不是漏做)

1. **`NA_RATIO_ROOT` 環境變數**(票沒寫):runner 預設掃 `$HARNESS/../../examples`,測試要有
   一個不依賴 repo 現況的掃描根,所以加了覆寫。同票 21 加 `ACT2_DRY_RUN` 的性質。
2. **skip 欄是推斷**:帳本裡沒有「跳過」這種紀錄;唯一機械讀得到的「跳過」是 `run-meta.json`
   的 `gate_skipped: true`,而它沒寫是哪一幕 —— 從欄位形狀推(`skeleton` → act4、`spec_db` →
   act3、`spec` → act2),對到 `check.GATES` 那幕要求的檢查器。報表逐處標「推斷」。
3. **`exam.py` 改了一行**:`CHECKER_GLOBS` 加 `na_ratio.py`。它原本只認 `*_check.py` /
   `*_triage.py`,`na_ratio` 的考卷會被列成「指不到檢查器」(script 明明在)。docstring 點名
   那一行是擴充點,所以改那裡。`test_exam.py` 沒動,11 條照過。
4. **`run_act3.sh` 沒加那一行**:票只點名 act2 / act4。要加是一行的事,但票沒說,留著。

## 已知上限(P4 驗出來的那條)

- 掃描根給 repo root 會把 `tools/harness/fixtures/` 的合成帳本掃進去(12 份),`landing_check`
  會被考卷語料頂成 ⚠️。runner 預設根是 `examples/`,**不要改成 repo root**;`.scratch/` 因為
  `.` 開頭被略過,但 `fixtures/` 不是。要排除它得加名單,本票不加(儀表沒有理由知道考卷住哪)。
- `run_act2.sh` 那條看的是**全 repo** 的 landing_check,不是「這份規格」的 —— 儀表量的是守衛
  跨跑的趨勢,不是這一跑;這是刻意的,票寫的也是「上 N 跑」。

## 沒驗過的

- runner 閘門過了之後真的呼叫 `claude` 那條路(花錢),dry-run 只到 run-meta.json。
- `run_act4.sh` 那行只在 `test_na_ratio.py` 的合成骨架上驗(dry-run 0、⚠️ 行在閘門之後);
  沒對真實骨架跑 —— 幕四的閘門在本 repo 只能靠 `ACT_GATE_SKIP` 過(21-RESULT),而跳過那條路
  在 act2 驗過會印(`test_act2_閘門跳過那條路也印`),act4 沒另外驗。
- 門檻 0.25 / 5 對本 repo 合不合適 —— 沒有帳本,量不了。
