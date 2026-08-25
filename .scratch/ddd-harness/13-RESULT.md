# 票 13 的實際結果(2026-08-25)

對答案:`13-PREDICTION.md`(commit `02ac617`,寫在 `innertest_landing_check.py` 之前)。

交付:`tools/harness/innertest_landing_check.py`(新)、`tools/harness/test_innertest_landing.py`
(新,16 條)、`tools/harness/fixtures/exams/innertest_landing_check/`(5 case)、
`tools/harness/run_act4.sh`(heredoc 第四節加一句)、`PIPELINE.md` 幕四加一段、本檔與預測檔。

## 逐條對預測

| 預測 | 結果 |
|---|---|
| P1 對 `runs/2026-08-19-act4/` 跑 → **1**,契約 17/17 無落點 | ✅ 命中。rc=1;「契約 17 條、情境 5 條;內圈測試檔 6 支,其中檔頭帶 `@covers` 的 0 支;舊約定方法名帶編號 9 條(不算落點)」;第二段印「沒有任何宣告,所以沒有東西可以漂」;`OrderImmutabilityTest` 那格 `Type.class:Order、UnsupportedOperationException` |
| P2 `vacuous_tests` 佇列**不含**陽性一、二 | ❌ **落空一半**。陽性一(`OrderImmutabilityTest.C8_…`)不在佇列(殺 19、獨佔 0、沒被支配);但陽性二的 **`OrderStatusTransitionTest.C9_…` 與 `C17_…` 在佇列**(最小共殺 2、殺 7、獨佔 0)。落空條件是「上述四條之一出現」,所以算落空。細節見下 |
| P3 heredoc 改後 blob ≠ `d4a17c9a…`,diff 只有一段 | ✅ 命中。改後 `c444497839687ce9de213ce1c848066524f577f3`;`diff -u` 只多出第四節末那一段(3 行),其他零變動。改前 blob 與 `runs/2026-08-19-act4/prompt.txt` 在 index 裡的 blob 相同 —— heredoc 從 2026-08-19 到改之前沒漂 |
| P4 合成三態 + 考卷 | ✅ 命中。16/16 pytest(含對真實 run 的 P1 一條);考卷 5 case 全命中,`exam.py` exit 0(25 case → 合併票 26 後 31 case);`innertest_landing_check` 不在「無考卷」佇列,`package_landing_check` 還在(`act4_order_check` 也在,那是票 24 的,不是本票的)。pytest 總數 396 → 417(+16 測試 +5 考卷 case);合併 main `c1173d5` 後 457 |
| P5 上限印在報表 | ✅ 命中。三條上限 + 副那段固定提醒都印;有 pytest 釘著 |

**命中 4 / 落空 1(P2 一半)。**

## P2 的落空是什麼(驗過,scratchpad 複本)

run 目錄不動:複製 `runs/2026-08-19-act4/` 到 scratchpad,`./gradlew innerTest` 先綠(9/9),
再加 `info.solidsoft.pitest 1.15.0` / pitest 1.15.0 / junit5-plugin 1.2.1(全在 gradle cache,
沒下載),`testSourceSets = [sourceSets.innerTest]`、`fullMutationMatrix = true`、
`targetClasses = ['com.shop.domain.*']`。71 mutant,9 條測試,PIT 6 秒。`vacuous_tests` 佇列 5/9:

```
最小共殺 4  殺  6  獨佔 0  OrderItemsRequiredTest.C3_…        ← 貢獻全來自共用 setup
最小共殺 4  殺 17  獨佔 0  OrderTotalAmountTest.C2_…_單一品項  ← 貢獻全來自共用 setup
最小共殺 4  殺 18  獨佔 0  OrderTotalAmountTest.C2_…_多個品項
最小共殺 2  殺  7  獨佔 0  OrderStatusTransitionTest.C17_…
最小共殺 2  殺  7  獨佔 0  OrderStatusTransitionTest.C9_…
```

C9 與 C17 進佇列的原因(從 `mutations.xml` 逐條算過):**兩條殺的是同一組 7 個 mutant**
(`Order.java:83` 的守衛 NegateConditionals、`place` 的兩個 NegateConditionals、`place` 的
NullReturn、`status()` 的 NullReturn …),於是**互相支配** —— 不是被 C16 支配(C16 殺 36,
但 `status()` 那個 NullReturn 它沒殺,所以 C9 / C17 的集合不是 C16 的子集)。這不是恆真 ——
`Order.java:83` 的守衛 mutant **確實被 C9 / C17 / C16 三條殺掉**(票裡的對照組 1 成立);
它是 `vacuous_tests` 檔頭自己寫的 (b)「跟另一條測試重複」那一類,而佇列分不出 (a)/(b)/(c)。

**票裡真正的漏(`RECEIVED -> null` 改成 `RECEIVED -> RECEIVED`,九條都不紅)PIT 根本沒生那個 mutant**
—— 71 個 mutant 分佈在 Money / Order / Quantity / OrderId / Sku / CustomerName / OrderItem /
DomainRuleViolation 八個檔,**`OrderStatus.java` 一個 mutant 都沒有**(預設 operator 對那個
enum 的 switch expression 一個都沒產;為什麼沒產沒查)。所以 P2 寫「C9 / C17 不會被支配」是我
預測錯,不是偵測器比票以為的更靈:它抓到的是重複,不是那個漏。

**預測之外的一個訊號**:`Order.java:51 restore` 的 mutant 是 **NO_COVERAGE** —— 九條內圈測試
沒有一條碰到 `restore`。這正是陽性一講的「範圍不足」,而且 PIT 資料裡有,只是 `vacuous_tests`
**只看測試、不看沒被任何測試蓋到的 mutant**,所以它沒印。第三類「範圍不足」在 `vacuous_tests`
現有的報表裡仍然看不見;`innertest_landing_check` 的固定提醒那行照舊。要不要讓 `vacuous_tests`
多印一段「NO_COVERAGE 的 mutant 落在哪些方法」,另開票,不在本票。

## 跟票的形狀不同的地方(刻意,不是漂移)

1. **契約決定離開碼,情境只印參考。** 票寫「每條契約 / 情境」;情境的落點是幕三生成的驗收
   (逐位元組驗過),要求每條情境也有內圈測試等於再犯一次「懲罰寫得好的那一方」。
   `@covers G16` 合法、反向段照查,只是不強制。
2. **情境編號不寫死 S。** 2026-08-19 那份 store 的情境是 `G1`、`G16`;編號從
   `domain_contract.id` / `acceptance_scenario.id` 讀。heredoc 那句照票寫 `S<n>`(prompt
   自己第一節就寫 S1–S12,那是既有的漂,本票不動)。
3. **目錄在但零個 `.java` → 1,不是 3。** `run_act4.sh` 自己會 `mkdir -p src/innerTest/java`,
   空目錄正是「agent 什麼都沒寫」的長相;3 只留給「沒有 `src/innerTest/`」與「store 0 契約 0 情境」。
4. **`@covers` 不在 class javadoc(方法 javadoc / 行註解)→ 列進反向段,不算落點,離開碼 1。**
   票只說「檔頭」;放錯位置算漂,不算宣告。
5. **只加一句,不刪舊句。** heredoc 裡「每條內圈測試的方法名要帶它在驗的那條契約編號」留著,
   `run_act4.sh` 檔頭上限 2 也還寫著方法名那條。票說舊約定「廢掉」—— 這次沒落地,prompt 同時
   載兩種約定;下次真跑要看 agent 兩種都寫、還是只寫一種。

## 沒做到 / 沒驗過

- **真 claude 沒照新 prompt 跑**(要錢;而且合併票 24 / 26 後 runner 環境已跟 2026-08-19 不同)。
  「agent 真的會在檔頭寫 `@covers`」沒驗過;「`@covers` 會不會被形式滿足」(隨便寫 `@covers C1`)
  也沒驗過 —— 上限印在報表裡。
- PIT 跑的是 **scratchpad 複本**,`build.gradle` 加了 pitest 段;run 目錄本身一個位元組沒動。
  mutation matrix 沒進 repo(`vacuous.out` / `mutations.xml` 都在 scratchpad)。
- 票裡的四個 mutant 對照組(刪守衛 / `RECEIVED -> RECEIVED` / 拿掉 `EMPTY_ORDER` / `Money` 的
  `currency != null`)**沒有手動逐個做**;PIT 資料只覆蓋到預設 operator 產得出來的那幾個。
- `harness/act4.git` 那份歷史對 `src/innerTest/**` 的先後(內圈測試是不是先於實作)本票沒查,
  那是 `act4_order_check` 的範圍(它只看 `src/test/**`)。
