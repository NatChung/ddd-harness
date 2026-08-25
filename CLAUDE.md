# CLAUDE.md

給在這個 repo 工作的 agent。

## 這是什麼

DDD × AI Agent 的 development harness(五幕管線)+ 十一課教材。立論見 `MISSION.md`,
管線逐段的證據見 `tools/harness/PIPELINE.md`。

## 非標準位置(先讀這段,不然會找錯地方)

- **票在 `.scratch/ddd-harness/issues/`**,markdown 一檔一票,不是 GitHub Issues。
  31 張,15 張還活著(2026-08-25,票 13、21–26 done)。詳細規約見下面〈票怎麼開、怎麼關〉。
- **ADR 從 `0003` 開始**,不是掉了東西:`0001` / `0002` 是原 repo(`kc-log`)自己的決策,
  沒有跟著搬。這裡的 `0003`–`0006` 編號**刻意不重編**——`schema.sql`、`spec_store.py`、
  `gen_acceptance.py`、多支檢查器與三份 `build.gradle` 的註解都逐字引用這些編號,重編會斷
  一批指標。(**不是每一支都引用**:`gen_archunit.py`、`vacuous_tests.py`、
  `provenance_check.py`、`acceptance_archunit.py`、`examples/shop/app/build.gradle`
  一個 ADR 都沒提到。)
- **詞彙在 `CONTEXT.md`**,10 條,每條附 `_Avoid_`(跟誰容易混、差在哪)。
  寫 code 或寫文件用到這些詞之前先讀:負面情境↔失敗情境、代理編碼↔假驗收、
  wire shape↔領域模型、可滿足性↔非恆真、指名測試↔由誰強制、不適用↔通過、
  對譯檢查↔來源標記檢查、骨架↔不存在、內圈測試↔驗收、恆真↔代理編碼。

## 票怎麼開、怎麼關

**檔名**:`NN-kebab-slug.md`,`NN` 是兩位數流水號(目前到 31,下一張是 32)。

**每張票的開頭**照這個形狀:

```markdown
# NN — 一句話標題(講「哪裡壞了」,不是「要做什麼功能」)

**What to build:** 一到兩句,要交付的東西。

**Status:** <見下>
```

**Status 是散文,不是列舉值**——這是刻意的,但也因此漂得很兇。實際用過的開頭詞:
`needs-triage` / `needs-info` / `blocked` / `reopened` / `done` / `resolved` / `A 半 done`。
**寫新的請用前六個之一開頭**,後面接一句「卡在哪 / 落在哪個 commit / 下一步是什麼」。
`done` 與 `resolved` 沒有語意差別,是同一件事的兩種寫法——**新的一律用 `done`**。
半完成的票(例:票 06、08)把已交付的部分寫成 `A 半 done`,並在同一行寫清楚剩下哪半、
卡在什麼。

**改一張票的 Status = 整格重寫**,不要在後面追加——狀態欄只放最新狀態,歷史寫進票的內文。

**新立慣例要二選一(ADR 0007)**:同票交 lint(`tools/harness/harness_lint.py`,票 22),
或在票裡逐字寫「prose-only, unenforced」+ 為什麼。以上規約由 `harness_lint.py` 守
(`python3 tools/harness/harness_lint.py .`;驗過:2026-08-25 對真 repo 跑 exit 0,見
`.scratch/ddd-harness/22-RESULT.md`),規則名:`ticket-filename`(檔名)、`status-vocabulary`
(開頭詞;**新票只放行前五個**,`resolved` 對新票算命中)、`status-single-cell`(整格重寫)、
`prediction-before-result` / `prediction-before-run`(預測先於結果 / 先於跑)、
`referenced-run-exists`(引用的 run 目錄在)、`blocked-by-resolvable`(Blocked by 的票號存在)、
`ticket-count-in-docs`(上面「N 張」的總數與「目前到 N」)、`convention-undecided`
(ADR 0007 §4 的佇列,**不是判決**,不計入離開碼)。祖父條款 `ADOPTION_DATE = 2026-08-25`:
**含當天**以前首次 commit 的票不追溯(看 git 日期,不看 mtime),所以票 21–27 也是祖父票。
⚠️ 「N 張還活著 / 已完成」lint **不查**(「活著」的定義沒拍板),關票時記得手改三份文件。

**預測檔**:動 harness 之前先把「我預期會看到什麼」寫進
`.scratch/ddd-harness/NN-PREDICTION.md`(**跟票是兄弟檔,不是票的一節**),跑完再寫
`NN-RESULT.md` 對答案。這是這個 repo 量「儀器準不準」的唯一方式:預測寫在跑之前才算數。
`runs/` 底下各跑也有自己的 `RESULT.md`,那是另一回事,別混。

## 硬規則

- **`tools/harness/interview-prompt.md` 是第一幕的正本,而且是唯一一份**。
  `.claude/skills/spec-authoring/SKILL.md` 2026-08-25 刪了(它是落後的副本,兩份散文講
  同一條規則會漂)。`runs/` 與 `NOTES.md` 裡對它的引用是歷史,不要去修。
  **`interview-brownfield.md` 是補充檔,只載差量**(ADR 0009):正本已有的段落**不准**在它裡面重講;
  brownfield 才載入。`hub-bootstrap.md` 同理:hub 用 submodule 引,不複製。
- **`examples/returns/interview-prompt.md` 一個字都不要動** —— 那是跨模型實驗的凍結受測品
  (blob `71c1eb7d6eb6`)。改它會毀掉實驗基準。
- **`examples/` 底下所有 `runs/` 是歷史素材,不要改、也不要刪**(⚠️ 有四個,而且
  `examples/returns/runs/` **沒有 `harness/` 那層** —— 寫成 `examples/*/harness/runs/`
  會漏掉它)。要跑新的就開新的 run 目錄。
  **全 repo** 18 個 run 目錄裡有 12 個被 `.scratch/ddd-harness/issues/` 的票引用著,
  刪掉一個還被引著的 run = 把開著的票的證據抽掉。**退役某一跑之前先跑
  `grep -rl <run 目錄名> .scratch/ddd-harness/issues/`,有命中就不能動。**
  ⚠️ **沒命中不等於可刪**:`2026-08-18-act2-opus` 零票引用,但 `PIPELINE.md` 引著它;
  `returns/runs/2026-08-17-*` 零票引用,但 `examples/returns/README.md` 與
  `interview-prompt-rationale.md` 引著它。全 repo 真正零引用的只有
  `timesheet/harness/runs/2026-08-21-act1-human-abandoned`。
  唯一豁免:`examples/shop/runs/`(**沒有 `harness/`** 的那個)是 harness 之前的舊實驗,
  但被 `NOTES.md` 與 `reference/0003-*.html` 當教材引用著。
- **生成物不要手改**:`gen_acceptance.py` / `gen_archunit.py` 產的 Java 是決定性的,
  `verify_generated.py` 會重新生成一次逐位元組比。手改 = 紅燈。
  ⚠️ 它的 `GENERATORS` 是白名單、不掃目錄——**沒有生成器認領的 `.java` 對它完全隱形**。
- **`run_act2.sh` 已經跟 2026-08-19 那一跑漂了**:那跑的 prompt 說產出**三個**檔,
  現在的 heredoc 說**四個**(票 16 補了 `architecture.yaml`)。所以 `act2/` 沒有
  `architecture.yaml` 是對的,不是漏掉——但**重跑第二幕會拿到四個檔**,跟既有素材對不起來。

## 測試

```bash
cd tools/harness && python3 -m pytest
```

**相依要講精確**:各支檢查器本身只用 stdlib(單獨跑不用裝東西),但

- **跑測試要 `pytest`**;
- **匯入 spec yaml 要 `PyYAML`**(`spec_store.py` 的 yaml 路徑、`test_negative_scenarios.py`
  的 module-level `import yaml`)。JSON 路徑不需要。

`pip install pytest pyyaml` 就這兩個,**不要再加第三個**。Java 那邊要 gradle,但那是
`examples/` 底下受測品的事,不是 harness 的相依。

## 寫作慣例

- 繁體中文,DDD / BDD 術語保留英文原文。
- **區分「驗過的」與「推斷的」**,並明確標註。這個 repo 反覆出現的失效是
  「做了 ≠ 接上了 ≠ 驗過了」,所以任何「這個有在守」的說法都要指得出證據;
  指不出來就寫「沒驗過」。
- 教材裡的標本挑**實際在用的東西**,不要挑「業界最常被引用的」(教訓見
  `learning-records/0008`)。
