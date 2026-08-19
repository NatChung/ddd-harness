# CLAUDE.md

給在這個 repo 工作的 agent。

## 這是什麼

DDD × AI Agent 的 development harness(五幕管線)+ 十一課教材。立論見 `MISSION.md`,
管線逐段的證據見 `tools/harness/PIPELINE.md`。

## 非標準位置(先讀這段,不然會找錯地方)

- **票在 `.scratch/ddd-harness/issues/`**,markdown 一檔一票,不是 GitHub Issues。
  18 張,9 張還活著。詳細規約見下面〈票怎麼開、怎麼關〉。
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

**檔名**:`NN-kebab-slug.md`,`NN` 是兩位數流水號(目前到 18,下一張是 19)。

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

**預測檔**:動 harness 之前先把「我預期會看到什麼」寫進
`.scratch/ddd-harness/NN-PREDICTION.md`(**跟票是兄弟檔,不是票的一節**),跑完再寫
`NN-RESULT.md` 對答案。這是這個 repo 量「儀器準不準」的唯一方式:預測寫在跑之前才算數。
`runs/` 底下各跑也有自己的 `RESULT.md`,那是另一回事,別混。

## 硬規則

- **`tools/harness/interview-prompt.md` 是第一幕的正本**。改了它,要回頭同步
  `.claude/skills/spec-authoring/SKILL.md` —— 兩份散文講同一條規則會漂。
  兩邊講到同一件事時**以 `interview-prompt.md` 為準**。
  ⚠️ **這個 skill 的凍結狀態,`NOTES.md` 自己講兩套,還沒裁決**:L638(2026-08-17)寫
  「題 3 當天稍晚補完(`spec-authoring` 因此**解凍**)」,L770 卻還寫著「解凍動作**還沒做**,
  而且題 3 還欠」。SKILL.md 本身沒有任何凍結標記(只有 `disable-model-invocation: true`,
  那是叫用政策不是凍結)。**動它之前先問人**,不要自己選一邊。
- **`examples/returns/interview-prompt.md` 一個字都不要動** —— 那是跨模型實驗的凍結受測品
  (blob `71c1eb7d6eb6`)。改它會毀掉實驗基準。
- **`examples/shop/harness/runs/` 底下是歷史素材,不要改**。要跑新的就開新的 run 目錄。
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
