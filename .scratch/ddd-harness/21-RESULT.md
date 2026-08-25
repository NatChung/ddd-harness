# 21 — 對答案(2026-08-25)

預測檔 `21-PREDICTION.md` commit `e981502`,**在寫 `check.py` 之前、在對真實素材跑之前**。
真實素材一律先 `cp -R` 到 scratchpad 再跑(`examples/**/runs/` 沒動,P15 驗過)。
跑的腳本與完整 log 在 session scratchpad(`21-run.sh` / `21-run.log`),不進 repo。

## 逐條

| # | 預期 | 實際 | |
|---|---|---|---|
| **P1** | 帳本裡是 3 → 閘門回 1,不回 0 | `test_P1_帳本裡的3不算通過`:act2 / act3 / act4 三個都回 1 | ✅ 命中(合成語料,測試釘住) |
| P2 | roleplay 複本 `landing_check` exit 1,帳本一筆 exit 1 | exit 1;`{"checker":"landing_check","argv":[…],"exit":1,"ts":"2026-08-25T07:51:52+00:00","cwd":…}` | ✅ 命中 |
| P3 | `run_act2.sh` 對它 exit 1、哨兵檔還在 | exit 1,印「❌ landing_check:1 筆,離開碼 [1],沒有一筆是 0」;`sentinel.txt` 還在 | ✅ 命中 |
| P4 | 新鮮複本(沒帳本)→ exit 3、不建 work | exit 3,印「不適用:上一幕從沒被檢查過(沒有 check-ledger.jsonl)」;work 不存在 | ✅ 命中 |
| P5 | opus-rerun 複本 `landing_check` 0 → dry-run runner 0、`gate_skipped: false` | 檢查器 0;runner 0;run-meta.json `"gate_skipped": false, "gate_skip_reason": ""` | ✅ 命中 |
| P6 | `ACT_GATE_SKIP=1` 沒理由 → 2、不建 work | exit 2「需要 ACT_GATE_SKIP_REASON(沒理由不准跳)」;work 不存在 | ✅ 命中 |
| P7 | 有理由 + dry-run → 0、理由落 run-meta.json | exit 0;`"gate_skipped": true, "gate_skip_reason": "haiku roleplay 漏 8 題是已知陽性,…"` | ✅ 命中 |
| P8 | act2 複本先不跑檢查就 `run_act3.sh` → 3、列四個缺的 | **exit 66**:複本裡根本還沒有 `spec.db`(gitignore `*.db`),runner 在閘門之前就擋「找不到 spec store」。import 之後再跑一次(P8b)才是 3,列出缺的三支、import 那筆打 ✅ | ❌ **落空** —— 儀器對,是我的前置條件寫錯。閘門那半的行為在 P8b 看到了,但預測寫的是 3,實際是 66 |
| P9 | `check.py spec_store import` 三份 yaml → 0;此時 `--gate act3` 仍 3 | import 0;gate 3(缺 provenance / contract_triage / glossary) | ✅ 命中 |
| P10 | 三支各留一筆 → gate 0,不管它們的離開碼 | provenance 0、contract_triage 1、glossary_check 1;gate **0**,印「跑過 1 筆(離開碼 [1];佇列不是判決,只要求跑過)」 | ✅ 命中(側預測 0 / 1 / 1 也全對,不計分) |
| P11 | `run_act3.sh` 閘門過、run-meta.json `gate_skipped: false`;gen_acceptance 0、gen_archunit 3 → runner 3 | 閘門過;`out11/run-meta.json` 寫了;`gen_archunit exit 3 / gen_acceptance exit 0`;runner 印「有生成器不適用 —— 不是通過」exit 3;`OrderAcceptanceTest.java` + `OrderProxyAcceptanceTest.java` 生出來了 | ✅ 命中(側預測也對) |
| P12 | `acceptance_gwt` 在 `stage()` 炸 → exit 1、帳本記 1 | `subprocess.CalledProcessError: Command '['git', 'archive', '4567d31', 'examples/shop/app']' returned non-zero exit status 128.`;帳本 `"checker":"acceptance_gwt","exit":1` | ✅ 命中 —— **票裡寫的「會 0」在本 repo 不可能** |
| P13 | `ACT4_DRY_RUN=1 run_act4.sh` → 1、不建 work | exit 1「❌ acceptance_gwt:1 筆,離開碼 [1],沒有一筆是 0」;work 不存在 | ✅ 命中 |
| P14 | 加 skip + 理由 → 0;run-meta.json 有 `gate_skipped: true`;work 裡**沒有** `check-ledger.jsonl` | exit 0;`"gate_skipped": true, "gate_skip_reason": "acceptance_gwt 在本 repo 找不到 4567d31,第一段跑不到"`;「no ledger in work」 | ✅ 命中 |
| P15 | `git status --porcelain` 只有我動的檔 | ` M run_act2.sh / M run_act4.sh / ?? check.py / ?? run_act3.sh / ?? test_check_ledger.py`(文件與票在之後才改);`examples/` 零變動 | ✅ 命中 |

**命中 14 / 落空 1 / 不適用 0。**

## 落空那條的意思

P8 的落空不是儀器的問題,是預測者的:`run_act3.sh` 開頭先驗 `<spec.db>` 存在(66),閘門在後面。
複本裡沒有 `spec.db` 是因為 `.gitignore` 擋了 `*.db`,`cp -R` 自然也沒有。寫預測時我把「帳本沒有紀錄」
和「store 還沒建」混成一步。**runner 的順序(先驗參數、再閘門、再 `rm -rf`)是對的**,不改。

## 對票的三處偏離(都不是漏做)

1. **幕三的閘門在 `run_act3.sh`,不在 `gen_*.py` 的 `main()`** —— `test_harness.py:515-516` 直接呼叫兩支
   生成器的 `main()` 釘離開碼,那個檔不能動。票的括號給了這條路。**代價:直接跑 `gen_*.py` 繞得過閘門**,
   `PIPELINE.md` 幕三的指令段寫明了。
2. **`run_act4.sh` 的閘門在真實素材上只能跳。** `acceptance_gwt` 的 `stage()` 要 `git archive 4567d31`,
   物件與 `layered/OL1-integration` 都留在 `kc-log`(P12 驗過);就算搬來,綁非 `shop-frozen-v1` 合約的
   spec 第 2、3 段一定不適用 → 整支 3 → 閘門拒絕。票要的「第一段 exit 0」在現在的檢查器上**沒有對應的
   離開碼**(它的 3 是三段合起來的,見 PIPELINE 那張表的但書)。修法要改檢查器本體(讓第一段單獨回報),
   本票不改任何檢查器,所以留給下一張。**閘門本身沒有為此放水**:判準仍是 `exit == 0`。
3. **`run_act2.sh` 多了 `ACT2_DRY_RUN=1`**(照 `run_act4.sh` 的 `ACT4_DRY_RUN`),因為 runner 用 `env -i`
   寫死 PATH,沒辦法用假的 `claude` 測「閘門過了之後」那半;dry-run 是唯一不花錢的路。
   **heredoc prompt 一個字沒動**(受測品),git diff 可查。另外 `run_act2.sh` 加了 `[ -f "$SPEC" ]` 的檢查
   (66,同 act4),因為閘門要從它推目錄。

## 沒驗過的

- 三支 runner 閘門**過了之後**真的呼叫 `claude` 那條路 —— 沒跑(花錢),dry-run 只證明到 run-meta.json 寫完。
- `check.py` 對 `orchestrate.py`(幕一 runner)沒有閘門 —— 幕一沒有「上一幕」,票也沒要求。
- 帳本被兩個並行的 `check.py` 同時 append 會不會交錯 —— 沒測;每筆一行、寫完 flush,推斷不會斷行但沒驗。

## 判準說明

命中 = 離開碼與檔案狀態跟預測表一樣;側預測(分診三支與生成器的離開碼)不計分,雖然全對。
