# CLAUDE.md

給在 `harness/` 底下工作的 agent。這份在上游(ddd-harness)與 hub 的副本裡逐字相同。

## 這是什麼

DDD × AI Agent 的 development harness(五幕管線):腳本、測試、prompt、`schema.sql`、詞彙、ADR。
**這個目錄是自足的一塊** —— hub 用 `vendor.sh <hub>` 整個拿走,之後各自發展(ADR 0010)。
管線逐段的證據見 `PIPELINE.md`;hub 怎麼用它見 `hub-bootstrap.md`;這份副本從哪個上游 commit
來的見 `ORIGIN.md`(`vendor.sh` 寫的,上游本身沒有這個檔)。

## 非標準位置(先讀這段,不然會找錯地方)

- **ADR 在 `docs/adr/`,從 `0003` 開始**,不是掉了東西:`0001` / `0002` 是原 repo(`kc-log`)
  自己的決策,沒有跟著搬。編號**刻意不重編**——`schema.sql`、`spec_store.py`、`gen_acceptance.py`、
  各支檢查器與大半測試的註解都逐字引用這些編號,重編會斷一批指標。
  (**不是每一支都引用**,驗過 2026-08-26:`acceptance_archunit.py`、`gen_archunit.py`、
  `orchestrate.py`、`relay_ledger.py`、`replay_act1.py`、`vacuous_tests.py` 一個 ADR 都沒提到。)
- **詞彙在 `CONTEXT.md`**(跟本檔同一層),10 條,每條附 `_Avoid_`(跟誰容易混、差在哪)。
  寫 code 或寫文件用到這些詞之前先讀:負面情境↔失敗情境、代理編碼↔假驗收、
  wire shape↔領域模型、可滿足性↔非恆真、指名測試↔由誰強制、不適用↔通過、
  對譯檢查↔來源標記檢查、骨架↔不存在、內圈測試↔驗收、恆真↔代理編碼。
- **「票 NN」指的是上游 ddd-harness 的 `.scratch/ddd-harness/issues/` 編號**。腳本、ADR、
  `PIPELINE.md` 裡到處引;票本身不在這個目錄裡,在 hub 裡要查得回上游。

## 預測檔

動 harness 之前先把「我預期會看到什麼」寫成 PREDICTION,跑完再寫 RESULT 對答案。
這是量「儀器準不準」的唯一方式:**預測寫在跑之前才算數**。位置看你在哪:
上游是 `.scratch/ddd-harness/NN-PREDICTION.md`(跟票是兄弟檔),hub 是
`specs/<feature>/<act>-PREDICTION.md`(`hub-bootstrap.md`〈每一幕結束要回報的〉)。
`runs/` 底下各跑也有自己的 `RESULT.md`,那是另一回事,別混。

## 硬規則

- **`interview-prompt.md` 是第一幕的正本,而且是唯一一份**(上游 2026-08-25 刪過一份落後的
  副本 `.claude/skills/spec-authoring/SKILL.md`:兩份散文講同一條規則會漂)。
  **`interview-brownfield.md` 是補充檔,只載差量**(ADR 0009):正本已有的段落**不准**在它裡面重講;
  brownfield 才載入。**`hub-bootstrap.md` 是 hub 開工的正本,住這裡**,hub 的 `AGENTS.md`
  只指過來、不複製。
- **生成物不要手改**:`gen_acceptance.py` / `gen_archunit.py` 產的 Java 是決定性的,
  `verify_generated.py` 會重新生成一次逐位元組比。手改 = 紅燈。
  ⚠️ 它的 `GENERATORS` 是白名單、不掃目錄——**沒有生成器認領的 `.java` 對它完全隱形**。
- **`run_act2.sh` 已經跟 2026-08-19 那一跑漂了**:那跑的 prompt 說產出**三個**檔,
  現在的 heredoc 說**四個**(票 16 補了 `architecture.yaml`)。所以那跑的 `act2/` 沒有
  `architecture.yaml` 是對的,不是漏掉——但**重跑第二幕會拿到四個檔**,跟既有素材對不起來。
  `run_act2.sh` 給 agent 的工作目錄仍用 `$WORK/tools/harness/` 放 `schema.sql` / `spec_store.py`
  ——那是 sandbox 內的佈局,不是 repo 佈局,不要順手改。
- **這個目錄裡不引用上層目錄**(`parents[2]`、`../../examples` 之類):引了,vendor 出去就斷。
  讀語料的測試住上游 `examples/shop/tests/`,不住這裡。prose-only, unenforced(票 32)。

## 測試

```bash
cd harness && python3 -m pytest
```

**相依要講精確**:各支檢查器本身只用 stdlib(單獨跑不用裝東西),但

- **跑測試要 `pytest`**;
- **匯入 spec yaml 要 `PyYAML`**(`spec_store.py` 的 yaml 路徑、`test_negative_scenarios.py`
  的 module-level `import yaml`)。JSON 路徑不需要。

`pip install pytest pyyaml` 就這兩個,**不要再加第三個**。Java 那邊要 gradle,但那是
受測品(上游 `examples/`、hub 自己的實作)的事,不是 harness 的相依。

## 寫作慣例

- 繁體中文,DDD / BDD 術語保留英文原文。
- **區分「驗過的」與「推斷的」**,並明確標註。這條線反覆出現的失效是
  「做了 ≠ 接上了 ≠ 驗過了」,所以任何「這個有在守」的說法都要指得出證據;
  指不出來就寫「沒驗過」。
- 新立慣例二選一(ADR 0007):交機械檢查,或逐字寫「prose-only, unenforced」+ 為什麼。
