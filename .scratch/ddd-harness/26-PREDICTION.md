# 26 — 預測(寫在對真實 run 目錄跑之前)

日期:2026-08-25。對象:`tools/harness/na_ratio.py`(不適用比率儀表)與 `run_act2.sh` /
`run_act4.sh` 閘門之後那一行。**這份寫完先 commit,再對真實素材跑。**

先講讀 repo 讀到、會左右預測的事(驗過的,寫預測之前查的):

- `examples/` 底下 4 個 `runs/` 目錄(`returns/runs`、`shop/harness/runs`、`shop/runs`、
  `timesheet/harness/runs`),第一層子目錄共 **18** 個(`find … -path "*/runs/*"` 數的,
  跟 `CLAUDE.md` 寫的「全 repo 18 個 run 目錄」一致)。
- **一份 `check-ledger.jsonl` 都沒有**(`find . -name check-ledger.jsonl` 零命中)——
  票 21 對真實素材是複製到 scratchpad 跑的,原位沒留帳本。這是預期,不去補。
- 6 份 `run-meta.json`,**沒有一份**含 `gate_skipped`(grep 零命中)→ skip 欄不會有東西。
- `tools/harness/fixtures/` 底下有我為考卷合成的帳本(`exams/na_ratio/*/examples/…`,12 份)
  與 lint 考卷的空 run(`lint/clean/examples/demo/harness/runs/*`,2 張)。它們**不在**
  `<repo>/examples/` 底下,但**在** `<repo>/` 底下 —— 所以掃描根給對很重要。

真實素材**唯讀**:`na_ratio.py` 只讀不寫;runner 那條要跑到閘門之後才印,而閘門要帳本,
所以 runner 的驗證用 scratchpad 複本(`check.py` 會寫帳本,不能對原位跑)。

## 預測

| # | 動作 | 預期 | 備註 |
|---|---|---|---|
| **P1(釘)** | `python3 tools/harness/na_ratio.py examples` | **exit 3**;印「帳本 0 份、0 筆;舊 run(沒帳本)18 張」與「一份 check-ledger.jsonl 都沒有 —— 整份不適用,不是通過」;表裡沒有任何檢查器那一列;**沒有 ⚠️** | 票的「完成的定義」釘的那條:全部不適用、exit 3 |
| P2 | `--brief --checker landing_check examples` | exit 3;**只一行**:`na_ratio:不適用 —— 沒有任何 check-ledger.jsonl(舊 run 18 張沒帳本,不進分母)` | runner 用的那條路 |
| P3 | `--brief --checker acceptance_gwt examples` | 同 P2,一字不差(沒帳本時跟看哪一支無關) | |
| P4 | `python3 tools/harness/na_ratio.py .`(repo root,**不是** runner 用的根) | **exit 0**,不是 3 —— 因為掃進 `tools/harness/fixtures/` 的合成帳本:帳本 **12** 份、舊 run **23** 張(18 + lint 考卷 2 + na_ratio 考卷 3);`landing_check` 那列會 ⚠️(over-threshold 考卷 6 跑 4 次不適用,跟 normal 考卷 3 跑 1 次、unreadable 考卷 1 跑 0 次合起來 10 跑 5 次 = 50%) | 這是 runner 預設掃 `examples/` 而不掃 repo root 的原因;若命中,寫進 PIPELINE 當已知上限 |
| P5 | 複製 `examples/shop/harness/runs/2026-08-18-act1-opus-rerun` 到 scratchpad → `check.py landing_check <copy>` → `ACT2_DRY_RUN=1 run_act2.sh <copy>/SPEC-draft.md <work>`(**不給** `NA_RATIO_ROOT`,走預設根) | 檢查器 0(21-RESULT P5 驗過);runner **exit 0**;stdout 裡「上一幕的檢查證據齊了」**之後**出現 P2 那一行(舊 run 18 張 —— 複本在 scratchpad,不在 `examples/` 底下,不會被算進去) | 真實素材走 runner 那條路 |
| P6 | 同 P5 的複本,`NA_RATIO_ROOT=<不存在的路徑>` | runner 仍 **exit 0**;stderr 一行 `na_ratio:用法錯誤 —— 找不到目錄:…`,**沒有** docstring 灌進去 | 儀表失敗不得讓 runner 失敗 |
| P7 | 全部跑完 `git status --porcelain` | `examples/` 底下**零變動**;變動只有我動的那幾個檔 | 硬規則 |

## 判準說明

- 「命中」= 離開碼、印出的數字與字串跟表上一樣;P4 的 ⚠️ 那一列的百分比是側預測(不計分,
  但寫出來讓數字算得出來)。
- 這一票對真實素材**量不到任何趨勢**——18 張全是舊 run,這是預期的,不是儀器壞了。
  儀器的行為靠合成帳本的考卷與測試釘(`fixtures/exams/na_ratio/`、`test_na_ratio.py`)。
