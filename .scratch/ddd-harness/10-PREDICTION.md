# 票 10 的預測(寫在動任何 code 之前,2026-08-18)

形狀由 `docs/adr/0006` §2/§3/§6 定死,這裡不重複論證形狀。
這份只寫死一件事:**空骨架真的跑起來之後,會量到什麼** —— 包含紅幾條、紅的理由分幾類。

「骨架建得起來」不可能失敗,**不用**。下面每一條都寫得出「什麼結果會讓它落空」。

## 它做什麼

從凍結的 `examples/shop/app/` 複製一份到 `examples/shop/app-from-interview/`,
讓 `runs/2026-08-18-act2-rerun/` 那兩支生成物**跑得起來**:
build 檔、`Application.java`、三個空的實作 package、把生成物放進 `src/test/java/acceptance/`。
**不填任何實作**(那是幕四 agent 的事,要付費,不在本票)。

## 動手前先查證過的四件事(不是預測,是事實)

1. **生成物是 12 個 `@Test`,不是票寫的 16 個。**
   `grep -c 'void scenario_'`:`generated-OrderAcceptanceTest.java` = **8**
   (S1/S2/S3/S4/S5/S6/S7/S11),`generated-OrderProxyAcceptanceTest.java` = **4**
   (S8/S9/S10/S12)。共 12,對得上散文的 S1–S12(S13 是刻意留白的阻斷級缺口)。
   **票 10 與派工單寫的「16 個 @Test」是錯的**,底下所有預測用 12。
2. **這份 store 生不出架構檢查。**
   `python3 tools/harness/gen_archunit.py <act2-rerun store>` 印:
   `store 裡沒有生成得出來的規則,沒有東西可生成` —— 一個檔案都沒產。
   `agent-acceptance.yaml` 頂層只有 `wire_contract` 與 `acceptance_scenarios` 兩個 key。
   而散文 `input-SPEC.md` L304 自己寫著:**「機械檢查(ArchUnit 之類)目前一條都沒有,
   架構規則靠人工守;這是已知缺口,不是遺漏。」**
   → 新骨架裡的 `ArchitectureTest.java` 是**從凍結骨架繼承來的,不是這份規格擁有的**。
3. **這份規格用不到外部替身。** 三個獨立證據:
   store 裡沒有任何外部系統模型;散文 L234「通知 / 外部系統串接 —— `暫定 [Q5]` 還沒規劃到那裡」;
   S1–S12 逐條讀過,**沒有任何一條需要外部系統回失敗或逾時**
   (S12 是「持久化中途故障」,而它被編成代理情境 —— schema 送不出中斷那一步)。
4. **環境有貨**:`~/.gradle/wrapper/dists/gradle-8.14-bin` 已快取、
   `~/.gradle/caches/modules-2/files-2.1/` 底下有 `org.springframework.boot` 與
   `com.tngtech.archunit`、`java -version` = 17.0.19。**所以 gradle 應該跑得動**。

## 預測(逐條可落空)

### P1 空骨架跑起來 → 驗收 **12 / 12 全紅**,而且**全部是 runtime 紅**

編譯必須過。兩支生成物的 import 全是 Spring / Jackson / assertj / JUnit,
唯一引用的 `com.shop` 型別是 harness 自己的 `Application`。

→ **預測:`compileTestJava` 綠,`test` 12 條全紅。**
落空條件:**任何一條綠**(表示空專案上有東西湊巧滿足了斷言),
或**編譯錯**(表示我不小心讓測試依賴了實作型別 —— 那會直接打破
「測試不 import 任何實作 class」這條整線最核心的不變式)。

### P2 紅的理由**恰好兩類**,而且分類看的是**斷言訊息**不是例外型別

兩類的例外型別都是 `org.opentest4j.AssertionFailedError`,
**照例外型別分類的話任何結果都塞得進去** —— 所以照訊息分:

| 類 | 訊息 | 幾條 | 哪幾條 |
|---|---|---|---|
| A | `POST /orders 應回 201,實際 404` (`orderIdOf` 的守門斷言) | **8** | S1 S2 S3 S11 + S8 S9 S10 S12 |
| B | `請求應被拒絕` (情境自己的狀態碼斷言,400/401 vs 404) | **4** | S4 S5 S6(400)、S7(401) |

理由:空專案沒有任何 controller,`POST /orders` 與 `GET /orders` 都是 Spring 的預設 404。
成功情境第一句就撞 `orderIdOf` 的 201 守門;被拒情境第一句是自己的 400/401 斷言,
先撞到它,還走不到 `customerIdsInList()`。

→ 落空條件:**出現第三類**。最誠實的替代結局是
**context 起不來**(零個 `@Entity` 的 JPA、`data.sql` 被我拿掉之後的 sql init)
→ 12 條全變 `IllegalStateException: Failed to load ApplicationContext`,那就是 **1 類 12 條**。
凍結骨架跑過同型的空骨架(`act4-result.txt`:「空骨架 → 4/4 紅」)所以我賭不會,
但這是它落空時最可能的樣子。
也可能落空成 **A 類 ≠ 8 / B 類 ≠ 4**(例如 `listRows()` 的 GET 斷言先炸)。

### P3 架構那套 **4 條全綠,而且那 4 條綠全是空的** —— 記成「不適用」

`ArchitectureTest` 四條規則掃 `com.shop`,而 `main/java` 底下只有 `Application`
(它住 `com.shop`,不住 `com.shop.domain/usecase/adapter`)。
四條的 `that()` 全部命中 0 個 class,`allowEmptyShould(true)` 讓它們過。

→ **預測:架構 4 / 4 綠,而每一條的 `that()` 命中數都是 0。**
→ **報告不准把它算成「通過」,要記成「不適用」**(ADR 0006 §1,規矩同 ADR 0005 §6)。
落空條件:有任何一條紅(表示我建的空目錄裡不小心留了型別),
或有任何一條命中 > 0 個 class(同上)。

### P4 `verify_generated.py` 對新骨架 **不漂**

複製時要把檔名的 `generated-` 前綴拿掉(Java 的 class 名必須等於檔名),
內容則**一個位元組都不改**。

→ **預測**:`python3 tools/harness/verify_generated.py
examples/shop/app-from-interview/src/test/java/acceptance <act2-rerun yaml>`
印 `ok: 生成物與 spec 一致`,三個檔全 ✅
(`ArchitectureTest.java` 是**空對空**地過:store 生不出來、那個目錄裡也沒有它)。
落空條件:任一檔 ❌ —— 那表示我在複製時手改了生成物。

### P5 `data.sql` 拿掉之後**沒有任何一條測試因此改變結果**

`data.sql` 的 `customers` 表是**凍結那份規格**的道具(它的列表要顯示 `customerName`)。
這份規格的 `list_fields` 是 `orderId / customerId / items / currency / placedAt /
status / totalCents` —— **沒有 customerName**,訂單只保存客人編號(散文 L223),
12 支測試沒有一支讀姓名。

→ **預測:拿掉 `data.sql` 之後 P1/P2 的數字一模一樣。**
理由不是「省事」,是**洩題面**:`C-001 = Alice` 對這份規格零功能,卻是一條
指向「讀取側 join 姓名」的假線索 —— 而這份規格根本沒有那個需求。
落空條件:拿掉之後 context 起不來,或紅的條數/類別跟 P1/P2 對不上。
(若落空,退回保留 `data.sql` 並把它整條列進洩題面。)

### P6 pytest 基線不動:**161 passed**

本票不碰 `tools/harness/`(票 11 正在動那裡)。
→ 落空條件:任何數字不是 161。

## 已知上限(要印進報告,不是只寫在票裡)

1. **三套測試 / 兩支外部替身 / 逾時,是另一份規格(`act1-opus-rerun/SPEC-draft.md`)要的,
   本票不交付。** 那份**一條情境都沒落檔**,生不出任何測試 —— 骨架做了也跑不起來。
   記成缺口,等它走完幕二再補。
2. **架構那套不是這份規格擁有的。** store 生不出來(事實 2),散文自己說「一條都沒有」。
   它是從凍結骨架繼承的,**空骨架階段一律「不適用」**;等到有實作了,它報的也是
   *凍結那份規格*的架構觀點,不是這份的。
3. **package 形狀同樣是繼承的。** 這份規格從頭到尾沒宣告過任何 package;
   `com.shop.domain / usecase / adapter` 是被兩件事逼出來的:生成物寫死
   `classes = com.shop.Application.class`,以及要繼承的 `ArchitectureTest` 就是掃那三個。
   → **ADR 0006 §3 那個「agent 把 class 放到別的 package,整套架構檢查靜靜地不適用」的坑,
   在本票交付之後仍然全開** —— 補它的是票 11,不是這張。
4. **「空骨架全紅」在驗收那半是結構保證的,在架構那半不是**(ADR 0006 §1)。
   報告要兩半分開印,不准合成一個「N 綠 M 紅」。
5. **完成 = 空骨架跑得起來且紅得對**,不含「找 agent 來填」(要付費,併到下次)。

## 洩題面(哪些檔 agent 讀得到、哪些值是答案卷)

新骨架整個目錄 agent 都讀得到。逐檔:

| 檔 | agent 讀得到什麼 | 是不是答案卷 |
|---|---|---|
| `src/test/java/acceptance/OrderAcceptanceTest.java` | **12 條情境的完整輸入與期望值** | ✅ **是,而且是最大那張** —— 但它必須讀得到(驗收就是題目) |
| `src/test/java/acceptance/OrderProxyAcceptanceTest.java` | 同上,4 條 | ✅ 同上 |
| `src/test/java/architecture/ArchitectureTest.java` | **package 名 `com.shop.domain/usecase/adapter` 與四條相依方向** | ⚠️ **是** —— 規格沒宣告 package,這個檔等於偷偷把答案講了 |
| `src/main/java/com/shop/Application.java` | base package = `com.shop`;Spring Boot | 半 —— 生成物本來就寫死它 |
| `build.gradle` | Spring Boot 3.4.5 / JPA / H2 / ArchUnit **技術選型整組** | ⚠️ **是** —— 規格沒指定過任何技術棧 |
| `application.properties` | H2 in-mem、`ddl-auto=create-drop`、JPA 開著 | ⚠️ **是** —— 等於指定了持久化做法 |
| `src/main/java/com/shop/{domain,usecase,adapter}/` 空目錄 | **要分三層,而且叫這三個名字** | ⚠️ **是** |
| ~~`data.sql`~~ | ~~`C-001 = Alice`~~ | **已刪**(P5)—— 對這份規格零功能的洩題 |

**最大的一條**:`build.gradle` + `application.properties` + 空 package 三個加起來,
等於已經替 agent 決定了「Spring Boot 分層 + JPA」。這份規格**沒有**授權過這件事
(散文 L202:「沒有任何被授權為架構模板的文件」)。**這是骨架自己帶進來的先驗,
不是規格帶進來的** —— 跨模型比較時兩份實作共享這個先驗,所以比較得出來;
但**不能拿它當「規格夠不夠完整」的證據**。

## 受測品紀律(ADR 0006 §6 三條)

1. 每個 harness 提供的檔頭寫警語(照 `tools/harness/run_act2.sh` 那份的風格)
2. 每跑在 run 目錄留骨架的 blob 雜湊(`git ls-files -s` 的 sha),寫報告前 diff
3. 洩題面清單(上一節)

## 驗收(綠 + 逐條可紅)

- [ ] `./gradlew compileTestJava` 綠(P1 的前半)
- [ ] `./gradlew test --tests 'acceptance.*'` → **12 條全紅**,A 類 8 / B 類 4(P1 P2)
- [ ] `./gradlew test --tests 'architecture.*'` → 4 條全綠,而**報告記「不適用」**(P3)
- [ ] `verify_generated.py` 印 ok(P4)
- [ ] `examples/shop/app/` 與 `examples/shop/spec/` **git diff 一個位元組都沒有**
- [ ] `python3 -m pytest tools/harness -q` = **161 passed**(P6)
