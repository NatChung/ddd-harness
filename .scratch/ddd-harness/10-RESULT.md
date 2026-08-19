# 票 10 的實際結果(2026-08-18)

骨架:`examples/shop/app-from-interview/`
規格:`runs/2026-08-18-act2-from-interview/input-SPEC.md`
store:`runs/2026-08-18-act2-rerun/agent-acceptance.yaml`
生成物:`runs/2026-08-18-act2-rerun/generated-Order{,Proxy}AcceptanceTest.java`(逐位元組複製,只去掉 `generated-` 前綴)

## 逐條對預測

| 預測 | 結果 |
|---|---|
| P1 12/12 全紅,而且是 runtime 紅(編譯必須綠) | ✅ `compileTestJava` EXIT=0;`test` 12/12 failures,0 errors |
| P2 紅的理由恰好兩類:A 類 8 條、B 類 4 條 | ✅ 逐條對上,見下 |
| P3 架構 4/4 綠,而且 4 條的 that() 命中 0 個 class | ✅ `build/classes/java/main` 只有 `Application.class`,它住 `com.shop` 不住三個子 package |
| P4 `verify_generated.py` 印 ok | ❌ **落空** —— 它整支 crash,見下 |
| P5 拿掉 `data.sql` 後數字不變、context 起得來 | ✅ 12 條全是 404 斷言失敗,沒有 context load 失敗 |
| P6 pytest = 161 passed | ✅ 161 passed |

## 12 條紅的分類(真實輸出,從 `build/test-results/test/*.xml` 解析)

例外型別 **12 條全部是 `org.opentest4j.AssertionFailedError`** —— 所以照型別分類分不出東西,
分類看的是**斷言訊息**:

**A 類(8 條)—— `orderIdOf` 的守門斷言:`POST /orders 應回 201,實際 404 NOT_FOUND`**
S1 S2 S3 S11(OrderAcceptanceTest)+ S8 S9 S10 S12(OrderProxyAcceptanceTest)
> `[POST /orders 應回 201,實際 404 NOT_FOUND,body={"timestamp":"…","status":404,"error":"Not Found","path":"/orders"}] expected: 201 but was: 404`

**B 類(4 條)—— 情境自己的狀態碼斷言:`請求應被拒絕`**
S4 S5 S6(`expected: 400 but was: 404`)、S7(`expected: 401 but was: 404`)
> `[請求應被拒絕,body={…"status":404…}] expected: 400 but was: 404`

沒有第三類。沒有 context load 失敗。沒有編譯錯。

## 架構那套:**不適用**,不是通過

```
### 機械檢查:第 5 課的相依性原則: tests=4 failures=0 errors=0 skipped=0
  GREEN  domain/ 不得 import usecase/ 或 adapter/(內層不知道外層)
  GREEN  domain/ 不得 import 任何框架(Spring、JPA、Jackson)
  GREEN  usecase/ 不得 import 任何框架(Spring、JPA、Jackson)
  GREEN  usecase/ 不得 import adapter/(介面宣告在內層,實作在外層)
```

4 條綠,**4 條的 `that()` 都命中 0 個 class**(`main` 底下只編出 `Application.class`)。
`allowEmptyShould(true)` 讓它們過。**這 4 個綠燈裡沒有任何資訊 → 記「不適用」。**
一個什麼都不寫的 agent 在這裡是免費綠的(ADR 0006 §1)。

## P4 落空的原因:`verify_generated.py` 對「沒有架構規則的 store」整支 crash

`gen_archunit.generate()` 在查不到規則時 `raise SystemExit("store 裡沒有生成得出來的規則…")`
(`gen_archunit.py`,`if not rules:`)。當 CLI 用沒問題,但 `verify_generated.py`
是**把它 import 進來當函式呼叫**的 —— `SystemExit` 直接把整支 drift check 打死,
stdout 一行都沒印、exit 1。

→ **後果:任何「沒有 architecture_rule」的 store 都無法做 drift check**,而這份 store 正是。
→ 本票**沒有**改 `tools/harness/`(票 11 正在動那裡),改用等價的直接比對驗證:
  重新 `gen_acceptance.py` 生一份到 temp,跟骨架裡那兩支 `diff` ——
  **兩支都 byte-identical**,而且生成器印出 12 個方法(8 + 4),與骨架一致。

## 骨架 blob 雜湊基線(受測品紀律第 2 條)

留法:`git ls-files -s examples/shop/app-from-interview` —— 每次跑幕四時把這份輸出
存進該次的 run 目錄,寫報告前 `diff` 上一跑那份。基線(本票交付時):

```
100644 67bcc2f72725f6057a8ff744444db07d234fb991 .gitignore
100644 a1bb13dddf79b4723600e19035aabc13a8b1b59c build.gradle
100644 eddabd2eef8d94a5437d6168ff9c87a78ff725b3 gradle/wrapper/gradle-wrapper.jar
100644 680d395227a83b3998048d0659276f093dcc7ffa gradle/wrapper/gradle-wrapper.properties
100755 249efbb032ce46a80c687c0723eb172e85f6a136 gradlew
100644 8508ef684d4e1f8473dcbbfdacf52a131beaee0e gradlew.bat
100644 bebd6e2333b68ba0efcadfcfe34a77e3b590c812 settings.gradle
100644 5a370aea0e0194e182d8f5ae2d37db4348926aa6 src/main/java/com/shop/Application.java
100644 a47ed52539e07dd0fce4490779a0c0b736d86b31 src/main/java/com/shop/adapter/.gitkeep
100644 9dee53eee4d816654fc3194c5446ae3881e67c2e src/main/java/com/shop/domain/.gitkeep
100644 20ae87554905f1d18a4b82c61208be49cea8a5ce src/main/java/com/shop/usecase/.gitkeep
100644 849e2d81362abd416b6842845e3526be6dc48fe9 src/main/resources/application.properties
100644 fd36ac912fbed2e41df3efe26d137c82834ae8e5 src/test/java/acceptance/OrderAcceptanceTest.java
100644 ca788e7f10a9218a1bcbf39f7ebc326b6870ed0f src/test/java/acceptance/OrderProxyAcceptanceTest.java
100644 b2a5705cc716f531e3ba737ce9eec8af91fbbad0 src/test/java/architecture/ArchitectureTest.java
```

## 外部替身(HTTP 假服務):**未做**

三個獨立證據說這份規格用不到:

1. store(`agent-acceptance.yaml`)頂層只有 `wire_contract` 與 `acceptance_scenarios`,
   **沒有任何外部系統模型**;
2. 散文 `input-SPEC.md` L234:「通知 / 外部系統串接 —— `暫定 [Q5]` 還沒規劃到那裡」;
3. S1–S12 逐條讀過,**沒有任何一條需要外部系統回失敗或逾時**。S12 是「持久化中途故障」,
   而它被編成**代理情境**(schema 送不出中斷那一步),連進程內的故障注入都沒有。

「兩支外部替身 + 逾時」是**另一份規格**(`runs/2026-08-18-act1-opus-rerun/SPEC-draft.md` §10)
要的,那份**一條情境都沒落檔**、生不出任何測試 —— 記成缺口,不是本票交付。

## 記下來的缺口(不是本票交付)

1. **三套測試 / 兩支外部替身 / 逾時** —— 屬於 `act1-opus-rerun/SPEC-draft.md`,
   等它走完幕二、生得出測試才輪到補。
2. **架構那套不是這份規格擁有的** —— store 生不出來,散文 L304 自己寫「機械檢查一條都沒有」。
   它是從凍結骨架繼承的;等有實作了,它報的也是*凍結那份規格*的架構觀點。
3. **package 形狀同樣是繼承的** —— 這份規格沒宣告過任何 package。
   ADR 0006 §3 那個「agent 換 package 名 → 整套架構檢查靜靜地不適用、看起來跟完全遵守
   一模一樣」的坑**在本票交付後仍然全開**,補它的是票 11。
4. **`verify_generated.py` 的 `SystemExit` 缺陷**(見上)—— 沒改,留給票 11 或另開。
5. **票面說生成物有 16 個 `@Test`,實際是 12 個**(8 + 4,對應 S1–S12)。
