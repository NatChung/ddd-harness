# 32 — 預測(寫在動目錄之前)

日期:2026-08-26。對象:上游重排成 `harness/` 一塊 + `vendor.sh`。**這份寫完先 commit,再動手。**

先講讀 repo 讀到的(驗過的):

- `HEAD = 6017911`,working tree 乾淨。`python3 -m pytest tools/harness -q` = **456 passed + 1 skipped = 457**。
- kc-hub 那邊手工剪完是 **354 passed + 1 skipped**(`~/projects/kc-hub` `f93e72a`),砍掉 `test_harness_lint.py` 收集 **50** 條、
  讀 `examples/` 的 **52** 條。354 + 1 + 50 + 52 = 457,對得上。
- `tools/harness/` 裡引 `tools/harness/` 字串的檔:PIPELINE.md 23、replay_act1.py 9、run_act2.sh 6(其中 sandbox 佈局那幾行不改)、
  hub-bootstrap.md 5、check.py 2、gen_acceptance.py 2、pitest.gradle 2、test_relay.py 2、其餘各 1。
- 依賴上層目錄的 code:`REPO = Path(__file__).resolve().parents[2]` 8 處(2 支腳本 + 6 支測試),`$HARNESS/../../examples` 2 處(run_act2 / run_act4)。
- `harness_lint.py` 的 `COUNT_DOCS` 寫死 `tools/harness/PIPELINE.md`。

## 預測

| # | 動作 | 預期 | 備註 |
|---|---|---|---|
| **P1(釘)** | 重排後從根跑 `python3 -m pytest harness examples/shop/tests tools/lint -q` | **456 passed + 1 skipped**,一條不多一條不少(`test_vendor.py` 另計) | 搬測試不改測試;數字漂 = 有測試掉了或重複收集 |
| P2 | `python3 -m pytest harness -q` | **354 passed + 1 skipped**,跟 kc-hub 手工那份一樣 | harness 這塊本身沒少東西 |
| P3 | `python3 tools/lint/harness_lint.py .` | exit 0;`ticket-count-in-docs` 讀 `harness/PIPELINE.md`(改 `COUNT_DOCS`)後三份文件 32 張一致 | |
| P4 | `grep -rn 'tools/harness' harness/` | 只剩 `run_act2.sh` 那 6 行(`$WORK/tools/harness/`、heredoc、run-meta key)| sandbox 佈局刻意不動 |
| P5 | `grep -rnE 'parents\[[1-9]\]|\.\./\.\./' harness/ --include=*.py --include=*.sh` | **0** 命中 | 「不引用上層目錄」 |
| P6 | `harness/vendor.sh <tmp>/hub` → `diff -r harness <tmp>/hub/harness` | 只差 `ORIGIN.md`(多一個)+ `__pycache__`(不 copy);副本 `pytest` = P2 的數字 | |
| P7 | 再跑一次 `vendor.sh` 對同一個 hub | exit 非 0,印「已存在,不覆蓋」;檔案沒動 | |
| P8 | 對 `~/projects/kc-hub` 跑 `vendor.sh`(先 `rm -rf harness`)→ `git status` | 差異只有:`ORIGIN.md` 內容(來源 commit 變新的)、`vendor.sh` / `test_vendor.py` 新增、`CLAUDE.md` 文字(hub 中立版)、README 用法段。**腳本本體 0 diff** | kc-hub 手工那份如果跟 script 產物有 code 差,代表手工搬時改了不該改的 |
