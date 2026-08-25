# 21 — 五幕之間什麼都不擋:跳過上一幕的檢查,下一幕的 runner 照樣啟動

**What to build:** 每支 runner 開工前查上一幕的**檢查證據**,沒有或沒過就拒絕啟動;加一支
`check.py` 包裝器把每次檢查的離開碼記進 run 目錄的 `check-ledger.jsonl`。

**Blocked by:** None

**Status:** done —— 2026-08-25 落在 `tools/harness/check.py`(包裝器 + `--gate`)、`run_act2.sh` / 新 `run_act3.sh` / `run_act4.sh` 開頭、`test_check_ledger.py`(33 條);預測 15 條命中 14、落空 1(P8,我自己的前置條件寫錯:spec.db 還沒建,runner 在閘門之前就 66)、不適用 0;⚠️ 幕四那道閘門在本 repo 只能靠 `ACT_GATE_SKIP` 過 —— `acceptance_gwt` 要的 `4567d31` / `layered/OL1-integration` 沒跟著從 kc-log 搬來,而且它對非凍結合約的 spec 一定回 3;修法動檢查器本體,不在本票(細節 `21-RESULT.md`)。

## 哪裡壞了

`PIPELINE.md` 用文字說「幕三之後才幕四」「跑 `run_act4.sh` 之前先 `acceptance_gwt` 確認空骨架全紅」。
沒有任何東西擋。今天可以直接 `run_act4.sh` 而空骨架從沒驗過紅;可以 `gen_acceptance.py`
而 `provenance_check` 從沒跑過。**順序靠自律** —— 正是 `MISSION.md` 說最容易換模型就漂的那種。

對照(驗過,`docs/research/2026-08-25-harness-survey.md` §3 第 1 條):fspec 的
`allowed_transitions` 表 20 行,`backlog→testing` 直接 `Err("Must move to 'specifying' state first")`;
Agentheim `LEGAL_MOVES` 3 行。**便宜,而且是唯一擋得住「跳幕」的形狀。**

## 形狀

1. **`tools/harness/check.py <checker> <args…>`**:用 subprocess 跑指定檢查器,把
   `{checker, argv, exit, ts, cwd}` 追加進 `<run_dir>/check-ledger.jsonl`(run_dir 從 argv 推,
   或 `--run-dir` 明給)。**不改任何檢查器本體** —— 這是刻意的,避免跟票 25 / 26 撞檔。
2. **每支 runner 開頭讀帳本**:
   - `run_act2.sh`:要求該 run 的 `landing_check` 有一筆 `exit == 0`。
   - `gen_acceptance.py` / `gen_archunit.py`(或包一層 `run_act3.sh`):要求 `spec_store import`
     ok 且 `provenance_check`、`contract_triage`、`glossary_check` 各至少跑過一筆。
   - `run_act4.sh`:要求對同一個骨架跑過 `acceptance_gwt` 第一段(空骨架全紅)且 `exit == 0`。
3. **⚠️ 離開碼 3(不適用)不算通過。** 閘門判準是 `exit == 0`,不是 `exit != 1`。
   寫成 `exit in (0, 3)` 就把「守衛靜靜不再適用」放行了 —— 這是本票最容易寫錯的一行,
   **預測檔要釘它**。
4. **逃生口要留痕**:`ACT_GATE_SKIP=1` 可跳過,但 runner 要把 `gate_skipped: true` + 理由寫進
   `run-meta.json`。沒理由不准跳。
5. 帳本沒有那一幕的任何紀錄 → runner 印「**不適用**:上一幕從沒被檢查過」並拒絕,離開碼 3;
   有紀錄但 `exit != 0` → 離開碼 1;`ACT_GATE_SKIP` → 照跑,離開碼由 runner 本身決定。

## 陷阱(advisor 2026-08-25 點名)

- 一支「沒人被迫用」的 `run_pipeline.py` 是散文級強制,跟現在沒差。**擋要擋在 runner 本身。**
- 帳本用 append-only jsonl,不要 sqlite —— 幕一 `relay-ledger.jsonl` 已經是這個形狀。

## 慣例(ADR 0007)

「runner 啟動前必須有上一幕的檢查證據」本身是一條新慣例 —— 由本票的 runner 開頭那段守,
**不另立 lint**。`check-ledger.jsonl` 的格式:prose-only, unenforced(票 26 會讀它,讀不動就知道)。

## 完成的定義

- 新測試檔 `test_check_ledger.py`(**不要動 `test_harness.py`**):包裝器記帳、三種閘門結果
  (0 / 1 / 3)、`ACT_GATE_SKIP` 留痕。
- `21-PREDICTION.md` 在對真實 run 目錄跑之前寫:預期對 `runs/2026-08-19-act4` 的骨架重跑
  `acceptance_gwt` 第一段會 0、對 `2026-08-18-act1-haiku-roleplay` 跑 `landing_check` 會 1
  → `run_act2.sh` 對它應拒絕。跑完寫 `21-RESULT.md`。
- `PIPELINE.md` 每幕的指令段加 `check.py` 用法;`README.md` 跑起來那節同步。
- **不動** `examples/**/runs/`、不動生成的 `.java`。
