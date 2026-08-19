# CLAUDE.md

給在這個 repo 工作的 agent。

## 這是什麼

DDD × AI Agent 的 development harness(五幕管線)+ 十一課教材。立論見 `MISSION.md`,
管線逐段的證據見 `tools/harness/PIPELINE.md`。

## 非標準位置(先讀這段,不然會找錯地方)

- **票在 `.scratch/ddd-harness/issues/`**,markdown 一檔一票,不是 GitHub Issues。
  每張票開頭有 `**Status:**` 行。18 張,9 張還活著。
  票裡的預測與結果在 `.scratch/ddd-harness/*-PREDICTION.md` / `*-RESULT.md`。
- **ADR 從 `0003` 開始**,不是掉了東西:`0001` / `0002` 是原 repo(`kc-log`)自己的決策,
  沒有跟著搬。這裡的 `0003`–`0006` 編號**刻意不重編**——它們被 `schema.sql`、
  每一支生成器與檢查器、每一份 `build.gradle` 的註解逐字引用,重編會斷一批指標。
- **詞彙在 `CONTEXT.md`**,11 條,每條附 `_Avoid_`(跟誰容易混、差在哪)。
  寫 code 或寫文件用到這些詞之前先讀:負面情境↔失敗情境、代理編碼↔假驗收、
  wire shape↔領域模型、可滿足性↔非恆真、指名測試↔由誰強制、不適用↔通過、
  對譯檢查↔來源標記檢查、骨架↔不存在、內圈測試↔驗收、恆真↔代理編碼。

## 硬規則

- **`tools/harness/interview-prompt.md` 是第一幕的正本**。改了它,要回頭同步
  `.claude/skills/spec-authoring/SKILL.md` —— 兩份散文講同一條規則會漂(`NOTES.md` 決定 4)。
  兩邊講到同一件事時**以 `interview-prompt.md` 為準**。
  ⚠️ 該 skill 目前是**凍結**狀態,解凍條件記在 `NOTES.md`。
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

只用 stdlib,沒有第三方相依——**保持這樣**。Java 那邊要 gradle,但那是 `examples/` 底下
受測品的事,不是 harness 的相依。

## 寫作慣例

- 繁體中文,DDD / BDD 術語保留英文原文。
- **區分「驗過的」與「推斷的」**,並明確標註。這個 repo 反覆出現的失效是
  「做了 ≠ 接上了 ≠ 驗過了」,所以任何「這個有在守」的說法都要指得出證據;
  指不出來就寫「沒驗過」。
- 教材裡的標本挑**實際在用的東西**,不要挑「業界最常被引用的」(教訓見
  `learning-records/0008`)。
