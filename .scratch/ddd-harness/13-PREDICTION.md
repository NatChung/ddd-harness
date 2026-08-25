# 票 13 的預測(寫在寫程式之前,2026-08-25)

形狀由票 13 檔末「2026-08-25 · 形狀」那節定死:一支新檢查器 `innertest_landing_check.py
<spec.db> <workdir>` 三段分開印;恆真分診(副)不動,仍交 `vacuous_tests`;`run_act4.sh`
heredoc 只加一句。這份釘的是**拿真實 run 跑會拿到哪一碼、哪幾段**,以及 heredoc 改前改後
的 blob —— 每一條都寫得出什麼結果會讓它落空。

「檢查跑得起來」「pytest 全綠」不可能失敗,**不用**。

## 動手前先查證過的事(不是預測,是事實)

- `runs/2026-08-19-act4/src/innerTest/` 有 **6 支檔、9 個 `@Test` 方法**,方法名帶契約編號
  (`C2_…`、`C8_…`),class javadoc 寫「契約 C4」這種散文;**沒有任何一處出現 `@covers`**。
- 這份規格的 store(`runs/2026-08-19-act2/` 三份 yaml 匯入)有 **17 條契約 C1–C17、5 條情境
  G1 G2 G13 G16 G17** —— 情境編號是 **G**,不是票裡寫的 S。所以檢查器**不能寫死 C / S 前綴**,
  編號一律從 `domain_contract.id` / `acceptance_scenario.id` 讀。
- `run_act4.sh` 的 heredoc 是 `<<'EOF'`(不展開變數),所以 `prompt.txt` 對同一版 runner
  是常數。改之前 dry run 一次(閘門用 `ACT_GATE_SKIP`,理由照 PIPELINE 幕四那句):
  **改前 blob `d4a17c9a1da3f2526a549e7a70f94bdb46393a41`,與 `runs/2026-08-19-act4/prompt.txt`
  在 index 裡的 blob 逐位元組相同** —— heredoc 從 2026-08-19 到現在沒漂。
- `run_act4.sh` 自己會在每個工作目錄 `mkdir -p src/innerTest/java`,所以「目錄在、零個檔」
  正是「agent 一條內圈測試都沒寫」的長相,不是「沒跑過第四幕」。
- 這台機器有 JDK 17 + gradle;`runs/2026-08-19-act4/build.gradle` **沒有 PIT plugin**。
  要跑 `vacuous_tests` 得先把 run 複製到 scratchpad、加 pitest 再跑 —— run 目錄本身不動。

## 決定(不是預測)

- **契約決定離開碼;情境只印參考。** 情境的落點是外圈生成的驗收(幕三,逐位元組驗過),
  要求每條情境也有內圈測試等於再犯一次「懲罰寫得好的那一方」。所以第一段分兩塊:
  契約逐條(無落點 → 1),情境逐條(只印,不進判定)。**`@covers G16` 這種指向情境的宣告是合法的**,
  反向段(指到不存在的編號)對情境編號一樣查。
- **舊約定(方法名帶編號)不算落點。** 檢查器另印一行「偵測到舊約定方法名 N 條(不算落點)」,
  讓 2026-08-19 那跑的報表讀起來是「舊約定的跑」而不是「偷懶的跑」。
- 離開碼:**0** 每條契約都有 `@covers`、沒有指到不存在編號的;**1** 任一契約無落點,或任一
  `@covers` 指到 store 沒有的編號(漂);**2** 用法錯誤(db 不在 / workdir 不在);
  **3 不適用** —— 沒有 `src/innerTest/` 目錄,或 store 契約與情境都是 0 條。
  **目錄在但零個 `.java` / 零個 `@covers` → 1,不是 3**(票裡明講:那是漏)。
- 「打在哪個入口」那欄:印 `第 4 階,人讀`,列出每支測試檔裡的 `Type.method(`、`new Type(`、
  `Type.class` 三種 token,**不判斷**。`Type.class` 要列 —— 陽性一的向量正是
  `Order.class.getDeclaredMethods()`。
- 副(恆真分診):檢查器印一段**固定提醒**,講第三類「範圍不足」兩支都抓不到,並以票 13 的
  陽性一、二為例點名(同 `vacuous_tests.py` 檔頭點名 HL1/HL2 的寫法)。**它不跑 PIT。**

## 預測(逐條可落空)

### P1 對 `runs/2026-08-19-act4/` 跑 → 離開碼 **1**,契約 17/17 無落點

沒有任何 `@covers`,所以第一段每條契約都印「無落點」;舊約定那行印 **9 條**;第二段(反向)
是空的(沒有宣告就沒有漂);第三段 6 支檔各列出型別呼叫,其中 `OrderImmutabilityTest`
那格要含 `Order.class`。

→ 落空條件:回 3(把「有檔但沒宣告」折成不適用);回 0;無落點不是 17 條;
  舊約定計數不是 9;`OrderImmutabilityTest` 那格沒有 `Order.class`。

### P2 `vacuous_tests` 那半:**佇列不會含陽性一、二**

票的完成定義寫「`vacuous_tests` 那半印出陽性一、二」。**我預測相反**:票 13 自己的修正 2
已經說陽性一不是恆真(加一個 public 實例 mutator 它會紅),它是**範圍不足**;陽性二的三條
非法轉移測試殺得掉守衛消失的 mutant,也不會被支配。所以 dominated 佇列**不含**
`OrderImmutabilityTest.C8_…` 與 `OrderStatusTransitionTest` 的三個方法。
「印出陽性一、二」由檢查器的固定提醒行滿足,不是由佇列滿足。

前提:能在 scratchpad 複本上把 PIT 跑起來(`./gradlew innerTest` 先綠,再加 pitest +
`fullMutationMatrix=true`)。**跑不起來就寫「沒驗過」**,P2 記「無法對答案」,不算命中也不算落空。

→ 落空條件:佇列裡出現上述四條之一。那會是值得寫進 RESULT 的發現(偵測器比票以為的更靈,
  或它靠的是 `@BeforeEach`-型的共用擊殺)。

### P3 heredoc 改後 blob ≠ `d4a17c9a…`,而且 diff 只有一句

改後 dry run 一次,`prompt.txt` 的 blob 變了;`diff` 改前改後只多出**一段**(第四節裡加的那句
「內圈測試檔頭必須 `@covers C<n>` / `@covers S<n>`」),其他行零變動。
舊的「方法名要帶契約編號」那句**留著**(只加不改)—— prompt 會同時載兩種約定,票裡「廢掉」
那半這次不落地,寫進 RESULT。

→ 落空條件:diff 超過那一段;或 blob 沒變(heredoc 沒改到)。

### P4 合成三態(pytest,tmp dir)+ 考卷

- 沒有 `src/innerTest/` → 3;store 0 契約 0 情境 → 3
- 目錄在、零個 `.java` → 1;目錄在、有檔、零 `@covers` → 1,每條契約無落點
- 每條契約都有 `@covers` → 0
- `@covers C99`(store 沒有)→ 1,第二段點名 `C99`
- 一支檔 `@covers C8, C9` 兩條都算落點(一檔多條,舊約定做不到的那件事)
- 考卷 `fixtures/exams/innertest_landing_check/` 至少 clean(0)/ 舊約定無落點(1,片段抽自
  `runs/2026-08-19-act4/` 的 `MoneyTest.java` 檔頭)/ 不適用(3)/ 漂(1)/ 用法錯誤(2)
  五個 case,`python3 exam.py` 全命中,exit 0;`innertest_landing_check` 從「無考卷」佇列消失,
  `package_landing_check` 還在。

→ 落空條件:任何一格對不上;pytest 總數不是 396 + 新增條數。

### P5 上限印在報表裡

三條:`@covers` 是一條約定(隨便寫 `@covers C1` 就過,只證明落點存在);「打在哪個入口」
那欄是第 4 階人讀、陽性一抓不到;第三類「範圍不足」兩支都抓不到。**不是要修**,是要印出來。

→ 落空條件:報表沒印;或有人把它當賣點。
