# 票 12 的預測(寫在動任何 code 之前,2026-08-19)

交付物:`tools/harness/run_act4.sh` —— 幕四的 runner,把 ADR 0006 的決定寫成 prompt。
**不含真的跑一次 `claude -p`**(付費,併到下次)。

這張票沒有數字可量(不跑 agent 就沒有「幾條綠幾條紅」),所以下面每一條押的是
**我自己的判斷會在哪裡出錯**,而不是 agent 的行為。每條都寫得出「什麼結果會讓它落空」。

## 形狀(不是預測,是查證過的事實)

1. **骨架有的是兩支驗收 + 一套架構**:`acceptance.OrderAcceptanceTest`(8 條)、
   `acceptance.OrderProxyAcceptanceTest`(4 條)、`architecture.ArchitectureTest`(4 條)。
   票 10 實測 12/12 紅、架構 4/4 綠而且命中 0 個 class(記「不適用」)。
2. **這份規格用不到外部替身**(票 10-RESULT 三個獨立證據)。ADR 0006 §2 的
   「HTTP 假服務」是**另一份規格**(`act1-opus-rerun/SPEC-draft.md`)的事,本 runner 不涵蓋。
3. **seam 的來源是散文自己的〈契約〉表**:C1–C11 每列的「守在哪個聚合根內」欄
   (`input-SPEC.md` L177-L190)。不需要問人 —— 查表。
4. **「不得開工」是 L288 那三條**、**「完成的定義」是 L298 那節**(S1–S12,S13 不列入)。
5. **骨架與 `run_act2.sh` 都不准改**;要注入的 gradle 設定只能進**工作目錄那份複本**。
   → 隔離靠 **runner 注入**,不是改凍結骨架。這是刻意的決定,不是漂移。

## 預測(逐條可落空)

### P1 結構隔離做得到,而且要**兩片**才夠

我押:單靠「多一個 `innerTest` source set」**不夠** —— 那只擋得住乖乖把測試寫進
`src/innerTest/java` 的 agent。真正的攻擊面是 **agent 直接在 `src/test/java/acceptance/`
底下新增一支 `SneakyTest`**,那樣它就跟著 `./gradlew test` 一起綠,而 `test` 綠正是完成的定義。

→ **預測:要 `sourceSets.innerTest` + `tasks.named('test') { filter { includeTestsMatching
'acceptance.OrderAcceptanceTest' / 'acceptance.OrderProxyAcceptanceTest' /
'architecture.ArchitectureTest' } }` 兩片一起才成立。**

**落空條件**:實測用兩個誘餌驗 ——
(a) `src/innerTest/java` 放一支**必紅**的測試 → `./gradlew test` 不跑它、`./gradlew innerTest` 跑它且紅;
(b) `src/test/java/acceptance/SneakyTest.java` 放一支**必紅**的測試 → `./gradlew test`
**不得**跑它。誘餌 (b) 若跟著跑了 → P1 的做法整個落空,filter 沒有按 class 名釘死。

### P2 `innerTest` source set 用 `extendsFrom testImplementation` 就編得起來,不用額外接 BOM

Spring Boot 的 dependency-management plugin 是對整個 project 生效的,不是對單一 configuration。

→ **預測**:
```
configurations {
    innerTestImplementation.extendsFrom testImplementation
    innerTestRuntimeOnly.extendsFrom testRuntimeOnly
}
```
加上把 `sourceSets.main.output` 掛進 compile/runtime classpath,就足以讓一支
`import org.junit.jupiter.api.Test;` + assertj 的內圈測試編得過、跑得動。

**落空條件**:編譯期 `package org.junit.jupiter.api does not exist`,或
`Could not resolve … no version specified`(表示版本沒被 BOM 管到,得手動釘版本)。
落空的話退路是 `innerTestImplementation.extendsFrom testRuntimeClasspath` 或直接
`classpath = sourceSets.test.runtimeClasspath + sourceSets.innerTest.output`。

### P3 我會在「防竄改」這一格判斷錯:**結構隔離擋不住 agent 改 `build.gradle`**

`build.gradle` 在工作目錄那份複本裡是**可寫的**。agent 只要刪掉 filter 那幾行,
它自己寫的測試就回到 `test` 裡。**結構分開 ≠ 防竄改。**

→ **預測:我做不到「防竄改」,只做得到「事後查得出來」** —— runner 在注入之後把
受保護檔(`build.gradle`、三支測試、`Application.java`、`application.properties`、
注入的 gradle 片段)的雜湊寫成基線,跑完再算一次比對,落 `tamper-check.txt`。
⚠️ 基線必須算在**注入之後**,否則第一個被自己的 tamper check 抓到的就是 runner 自己。

**落空條件**:如果我最後宣稱「結構隔離讓 agent 無法把自己的測試算進全綠」——
那句話是錯的,應該被打回。正確的說法是「**預設不算進去,而且改了看得出來**」。

### P4 洩題面:**prompt 本身會變成新的一片**,而我會想把「已知上限」寫進 prompt

ADR 0006 §3 那條上限(「class 放到別的 package → 整套架構檢查靜靜地不適用、
看起來跟完全遵守一模一樣」)寫進 agent 讀得到的 prompt = **把繞過的方法直接教給它**。

→ **預測:上限要分兩處寫** —— 給 agent 的那份寫成**正向要求**
(「實作必須落在 `com.shop.domain` / `usecase` / `adapter`,完成時三個都要有 class」),
繞過方法與可被形式滿足的那些話只寫在**檔頭 / README**(人讀的)。

**落空條件**:review 時發現 prompt 裡出現「否則檢查會不適用」這種句子 → 我沒守住。

### P5 `pytest tools/harness -q` 維持 **195 passed**

本票不碰 `tools/harness/*.py`,只新增一支 `.sh`。
**落空條件**:數字 ≠ 195。⚠️ 若落空,**先查票 14 的 commit**
(它正在動 `verify_generated.py` / `gen_archunit.py` / `package_landing_check.py`
與它們的測試),不要直接當成自己弄壞的。

### P6 `ACT4_DRY_RUN=1` 驗得完整條隔離鏈,只差 `claude -p`

→ **預測**:dry-run 跑完,工作目錄裡有 `spec/SPEC.md`、完整的 gradle 專案(無 `build/`、
無 `.gradle/`)、`prompt.txt`、`harness/inner-tests.gradle`、`skeleton-blobs.txt`、
`protected-baseline.txt`,而且**沒有** `result.json`。
另外:工作目錄裡**不得**出現生成器、store、`examples/shop/app/` 的任何檔案。
**落空條件**:上述任一檔缺席,或 `grep -rl "gen_acceptance\|acceptance.yaml"` 在工作目錄命中。

## 已知上限(要印進檔頭 / README,不是只寫在票裡)

1. **內圈測試靠方法名帶契約編號指認自己**(`C4_…`)—— 那是一條約定,
   隨便一條測試取名 `C1_xxx` 就通過。**只證明落點存在,不證明那條測試真的在驗 C1**(ADR 0006 §5)。
2. **結構隔離不是防竄改**(P3)。
3. **架構那套不是這份規格擁有的**,是從凍結骨架繼承的;空骨架階段一律記「不適用」。
4. **package 落點的坑仍然全開** —— 補它的是票 11 的 `package_landing_check.py`,不是本 runner。
5. **外部替身(HTTP 假服務)未涵蓋** —— 屬於 `act1-opus-rerun/SPEC-draft.md`,那份一條情境都沒落檔。
6. **完成 = script 綠 + 隔離驗過**,不含真的跑一次(付費,併到下次)。

## 驗收

- [ ] `bash -n tools/harness/run_act4.sh` 綠
- [ ] `ACT4_DRY_RUN=1` 跑完,P6 的檔案清單逐項對得上,且無答案卷洩漏
- [ ] 兩個誘餌實測(P1):`src/innerTest` 那支不跟 `test` 跑;`acceptance.SneakyTest` 不跟 `test` 跑
- [ ] `python3 -m pytest tools/harness -q` = 195 passed(P5)
- [ ] `examples/shop/app/`、`examples/shop/spec/`、`examples/shop/app-from-interview/`、
      `tools/harness/run_act2.sh`、`tools/harness/interview-prompt.md`、`examples/shop/harness/act1/`
      **git diff 一個位元組都沒有**
