# 票 16 的實際結果(對答案:2026-08-24)

預測:`.scratch/ddd-harness/16-PREDICTION.md`(2026-08-19,寫在改 prompt 之前)
被拿來對答案的那一跑:`examples/timesheet/harness/runs/2026-08-21-act2/`
(2026-08-21,timesheet 領域,Opus,16 turns / 21.1 分 / $7.34)
受測品:`tools/harness/run_act2.sh` 的 heredoc(票 16 加的第五節 `architecture.yaml`)
store:那一跑的 `spec.db`(`*.db` 被 `.gitignore` 排除,只在本機)

⚠️ **這次對答案有一個先天錯配。** 那份預測是**對 shop 的 `runs/2026-08-19-act2/spec/SPEC.md`
§9(L434–L455,R1–R10)**逐條寫的;真的跑起來的是 **timesheet 的 §10(L645–L662,A-1–A-10)**,
是完全不同的十條規則。所以預測裡「跟規格綁死」的那一整張表**驗不了**,
記成〈不適用〉——**不是通過,也不是落空**(`CONTEXT.md` L54–L59)。

---

## 一句話

**可落空的三條全部命中(3/3),但這三條在 timesheet 上都不太咬人;
那份預測真正的肉——R1–R10 的逐條形狀——一條都沒驗到。**
另外量到一件預測沒預期到的事:**副預測 2 想看的那個「撞牆過程」,這套儀器根本留不下來。**

---

## 對答案的分母

| 類別 | 條數 | 進不進分母 |
|---|---|---|
| 可落空、且在 timesheet 上驗得了的 | **3**(主預測 + 副預測 1 + 副預測 2 的終態) | ✅ 進 |
| 跟 shop §9 綁死的逐條猜 R1–R10 | 10 | ❌ 不適用 |
| 主預測底下那個「押 3 到 4 條非 none」的點估計 | 1 | ❌ 不適用(它是 R2/R4/R6/R7 的加總,同樣綁 shop) |

**命中率 = 3/3 = 100%,分母 3。**
不適用的 11 條**不進分母**——理由不是「不好算」,是 `CONTEXT.md` 的〈不適用〉條目要求
它自成一類:折進分子會謊報準確度,折進分母會謊報失準度。兩邊都不對。

---

## 逐條對照(進分母的三條)

| # | 預測 | 落空條件 | 實際 | 判定 |
|---|---|---|---|---|
| 主 | §9 的 10 條裡 `enforcement <> 'none'` **少於 6 條** | 回傳 6 或以上 | **1**(A-01,`archunit_forbidden_dependency`) | ✅ 命中(**但門檻不咬人,見下**) |
| 副 1 | `authorized_templates` 是空的 | `authorized_template` 非 0 筆 | **0 筆** | ✅ 命中 |
| 副 2 | `provenance = '模板既定'` 零筆 | 非 0 筆 | **0 筆** | ✅ 命中(**只驗到終態,過程驗不了,見下**) |

### 證據(逐條 SQL,對 `examples/timesheet/harness/runs/2026-08-21-act2/spec.db`)

```sql
sqlite> SELECT count(*) FROM architecture_rule;
10
sqlite> SELECT count(*) FROM architecture_rule WHERE enforcement <> 'none';
1
sqlite> SELECT count(*) FROM authorized_template;
0
sqlite> SELECT count(*) FROM architecture_rule WHERE provenance='模板既定';
0
```

```
sqlite> SELECT id, enforcement, provenance FROM architecture_rule ORDER BY id;
A-01  archunit_forbidden_dependency  本案自決
A-02  none                           推導自
A-03  none                           本案自決
A-04  none                           推導自
A-05  none                           推導自
A-06  none                           Qn
A-07  none                           推導自
A-08  none                           本案自決
A-09  none                           Qn
A-10  none                           Qn
```

順帶驗過的兩件(不在預測裡,但預測的前提靠它們):

```
sqlite> SELECT id, coalesce(enforced_by,'<NULL>') FROM architecture_rule;
A-01|<NULL> … A-10|<NULL>          ← 十條全空,agent 沒有自己填「由誰強制」
sqlite> SELECT id FROM architecture_rule
   ...> WHERE enforcement='none' AND (ladder_note IS NULL OR trim(ladder_note)='');
(零列)                              ← 九條 none 的 ladder_note 全部有寫
sqlite> SELECT count(*) FROM forbidden_annotation;   → 0
sqlite> SELECT count(*) FROM forbidden_return_type;  → 0
sqlite> SELECT * FROM forbidden_dependency;
A-01 | tw.hengyue.timesheet.domain.. | org.springframework.. | 0
A-01 | tw.hengyue.timesheet.domain.. | jakarta.persistence.. | 1
A-01 | tw.hengyue.timesheet.domain.. | javax.persistence..   | 2
A-01 | tw.hengyue.timesheet.domain.. | org.hibernate..       | 3
A-01 | tw.hengyue.timesheet.domain.. | jakarta.servlet..     | 4
A-01 | tw.hengyue.timesheet.domain.. | jakarta.ws.rs..       | 5
```

---

## 主預測命中了,但這一跑證據力很弱

那條門檻是**對著 shop §9 校準的**:那份散文的「由誰強制」欄裡
**8 條指名了 ArchUnit 測試名**(`LayeredArchitectureTest.layers_are_respected` 之類),
只有 R8/R9 兩條自己寫「目前無機械檢查(第 4 階)」。
預測要量的落差就是「**散文指名 8 條 ≠ 落檔後 8 條非 none**」——押 3–4,門檻放在 6。

**timesheet §10 的那一欄長得完全不一樣**(L653–L662,逐格讀過):

| 那一欄寫的是什麼 | 條數 | 是哪幾條 |
|---|---|---|
| 具體的 ArchUnit 測試名 | **0** | — |
| 「目前無機械檢查(第 4 階)」 | 3 | A-1、A-2、A-5 |
| 驗收情境編號(S24 / S19 / S9、S10 …) | 7 | A-3、A-4、A-6、A-7、A-8、A-9、A-10 |
| 含「骨架應提供 / 建議加一條 ArchUnit」這種模糊字眼 | 2 | A-1、A-4(與上面重疊) |

→ **預測要量的那個落差,在 timesheet 上根本沒有形成。**
散文自己就沒宣稱有八條機械檢查,agent 也就沒有可以誤讀成 enforcement 的東西。
門檻 6 對著一份「只有 A-1 一條形狀對得上三種 kind」的規格,**不咬人**——
它是命中,但這一跑幾乎不可能讓它落空,所以它**沒有測到儀器,只測到題目**。

⚠️ 這條要老實說清楚:**「非 none 少於 6」這條預測在 timesheet 上是幾乎恆真的**,
它與「架構規則落檔數 > 0」那條被預測檔自己排除掉的廢話,只差一個級距。

---

## 副預測 2 的另一半:**這套儀器留不下那個過程**

預測寫得很清楚,這一條真正的價值不在「會不會零筆」,而在
**「它現在是靠 trigger 而不是靠自覺守住的」**,而且指名了看哪裡:
> 「最終落檔仍是零筆,但過程中撞過牆。**那個過程在 `result.json` 裡看得到**。」

**這個假設是錯的。**(驗過)

- `run_act2.sh` 用的是 `claude -p … --output-format json`,`result.json` 裡
  只有**最後一則訊息**加 usage/cost/turns,**沒有逐 turn 的工具呼叫紀錄**。
  我用 python 讀過整份 json 的所有 key:沒有 `messages`、沒有 transcript。
- `stderr.log` **0 bytes**。
- import 是 agent 自己在 sandbox 裡跑進 `/tmp/spec.db` 的,那個 db 與它的錯誤輸出都沒有落地。

→ **「trigger 擋過一次」與「agent 從頭到尾沒試過模板既定」,這一跑分不出來。**
零筆這個終態,兩種因果都會產生它。

**推斷(不是驗證)**:agent 大概沒撞牆。依據是它自己在
`architecture.yaml` 檔頭 L3–L9 就把 ABORT 那件事複述了一遍
(「白名單空的時候,provenance『模板既定』物理上寫不進去」)。
但**這正好說明它是被 prompt 教會的,不是被 trigger 教會的**——
那一跑**凍結下來的** `prompt.txt` L87–L89 逐字寫了同一件事
(「白名單是空的時候,`模板既定` 這個值物理上寫不進去 —— schema 的 trigger 會 ABORT,
整份 import 一條都不會進」),L135 再提醒一次。那正是票 16 加進 prompt 的第 2 點。
(⚠️ 這裡引的是 run 目錄裡的 `prompt.txt`,不是 working tree 的 `run_act2.sh` ——
後者此刻正被別的工作改著,不代表那一跑餵進去的東西。)
所以這一跑量到的是**prompt 的說明有效**,不是**trigger 有效**。
兩者的差別在於:prompt 可以被改掉、被忽略,trigger 不會。**trigger 這條路今天仍然沒驗過。**

---

## R1–R10 逐條:**不適用**,不是通過

那十格猜的是 shop §9 的十條規則,timesheet 的十條是另一組主題:

| shop R# | 規則的形狀 | 當時的猜 | timesheet 有沒有這條 | 判定 |
|---|---|---|---|---|
| R1 | 分三層 package 必須存在 | `none`(可拆) | 沒有(§10 沒宣告分層 package) | 不適用 |
| R2 | `domain` 不得 import 框架 / 第三方 SDK | `forbidden_dependency` | **有形狀近親 A-1** | 不適用(旁證見下) |
| R3 | 依 §1.1 切五個 context package | `none` | 沒有(A-5 反過來:單一 BC 不切) | 不適用 |
| R4 | `ordering` 不得 import `inventory` 領域型別 | `forbidden_dependency` | 沒有(只有一個 context) | 不適用 |
| R5 | 相依方向單向 + `reporting` 只讀 | `none`(可拆) | 半個近親 A-6(唯讀模型不得回寫) | 不適用 |
| R6 | 聚合根只以識別碼引用外部 | **當時就不押** | 半個近親 A-2 | 不適用(雙重) |
| R7 | 支付以 port 表達 | `forbidden_dependency` | 沒有(本案沒有第三方支付) | 不適用 |
| R8 | 每月銷量走獨立讀模型 | `none` | 近親 A-6 | 不適用 |
| R9 | 一次交易只改一個聚合根 | `none` | **有形狀近親 A-3** | 不適用 |
| R10 | 購物車型別 / package / 欄位不得存在 | `none` | 近親 A-9(不得實作任何自動判定) | 不適用 |

### 形狀層的旁證(**不計分**)

這些不是那十格的驗證——規則不同、依據不同、寫的人不同。
但預測底下那條**形狀 → kind 的映射規律**,在 timesheet 上獨立地被跑了一次,方向一致:

| 預測的形狀規律 | shop 的猜 | timesheet 的對應條 | 實際落檔 | 一致? |
|---|---|---|---|---|
| 「domain 不得 import 框架」→ `forbidden_dependency` | R2 非 none | A-01 | `archunit_forbidden_dependency`,6 個 to_package | ✅ |
| 「一次交易只改一個聚合根」→ `none`(執行期行為) | R9 none | A-03 | `none` | ✅ |
| 「切 / 不切 context」→ `none`(不是依賴問題) | R3 none | A-05 | `none` | ✅ |
| 「只讀不回寫」→ `none`(行為,不是依賴) | R5 後半 / R8 none | A-06 | `none` | ✅ |
| 「某種東西不得存在」→ `none` | R10 none | A-02、A-09 | 兩條都 `none` | ✅ |

五條規律沒有一條被推翻。**但這是旁證,五條加起來也不能把 R1–R10 從「不適用」搬進「命中」**——
換一份散文,同樣的形狀完全可能被別的 agent 硬湊成三種 kind 之一,而那正是預測要防的失效。

九條 `none` 的 `ladder_note` 我逐條讀過,寫的都是「缺哪一種 kind」而不是「還沒做」,
例如 A-04:「三種 kind 沒有一種看得到**欄位的型別**……缺的是兩種——『某個 package 底下
不得有某型別的欄位』與『不得對某型別做算術』」;A-09 還多寫了一句
「湊出來的測試會綠,而綠會被讀成『已經確認沒有自動判定』」。
**這是預測沒有預測、但票 16 的 prompt 明確要求的東西,交出來了。**

---

## 額外驗證(超出預測範圍)

預測明講「**不主張非 none 的那幾條會生得出可編譯的 Java**」。我還是跑了一次,結果記在這裡:

```
$ python3 tools/harness/gen_archunit.py <該跑的 spec.db> <scratchpad>/ArchitectureTest.java
ok: …/ArchitectureTest.java
  A-01 由 ArchitectureTest.rule_A-01 強制
EXIT=0
```

生出**一個** `@ArchTest`。**這只證明形狀吃得下,不證明它抓得到東西**——
timesheet 沒有骨架、沒有實作,這條規則今天沒有 class 可掃,跑起來會是票 10 那個
`allowEmptyShould(true)` 的免費綠燈。**記成不適用,不是通過。**

### ⚠️ 這一跑把它自己要證的東西改壞了(2026-08-24,已還原)

**`gen_archunit.generate()` 對 store 有寫入副作用** —— `tools/harness/gen_archunit.py:324`:

```sql
UPDATE architecture_rule SET enforced_by = ? WHERE id = ?
```

檔頭 `:9` 就寫明「生成後把『由誰強制』回填進 store」,但上面那次「額外驗證」是**直接拿凍結
run 目錄裡的 `spec.db` 當輸入**,於是回填寫進了凍結素材:`A-01.enforced_by` 從 `NULL` 變成
`'ArchitectureTest.rule_A-01'`。

**它毀掉的正好是本檔上面那條證據** —— L77 的「`A-01|<NULL>` … `A-10|<NULL>` ← 十條全空,
agent 沒有自己填『由誰強制』」重跑會拿不到。寫這份對答案的動作,把這份對答案的憑據改掉了。

已還原(`UPDATE … SET enforced_by = NULL WHERE id = 'A-01'`,非 NULL 列數 1 → 0,
`pragma integrity_check` = ok)。L77 那條證據現在重跑得回來。

**兩個要記住的:**

1. **`git status` 看不到這件事。** `.gitignore:4` 排掉 `*.db`,所以凍結 run 裡的 store
   不在版控裡 —— 改壞了沒有紅字、也沒有 `git restore` 可以救。`CLAUDE.md` 的
   「`runs/` 不要改也不要刪」那條規則,**對 `*.db` 沒有任何機械保護**。
2. **拿生成器去「查」store 不是唯讀操作。** 要對凍結 store 跑生成器,先複製一份到
   scratchpad 再跑。這件事現在沒有寫在任何地方,也沒有東西擋。

---

## 跟那一跑自己的 `RESULT.md` 對不上的地方

那份報告(agent 自己寫的,`examples/timesheet/harness/runs/2026-08-21-act2/RESULT.md`)
在兩處說 **「票 16 仍然未驗」**,理由是「那份釘的是 shop 規格的 R1–R10 逐條形狀」。

**這句話對了一半。** 精確的判定是:

- **可落空的三條(主 + 副 1 + 副 2 終態)驗了,而且命中。** 它們寫的是純 SQL 條件,
  不綁領域,timesheet 的 store 一樣查得動。那份報告自己的 C1/C2/C3 三條其實查的就是同一組數字。
- **R1–R10 的逐條形狀確實未驗**,而且**加上副預測 2 的過程那一半也未驗**(那份報告沒提到這點)。

所以不是「全未驗」,也不是「全驗了」。這份檔就是那個中間狀態的紀錄。

那份報告裡我照抄、**沒有自己重驗**的說法:
「shop 那跑 §9 一條都沒落檔」。它的原始證據在票 16 內文(當時 `gen_archunit` 印
「不適用……store 裡沒有生成得出來的規則」),而**那個 `/tmp/act2new.db` 已經不在了**。
我驗得到的替代證據是:`examples/shop/harness/runs/2026-08-19-act2/` **目錄裡沒有
`architecture.yaml`**(`git ls-files` 與 `ls` 都確認),也沒有 spec.db(`.gitignore` 排 `*.db`)。
沒交檔 → 落不了檔,這一步成立;但「表是空的」那個當年的直接觀測**我重驗不了**。

---

## 這次對答案的限制(哪些是本來就驗不了的)

1. **領域錯配是最大的一條。** 預測的 14 條裡有 11 條綁 shop、3 條不綁。
   驗得了的比例是 3/14 ≈ 21%。這不是預測寫壞了——它寫的時候就講明「本票驗不了,
   下一次跑第二幕的人回來對」——**是「下一次跑第二幕」剛好換了題目**。
   **教訓:預測檔要嘛把落空條件寫成不綁領域的查詢,要嘛在檔頭寫明「只有重跑 X 規格才驗得了」。**
   這份兩件事都做了一半:三條 SQL 是可攜的,十條猜是綁死的,而檔頭沒說要重跑哪一份。
2. **n = 1。** 一跑、一個模型(Opus)、一份規格。形狀規律的五條旁證都是同一個 agent 的同一次判斷。
3. **過程留不下來**(見上)。凡是預測「agent 會撞牆 / 會重試 / 會先錯再改」這一類的,
   現行 `--output-format json` 的產出**一律驗不了**,不論題目換不換。
4. **`enforcement <> none` 的那一條(A-01)是唯一的樣本**,所以「非 none 的規則會不會被寫壞」
   這件事這一跑等於沒測。

---

## 要把 R1–R10 驗完,得做什麼

以**現行**的 `run_act2.sh`(含票 16 那一節)重跑 shop 那份規格:
`examples/shop/harness/runs/2026-08-19-act2/spec/SPEC.md`,開一個新的 run 目錄。
成本參考 timesheet 這一跑:**$7.34 / 16 turns / 21 分**。
跑完直接對 `16-PREDICTION.md` 那張 R1–R10 的表,那時十格才有答案。

⚠️ 重跑前要知道兩件事:
- 那份 SPEC 是**舊 prompt 產出的**,它的 §9 已經是既成事實,重跑第二幕不會改它——這正好,
  預測釘的就是那十條。
- `CLAUDE.md` 已記:重跑第二幕會拿到**四個**檔,跟 `runs/2026-08-19-act2/` 的三個檔對不起來,
  **不要覆蓋舊目錄**。

---

## 記下來的缺口(不是本次交付)

1. **`result.json` 留不下逐 turn 紀錄** → 任何「過程中撞過牆」型的預測都驗不了。
   要補的話是在 `run_act2.sh` 加 `--output-format stream-json` 之類的逐字稿落地。
   ⚠️ 這會動受測品的執行方式(雖然不動 prompt),**要當受測品變更處理**。
2. **預測檔的可攜性沒有規約。** `CLAUDE.md` 只說「跑之前寫預測、跑完寫 RESULT」,
   沒說預測要不要綁定「用哪份規格跑」。票 16 這次踩到的就是這個洞。
3. **A-01 生出來的那條 ArchUnit 今天必然綠**(沒有實作可掃)——票 10 那個坑原樣還在,
   換了題目也一樣。
