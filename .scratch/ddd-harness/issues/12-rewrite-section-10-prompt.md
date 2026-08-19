# 12 — 幕四的 runner 與工作契約:寫 `run_act4.sh`

> ⚠️ **2026-08-19 重新界定。** 本票原本叫「§10 的工作契約要改寫」,那個範圍是錯的:
>
> 1. **`run_act4.sh` 根本不存在** —— `tools/harness/` 只有 `run_act2.sh`。
>    幕四從來沒有 runner,這跟「正向那半從沒跑過」是同一件事的兩面。
> 2. **§10 那張表在另一份規格裡。** 骨架(票 10)做給的是
>    `runs/2026-08-18-act2-from-interview/input-SPEC.md`,它**沒有 §10 表格** ——
>    它有的是「**不得開工的部分**」(L288)與「**完成的定義**」(L298)兩節。
>    §10 那張表屬於 `act1-opus-rerun/SPEC-draft.md`,而那份一條情境都沒落檔。
> 3. **改 run 目錄裡的產出是錯的。** 那些是紀錄,不是可編輯的文件。
>
> **所以本票真正要做的是:把 ADR 0006 的決定寫成 `run_act4.sh` 的 prompt**,
> 原料是目標規格自己的那兩節。原本寫的「改寫 §10」只在**下一次**訪談產出新規格時才適用
> —— 那時是改 `interview-prompt.md` 對 §10 的要求(受測品變更),不是改既有的產出。

**What to decide & write:** 訪談產出的 §10「給實作 agent 的工作契約」目前對做法只寫
「填到驗收全綠」。ADR 0006 定了四件要寫進去的事。

**Blocked by:** 部分 —— 「內圈測試放哪個 source set」要跟票 10 的骨架一起定

**Status:** done(2026-08-19)—— `tools/harness/run_act4.sh` 已交付。
prompt 在該檔的 heredoc(受測品),已知上限在該檔檔頭,管線位置在 `PIPELINE.md` 幕四那節,
預測在 `.scratch/ddd-harness/12-PREDICTION.md`。
⚠️ **還沒真的跑過**(付費那一跑併到下次);ADR 0006 §2 的 HTTP 假服務**未涵蓋** ——
這份規格用不到(票 10-RESULT 三個獨立證據),它屬於 `act1-opus-rerun/SPEC-draft.md`。

## 要改寫的四處

1. **外部替身從 Java class 名改成 HTTP 假服務。** §10 現在寫的是
   `FakeMembershipSystem` / `FakePricingSystem` 兩個 Java class ——
   那會逼骨架宣告 port 型別。⚠️ **§10 是訪談產出的規格,不是 harness**;
   改它等於我們替規格做決定,**標 `本案自決` 並記下依據**。
2. **完成的定義加一句:內圈測試不算。** 現在寫「三套全綠」,要補明生成的那三套
   才算數,agent 自己寫的測試**不算**,而且是用結構分開(單獨 source set / task),
   不是靠自律。
3. **把 `tautological` 的定義寫進去**(借自 `mattpocock-skills:tdd`):
   > 斷言用跟程式碼同樣的方式重算期望值,因此依構造必然通過,永遠不可能跟程式碼意見相左。
   > 期望值必須來自獨立的真相來源 —— 已知good的字面值、算過的例子、**規格**。
4. **seam 由規格指定,不是問人。** `domain_contract` 的每一條就是一個 seam 候選,
   `guarded_in` 就是「這條測試該打在哪個物件上」。隔離跑沒有使用者可以確認。

## 不要做

不要外包給 `:implement` / `:tdd`。讀過了,三處打架(完成訊號 / seam 誰定 / 收尾),
理由逐條在 `docs/adr/0006` §4。**借詞彙可以,換合約不行。**
