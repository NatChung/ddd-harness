@harness/CLAUDE.md

# 上游才有的

上面那份跟 hub 的副本逐字相同;底下是只有 ddd-harness 這邊才有的東西。
立論見 `MISSION.md`,十一課教材在 `lessons/`。

## 目錄

```
ddd-harness/
  harness/          ← 自足的一塊 = hub 拿走的全部(腳本、測試、prompt、schema、CONTEXT.md、CLAUDE.md、docs/adr/、hub-bootstrap.md、vendor.sh)
  examples/         ← 語料;examples/shop/tests/ 是讀語料的測試(從 harness/ 搬出,票 32;hub 不拿)
  tools/lint/       ← harness_lint.py + 測試 + fixtures(管 .scratch 的票;hub 不拿)
  lessons/ practice/ reference/ research/ learning-records/ index.html   ← 教材
  .scratch/ddd-harness/   ← 票、預測檔
  docs/research/    ← 調查筆記
  CLAUDE.md         ← 本檔:@harness/CLAUDE.md + 這一段
  README.md MISSION.md NOTES.md RESOURCES.md
```

為什麼這樣切:`harness/` 是 hub 用 `harness/vendor.sh` 整個 copy 走的(ADR 0010),
所以它裡面不能引用上層;其他全部都是上游自己的,hub 一樣都不拿。

## 非標準位置

- **票在 `.scratch/ddd-harness/issues/`**,markdown 一檔一票,不是 GitHub Issues。
  32 張,15 張還活著(2026-08-26,票 13、21–26、32 done)。詳細規約見下面〈票怎麼開、怎麼關〉。

## 票怎麼開、怎麼關

**檔名**:`NN-kebab-slug.md`,`NN` 是兩位數流水號(目前到 32,下一張是 33)。

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

**新立慣例要二選一(ADR 0007)**:同票交 lint(`tools/lint/harness_lint.py`,票 22),
或在票裡逐字寫「prose-only, unenforced」+ 為什麼。以上規約由 `harness_lint.py` 守
(`python3 tools/lint/harness_lint.py .`;fixtures 在 `tools/lint/fixtures/`;驗過:2026-08-25
對真 repo 跑 exit 0,見 `.scratch/ddd-harness/22-RESULT.md`),規則名:`ticket-filename`(檔名)、
`status-vocabulary`(開頭詞;**新票只放行前五個**,`resolved` 對新票算命中)、`status-single-cell`
(整格重寫)、`prediction-before-result` / `prediction-before-run`(預測先於結果 / 先於跑)、
`referenced-run-exists`(引用的 run 目錄在)、`blocked-by-resolvable`(Blocked by 的票號存在)、
`ticket-count-in-docs`(上面「N 張」的總數與「目前到 N」,讀本檔、`README.md`、`harness/PIPELINE.md`
三份)、`convention-undecided`(ADR 0007 §4 的佇列,**不是判決**,不計入離開碼)。
祖父條款 `ADOPTION_DATE = 2026-08-25`:**含當天**以前首次 commit 的票不追溯(看 git 日期,
不看 mtime),所以票 21–27 也是祖父票。
⚠️ 「N 張還活著 / 已完成」lint **不查**(「活著」的定義沒拍板),關票時記得手改三份文件。

**預測檔**:動 harness 之前先把「我預期會看到什麼」寫進
`.scratch/ddd-harness/NN-PREDICTION.md`(**跟票是兄弟檔,不是票的一節**),跑完再寫
`NN-RESULT.md` 對答案。預測寫在跑之前才算數。

## 硬規則(examples/)

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
- **`examples/shop/tests/` 是讀語料的測試**(`examples/shop/{harness,app,spec}`、
  `examples/returns/interview-prompt.md` 當 fixture),從 `harness/` 搬出來是票 32:
  它們測的是上游語料上的行為,hub 沒有語料就不該帶著它們。

## 測試(全 repo)

```bash
python3 -m pytest harness examples/shop/tests tools/lint
```

`run_act2.sh` / `run_act4.sh` 的 `NA_RATIO_ROOT` 預設是 `$HARNESS/../runs`(hub 的 `runs/`);
上游要掃語料時自己傳 `NA_RATIO_ROOT=examples`。

## 寫作慣例(教材)

- 教材裡的標本挑**實際在用的東西**,不要挑「業界最常被引用的」(教訓見
  `learning-records/0008`)。
