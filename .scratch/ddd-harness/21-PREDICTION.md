# 21 — 預測(寫在對真實 run 目錄跑之前)

日期:2026-08-25。對象:`tools/harness/check.py`(包裝器 + 閘門)、`run_act2.sh` / `run_act3.sh` /
`run_act4.sh` 開頭的閘門。**這份寫完先 commit,再跑真實素材。**

先講兩件讀 code 讀到、會左右預測的事(驗過的):

- `test_harness.py:515-516` 直接呼叫 `gen_acceptance.main()` / `gen_archunit.main()` 釘離開碼,
  而那個檔不能動 → 幕三的閘門**不能**放進生成器的 `main()`,只能包一層 `run_act3.sh`
  (票的括號裡有給這條路)。
- `acceptance_gwt.py` 第一段 `stage()` 是 `git archive 4567d31 examples/shop/app`
  (`check=True`),而**這個 repo 沒有 `4567d31` 這個物件、也沒有 `layered/OL1-integration`
  分支**(`git archive 4567d31` → `fatal: not a valid object name`,`git rev-parse` 也找不到分支)。
  它們留在 `kc-log`,沒跟著搬。所以這支在本 repo **跑不到第一段的判定,會在 stage 就炸**。

真實素材一律**複製到 scratchpad 再跑**(`examples/**/runs/` 一個 byte 都不動,帳本會寫進
run 目錄,所以不能對原位跑)。

## 預測

| # | 動作 | 預期 | 備註 |
|---|---|---|---|
| **P1(釘)** | 帳本裡 `landing_check` 只有一筆 `exit == 3`,查 `--gate act2`;`acceptance_gwt` 只有一筆 `exit == 3`,查 `--gate act4` | **兩個都回 1,不回 0**。3 是「不適用」,不是通過;閘門判準是 `exit == 0`,不是 `exit != 1` | 合成語料,`test_check_ledger.py` 釘住。這是本票最容易寫錯的一行 |
| P2 | 複製 `2026-08-18-act1-haiku-roleplay/roleplay` → `check.py landing_check <copy>` | 檢查器 exit **1**(PIPELINE:漏掉整整兩輪 8 題);`<copy>/check-ledger.jsonl` 多一筆 `{"checker":"landing_check", "exit":1, …}` | 真實素材 |
| P3 | 接著 `run_act2.sh <copy>/SPEC-draft.md <work>`(`<work>` 先放一個哨兵檔) | runner **exit 1**、印「上一幕檢查沒過」;哨兵檔還在(閘門在 `rm -rf "$WORK"` 之前) | 真實素材 |
| P4 | 另一份新鮮複製(還沒跑過任何檢查)直接 `run_act2.sh` | **exit 3**、印「不適用:上一幕從沒被檢查過」;`<work>` 不被建立 | 真實素材 |
| P5 | 複製 `2026-08-18-act1-opus-rerun` → `check.py landing_check <copy>` → `ACT2_DRY_RUN=1 run_act2.sh <copy>/SPEC-draft.md <work>` | 檢查器 exit **0**(15 題全有落點;最後一輪不適用是逐輪的,不是整份);runner **exit 0**,`<work>/run-meta.json` 有 `"gate_skipped": false` | 真實素材 |
| P6 | 對 P3 那份(帳本裡是 exit 1)`ACT_GATE_SKIP=1` 但**沒給** `ACT_GATE_SKIP_REASON` | **exit 2**,不建 `<work>`(沒理由不准跳) | |
| P7 | 同上但給了理由,`ACT2_DRY_RUN=1` | **exit 0**,`run-meta.json` 有 `"gate_skipped": true` 與那句理由 | |
| P8 | 複製 `2026-08-19-act2` → 先不跑檢查就 `run_act3.sh <copy>/spec.db <out>` | **exit 3**,印出四個缺的名字(`spec_store import` / `provenance_check` / `contract_triage` / `glossary_check`);`<out>` 不被建立 | 真實素材 |
| P9 | `check.py spec_store import <copy>/{acceptance,glossary,contracts}.yaml <copy>/spec.db` | exit **0**(2026-08-19 那跑 import 印 ok);此時 `--gate act3` 仍回 **3**(還缺三支) | |
| P10 | `check.py --run-dir <copy> provenance_check <2026-08-19-act1-human-stakeholder 原位,唯讀> <其 SPEC-draft.md>`;`check.py contract_triage <copy>/spec.db`;`check.py glossary_check <copy>/spec.db` | 三支各留一筆;**閘門 `--gate act3` → 0**,不管這三支的離開碼是多少(票只要求「各至少跑過一筆」)。側預測(不確定,不計分):provenance 0(掃到東西)、contract_triage 1(有分診項目)、glossary_check 1(5/7 對不到) | provenance_check 的第一個目錄參數是幕一的 run,推不到幕二 → **必須 `--run-dir` 明給** |
| P11 | 接著 `run_act3.sh <copy>/spec.db <out>` | 閘門過、`<out>/run-meta.json` 有 `"gate_skipped": false`;生成器本身:gen_acceptance **0**(5 條情境、有 wire 合約)、gen_archunit **3**(那跑沒交 `architecture.yaml`)→ runner 把 3 傳出去(不適用不是通過) | 生成器離開碼是側預測 |
| P12 | 複製 `2026-08-19-act4-skeleton` → `check.py --run-dir <skelcopy> acceptance_gwt <2026-08-19-act3/OrderAcceptanceTest.java 原位,唯讀> <scratch/gwt-work>` | 檢查器在 `stage()` 就炸(`CalledProcessError`,`4567d31` 不存在)→ Python 未捕捉例外 → **exit 1**;帳本記 `exit: 1`。**票寫的「會 0」在本 repo 不可能成立** —— 就算物件都在,這份生成物綁的合約不是 `shop-frozen-v1`,第 2、3 段不適用,整支也是 3 不是 0 | 這條若命中,幕四的閘門在真實素材上**只能靠 `ACT_GATE_SKIP` 過**,直到 `acceptance_gwt` 修好(改檢查器本體,不在本票) |
| P13 | `ACT4_DRY_RUN=1 run_act4.sh <spec> <skelcopy> <work>` | **exit 1**(有紀錄但不是 0);`<work>` 不被建立 | |
| P14 | 同上加 `ACT_GATE_SKIP=1 ACT_GATE_SKIP_REASON=…` | exit 0;`<work>/run-meta.json` 有 `gate_skipped: true`;**`<work>/check-ledger.jsonl` 不存在**(骨架的帳本被 `cp -R` 帶進來後要刪掉,新跑新帳本) | |
| P15 | 全部跑完 `git status --porcelain` | `examples/` 底下**零變動**;變動只有我動的那幾個檔 | 硬規則的驗證 |

## 判準說明

- 「命中」= 離開碼與檔案狀態都跟表上一樣;側預測(生成器 / 三支分診的離開碼)不計分。
- P12 是唯一跟票的預期(0)相反的一條。它落空的話代表 `acceptance_gwt` 在本 repo 跑得動,
  那是好消息,但閘門仍會因第 2、3 段不適用而拿到 3 → 仍拒絕。
