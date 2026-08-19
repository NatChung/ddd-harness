# 16 — 第二幕的 prompt 沒有叫 agent 交架構規則,所以 §9 整節掉在地上

**What to build:** 讓 `run_act2.sh` 的 prompt 要求第四份 yaml(`architecture_rules`),
並補上它的欄位說明 —— 現在整節架構規格**沒有任何一步在讀它**。

**Blocked by:** None

**Status:** **done**(2026-08-19,commit `18bf044` + `6c85992`)—— `run_act2.sh` 的 prompt 加第四份 `architecture.yaml`(受測品變更)。⚠️ 預測 `.scratch/ddd-harness/16-PREDICTION.md` **還沒驗** —— 要下次真跑第二幕才驗得了,下一個跑的人請回來對那張表。

## 量到了(2026-08-19 全鏈跑通那次)

真人訪談產出的規格 §9 有 **10 條架構規則**(R1–R10,每條都有「由誰強制」欄,
其中 8 條指名了 ArchUnit 測試)。落檔之後:

```
$ python3 tools/harness/gen_archunit.py /tmp/act2new.db out/ArchitectureTest.java
不適用(不是通過):store 裡沒有生成得出來的規則,沒有東西可生成
```

**`architecture_rule` 表是空的。** 原因很笨:`run_act2.sh` 的 heredoc prompt 只要三份 yaml ——

```
acceptance.yaml —— wire_contract 與 acceptance_scenarios
glossary.yaml   —— glossary_terms 與 banned_synonyms
contracts.yaml  —— domain_contracts
```

**沒有 architecture。** agent 沒交,因為沒人叫它交。

⚠️ **這是 2026-08-18 我改那份 prompt 時漏掉的** —— 那次把「一份 yaml」擴成「三份」,
補了詞彙與契約,**卻沒補架構**,而 `architecture_rule` 是這個 store 裡**最老的一張表**、
配著唯一一個從第一天就在的生成器(`gen_archunit`)。

## 後果(不只是少一份檔)

那一跑的空骨架結果是 **5 紅 + 4 綠**,而那 4 個綠是:

1. **凍結骨架繼承來的** `ArchitectureTest`(`com.shop.domain/usecase/adapter`),**不是這份規格生的**
2. 在空專案上**必然綠**(`allowEmptyShould(true)`,掃不到任何 class)

`package_landing_check` 對它的判定是 **exit 3「宣告過的 package:0 個 → 本次不適用(不是通過)」**。

也就是說:**這份規格的架構規則,從落檔到跑起來,一路上沒有任何一步碰過它。**
而報表上看起來是「9 條測試 4 條綠」。

## 這是哪一家族

跟票 08(詞彙沒進 store)、票 06(契約沒進 store)**完全同一種**,只是這次少的那一節
**曾經有過表也有過生成器** —— 它是被 prompt 的改動弄丟的,不是從來沒有。

⚠️ 所以它多帶一個教訓:**擴充受測品的時候,要對照 store 現有的表逐張確認有沒有人交。**
今天的 store 有 `architecture_rule` / `wire_contract` / `acceptance_scenario` /
`domain_contract` / `glossary_term` 五組,而 prompt 只點名了四組。

## 要做什麼

1. `run_act2.sh` 的 prompt 加第四份 `architecture.yaml`(頂層 `authorized_templates` 與
   `architecture_rules`),欄位說明照 `schema.sql` 的 `architecture_rule` 與三張參數子表。
2. ⚠️ **`authorized_templates` 要明講**:沒有被授權為架構模板的文件時**必為空**,
   而 `模板既定` 這一格在白名單為空時**物理上寫不進去**(trigger 會 ABORT)。
   ——這條不講,agent 會把自決偽裝成既定(歷史上兩輪都這樣)。
3. 驗證命令要一起改成四份。
4. ⚠️ **這是受測品變更**,檔頭已有警語,改完要在 run 目錄留 `prompt.txt` 並記進下一跑的報告。

## ⚠️ 先寫下來的上限

- **交得出來 ≠ 生得出來。** `gen_archunit` 只吃三種 kind(`forbidden_dependency` /
  `forbidden_annotation` / `forbidden_return_type`)。那份規格的 R8、R9 自己就寫著
  「目前無機械檢查(第 4 階)」,R5 的「reporting 只讀」也不在那三種裡。
  **預期落檔後仍有數條 `enforcement: none`** —— 那是對的,不要為了好看去湊。
- **本票不解決「凍結骨架的 ArchUnit 是繼承來的」**。骨架換成規格自己生的那一份,
  是票 10 的下一步,不在這裡。

## 可落空的預測(實作前要寫)

不要寫「架構規則落檔數 > 0」。可落空的例子:
**預測 §9 的 10 條裡,`enforcement` 不是 `none` 的會少於 6 條**(因為 R5/R8/R9 那三條
的形狀不在現有三種 kind 裡),**而且 `authorized_templates` 會是空的、`模板既定` 零筆。**

## 相關

- **票 06 / 08** —— 同一家族的前兩次(契約、詞彙)
- **`runs/2026-08-19-act2/RESULT.md`** —— 本票的原始證據
