# harness —— 第三幕的生成器

> **要看整條線(幕一到幕五、每段驗過沒有)請讀 [`PIPELINE.md`](./PIPELINE.md)。**
> 本檔只講第三幕的生成器。

把 spec 裡的**規則**變成**機械檢查**。第 9 課階梯的搬階動作,做成 script。

```
architecture.yaml ─┐                        ┌─gen_archunit───▶ ArchitectureTest.java   (第 2 階)
                   ├─spec_store──▶ spec.db ─┤
acceptance.yaml   ─┘   (schema 擋)          └─gen_acceptance─▶ OrderAcceptanceTest.java (第 3 階)
                                                                    │
                                              verify_generated ◀────┘  兩個都重新生成再比
```

分兩份 spec 檔是因為**關注點**不同(架構規則 vs 驗收情境:不同的 reviewer、
不同的改動節奏),合併發生在 `spec_store`,不是要人自己 concat。

## 為什麼是這個形狀

| 決定 | 為什麼 |
|---|---|
| **agent 只交 yaml,碰不到 schema** | schema 是我們的。agent 改不掉規則,只能交資料。若讓它下 SQL,它也能 `CREATE TABLE` 繞過 —— 那就退回第 4 階(靠它不繞) |
| **結構化進 store,散文留 markdown,不重疊** | 兩份真相會漂。凡是進 store 的欄位,散文那份要整段刪 |
| **生成物進 git 並凍結,build 期做 drift check** | 只生成不檢查 → spec 改了生成物不會跟;每次 build 重生 → agent 改 spec 就能放寬自己的考卷。丙 兩邊都堵 |
| **生成器回填「由誰強制」** | 誰生成的誰知道生了什麼。人手寫會寫錯,也會忘記更新 |
| **輸出確定性(無時間戳、排序固定)** | 否則 drift check 每次都紅,然後就沒人看它了 |

## 哪一條住第幾階(不要混)

| 階 | 這裡的實例 |
|---|---|
| **1** 做不到 | `schema.sql` 的 CHECK / REFERENCES / TRIGGER。**`模板既定` 在白名單為空時物理上寫不進去** —— 歷史上模型兩輪把自決偽裝成既定,那條規則靠自覺守不住 |
| **2** 會被擋 | `spec_store.py` 的跨列不變式(kind ↔ 參數)、`verify_generated.py` 的 drift check、生成出來的 ArchUnit 規則 |
| **4** 文件 | `architecture.yaml` 裡 `enforcement: none` 的那幾條 —— 它們的 `ladder_note` 就是**搬階清單的原料** |

查搬階清單:

```sql
SELECT id, enforcement, enforced_by, ladder_note
FROM architecture_rule ORDER BY enforcement, id;
```

## 三個尺度都有表了(2026-08-18,ADR 0005)

原本只有大尺度(`architecture_rule`,配了 `gen_archunit`)與小尺度(`wire_contract`,
生成器兩側都讀它)有表。微尺度與詞彙表**只活在散文裡** —— 於是一條 invariant 進得了
store 的唯一形式,是被寫成某一條情境的斷言(**invariant 被降級成 example**);
而「實作命名必須照詞彙表」那句話**沒有任何一步會去讀**。

| 尺度 | 表 | 配的檢查 | 買到什麼 |
|---|---|---|---|
| 大 | `architecture_rule` + 三張參數子表 | `gen_archunit.py` | 規則變成可執行的 ArchUnit 測試 |
| 小 | `wire_contract` / `wire_list_field` | 兩支生成器都讀 | 欄位名歸規格擁有,實作照做 |
| 微 | `domain_contract` + `contract_named_test` | `contract_triage.py` | 「有沒有指名測試」「哪幾條守不住」變成兩句 SELECT |
| 詞彙 | `glossary_term` + `glossary_banned_synonym` | `glossary_check.py` | 「對外欄位名對不對得到一個詞」變成一個**查得出來的差額** |

⚠️ **兩張新表都不生成任何可執行的東西。** 它們買的是**分診**,不是強制:

- `domain_contract` 的 `enforcement` 值域今天**只有 `none`**(沒有任何生成器讀它)。
  「有指名測試」與「由誰強制」是**兩欄,不得合併** —— 合併就把
  invariant → example 的降級整個蓋住,而那正是這張表要抓的東西。
  ⚠️ 這條 2026-08-18 之前**在測試層沒有任何守衛**:把兩欄在報表層合併(`with_enforcement
  = with_test`)、或把閘門改成無條件 `return 0`,24 支測試全綠。現在
  `test_有指名測試不等於有機械檢查_兩欄分開印` 造一個 with_test=1 而 with_enforcement=0
  的 store,任何一個方向的合併都會翻紅。
- `glossary_check.py` 的對譯檢查是**第 2 階報告,不是 FK**。硬擋只拿得到「匯入失敗」,
  拿不到「差幾個」—— 而那個數字就是這條檢查的全部價值。
- `glossary_term` 的「DDD 型態」是**自由文字**(只住第 4 階),刻意不做成固定清單:
  查過的兩份真實詞彙表型態用語幾乎不重疊,鎖清單會**逼出假資料**。

⚠️ **兩個新的頂層區塊(`domain_contracts` / `glossary_terms`)都是選填**,
所以兩支報表各自綁死一條:**「不適用」不算「通過」**,自成一類、印在最上面、
給自己的離開碼 3。而詞彙表這一側的不適用**有兩種**:詞彙表是空的、
或詞彙表有東西而這份 store 根本沒有對外合約可比 —— 後者更難看見,
因為計數上什麼都不缺。

## 用法

```bash
# 兩份 spec 一起進同一個 store —— gen_acceptance 要吃情境,合併發生在 spec_store
python3 spec_store.py import ../examples/shop/harness/architecture.yaml \
        ../examples/shop/harness/acceptance.yaml /tmp/spec.db
python3 gen_archunit.py   /tmp/spec.db ../examples/shop/harness/generated/ArchitectureTest.java
python3 gen_acceptance.py /tmp/spec.db ../examples/shop/harness/generated/OrderAcceptanceTest.java

# drift check 吃的是**放生成物的目錄** + 那些 spec 檔,順序不能反
#(反過來寫的話目錄參數收到一個 yaml → 離開碼 2「吃錯目錄」,不是 1)
python3 verify_generated.py ../examples/shop/harness/generated \
        ../examples/shop/harness/architecture.yaml \
        ../examples/shop/harness/acceptance.yaml
python3 -m pytest test_harness.py -q            # 離線,不碰 gradle
python3 acceptance_archunit.py ../examples/shop/harness/generated/ArchitectureTest.java /tmp/acc

# package 落點:規格宣告過的 package,實作產出裡真的有 class 嗎
python3 package_landing_check.py ../examples/shop/app/src/main/java \
        ../examples/shop/harness/architecture.yaml   # 凍結骨架是空的 → 離開碼 1

# 微尺度與詞彙:落檔之後跑分診,兩支都不生成任何可執行的東西
python3 spec_store.py import ../examples/shop/harness/runs/2026-08-18-act1-opus-rerun/contracts.yaml /tmp/contracts.db
python3 contract_triage.py /tmp/contracts.db      # 離開碼 3 = 不適用,不是通過

python3 spec_store.py import ../examples/shop/harness/glossary.yaml \
        ../examples/shop/harness/acceptance.yaml /tmp/glossary.db
python3 glossary_check.py /tmp/glossary.db        # 離開碼 3 = 不適用,不是通過
```

上面的路徑是上游(ddd-harness)的佈局:`../examples/shop` 是語料。在 hub 裡這個目錄是 `vendor.sh` copy
進來的副本,把 `../examples/shop/harness` 換成 hub 自己的 `specs/<feature>/` 就是了;hub 怎麼走五幕見
`hub-bootstrap.md`。讀語料的測試不在這裡,住上游 `examples/shop/tests/`;`python3 -m pytest` 在這個目錄
跑的是不碰語料的那些。

相依:JSON 走標準庫;YAML 需要 PyYAML(lazy import)。

## 驗收:綠 ＋ 逐條可紅

**純綠燈證明不了任何事** —— 一條恆真的測試也是綠的(分層實驗發現的洞層:「恆真反射測試」)。
所以 `acceptance_archunit.py` 有兩半:對乾淨骨架跑要全綠,**逐條把規則違反掉,只有對應那條變紅**。
第二半才是「這條規則真的被強制了」的證據。它每輪都複製 `examples/shop/app/` 到 scratch 再改
—— 那份骨架逐位元組凍結在 `4567d31`。

## 目前支援的 rule kind

| kind | 生成什麼 | 參數 |
|---|---|---|
| `archunit_forbidden_dependency` | `noClasses().that().resideInAPackage(from).should().dependOnClassesThat().resideInAnyPackage(…)` | `from` + `to[]` |
| `archunit_forbidden_annotation` | 自訂 `ArchCondition`,查**類別與其成員**掛的 annotation 是否落在指定 package | `from` + `annotations[]` |
| `archunit_forbidden_return_type` | `noMethods().that().areDeclaredInClassesThat()….should().haveRawReturnType(…)` | `from` + `class_name_suffix` + `return_packages[]` |

第三個 kind 的 `from` 是「package × **類名字尾**」而不只是 package,這不是為了彈性
—— **整個 adapter 層都禁會擋錯人**:`JpaOrderRepository` 也住 adapter,而它本來就該回傳
`Order`,那是它的工作。規則只針對 Controller。

annotation 那條刻意連 member 一起查:類別層級只看得到 `@Entity`,而把 `@Column` / `@Id`
掛在欄位上一樣是「領域物件直接當持久化模型」——**輪 1 實際出現的就是欄位層級**。
也刻意用 package 前綴而不是列舉 annotation 型別名:列舉是白名單式的不完整,漏一個
`@Embeddable` 就穿了。

## 驗收抓到的第一個發現:A6 被 A1 蓋住

`acceptance_archunit.py` 對每條規則記的是**預期變紅的集合**,不是「只有它紅」。
這個設計立刻換到一個發現:

```
✅ A6 違反 → 紅的正好是 ['A1', 'A6']     實際紅的是 ['A1', 'A6']
```

在 `domain/` 的欄位上掛 `@jakarta.persistence.Column`,**A1 與 A6 同時紅**
—— annotation 本身就是一條依賴,不寫 `import` 也一樣。所以 **A6 對 `domain/`
不增加任何偵測力**,它只把錯誤訊息從「domain 依賴了 jakarta.persistence」
換成「`Order.totalCents` is annotated with `jakarta.persistence.Column`」。

留著它的理由不是「多一層保險」,是兩件具體的事:A1 的清單若收窄它仍然守著;
以及錯誤訊息指得出是**哪個成員**。這件事寫進 `architecture.yaml` 的 A6 註解裡
—— 發現要留在資料旁邊,不是留在對話裡。

順帶拆出 **A12**:ARCHITECTURE.md L28-30 那句話裡,「不得掛 annotation」機械化得了,
「adapter 必須建立自己的持久化模型」機械化不了(ArchUnit 查得到「不該有的出現了」,
查不到「該有的沒出現」)。兩半原本混在同一句,是 A6 被蓋住之後才拆開的。

### 對照組:A10 沒有被蓋住

A6 的發現直接決定了第三個 kind 挑誰。A10(Controller 不得回傳 domain 型別)
**確定不會被任何依賴規則蓋住** —— adapter 本來就允許依賴 domain(它要做對映),
所以「Controller 回傳了 `Order`」不觸發任何 dependency 規則。實測:

```
✅ A10 違反 → 紅的正好是 ['A10']     實際紅的是 ['A10']
```

**只有 A10 紅。** 這是第一個能證明「新 kind 真的增加偵測力」的資料點
—— 而不是只換到比較好看的錯誤訊息。挑目標時先問「這條會不會被既有規則蓋住」,
比挑「哪條聽起來重要」有用。

⚠️ A10 擋不到的:回傳一個名字不像 domain、裡面卻包著 domain 物件的 wrapper
(例 `ApiResponse<Order>` —— raw return type 是 `ApiResponse`)。
`haveRawReturnType` 只看 raw type,泛型參數查不到。留給 review。

## `allowEmptyShould(true)` 的盲區:`package_landing_check.py`

生成的每條規則都帶 `allowEmptyShould(true)`(骨架階段 `domain/` 還是空的),而規則的
package 名是照規格宣告**寫死**的。兩件事接起來就是一個假綠燈:

    agent 只要把 class 放到別的 package,整套架構檢查就全部靜靜地不適用
    —— 不是紅、不是報錯,是**綠**,而且看起來跟「完全遵守架構規則」一模一樣。

風險是真的:凍結骨架用 `com.shop.domain` / `com.shop.usecase`,訪談那份 §10 用
`order/domain` / `order/application` / `order/adapter` —— **兩套本來就對不上**。

`package_landing_check.py` 補這一格:store 裡宣告過的每一個**自有** package,
`src_root` 底下必須至少有一個 class 的 `package` 宣告落在它(或它的子 package)裡。
判準刻意寫笨,而且**掃源碼樹不掃編譯產出** —— 編譯產出不在的時候,「掃不到 class」
跟「還沒 build」長得一模一樣,那正是它要抓的那種病的翻版。

離開碼跟這條線上其他報表對齊:`0` 全部有 class /`1` **有空的(不適用,不算通過)**/
`2` 用法錯誤 /`3` **整份不適用**(一條都沒宣告、`--root` 沒對上任何宣告、宣告全是萬用字元)。
`--root` 打錯一個字母會讓自有 package 全被歸成第三方 —— 那條路現在走 3,**不會翻綠**。
其餘上限印在報表尾巴,讀結論之前先看那一段。

## 第二個生成器:GWT → 可執行的驗收(第 3 階)

比第一個難的地方是**測試資料**:架構規則只有 package 名,情境有金額、數量、幣別、
期望值 —— 那些要變成 fixture。schema 因此擋得住散文擋不住的東西
(數量非正、金額為負、幣別不是三碼)。

**最值錢的是這一條**:`totalCents` 的期望值會被 import 拿 Σ(數量 × 單價) 重算一次。

```
S4.assertions[1]:totalCents 期望 5200,但各明細的「數量 × 單價」加總是 5100 —— 兩者不一致
```

散文寫「2 件 1500、3 件 700,總額 5100」,讀的人要自己心算才發現寫錯;
結構化之後那個乘加**變成可以被檢查的東西**。這就是訪談 prompt §7「內部矛盾」
想靠散文抓的**推導型矛盾**,搬到第 2 階。

### 驗收:兩側都要驗,不是「綠 ＋ 逐條可紅」

驗收測試跟 ArchUnit 不一樣 —— 它在**空骨架上必須是紅的**,所以「跑得綠」反而是壞消息。
`acceptance_gwt.py` 三段:

```
✅ 空骨架 → 5/5 紅                     不是恆真
✅ layered/OL1-integration → 5/5 綠    可滿足
✅ S2/S3/S4/S5 破壞 → 只有對應那條紅
✅ S1 破壞 → 全紅(見下)
```

**第二段特別值錢**:OL1 是輪 1 分層實驗寫的實作,對著**手寫的**那份凍結驗收跑綠,
而且從沒看過生成的這一版。生成版在它身上也全綠 ⇒ **兩份驗收在行為上等價**
—— 那比逐位元組比對 Java 有意義得多(格式、順序、命名都可以不同而行為相同)。

**S1 被其他情境蓋住**:S2–S5 都要先 `orderIdOf(...)` 才拿得到 id,而那個 helper
自己就斷言 201。所以破壞 201 會全紅,S1 沒有獨立的偵測力。
**這跟 A6 被 A1 蓋住是同一種現象** —— 第二次遇到,值得當成通則:
**一組檢查裡總有幾條是被別條蘊含的,而那件事只有靠「逐條破壞」才量得出來。**

## 假驗收偵測(第 3 階唯一沒人守的洞)

`acceptance_archunit.py` 治的是第 2 階的假綠燈(逐條可紅)。**第 3 階同樣的病沒人守**:
分層實驗量到過一次 —— HL1/HL2 的 no-setter 反射測試**恆真**(掃不到任何真 setter),
而 HL2 的 `reconstruct` 後門正好從 `set*` 字面檢查旁邊走過。測試是綠的,
而且**不管實作怎麼寫都會是綠的**。

`vacuous_tests.py` + `pitest.gradle` 補這格。**這裡有三個指標,兩個是錯的,而且都是實測掉的
—— 用分層實驗那條已知的恆真測試當已知陽性,錯的指標會在它身上回報「乾淨」。**

**兩個已知陽性**(都來自分層實驗,都是真的恆真測試):

| | 形狀 | 為什麼恆真 |
|---|---|---|
| **HL2** `OrderTest.testOrderNoSetters` | 靠 `@BeforeEach` 建 fixture | 掃 `getDeclaredMethods()` 找 `set*` 開頭;類別本來就沒有,所以永遠綠 |
| **HL1** `OrderTest.testNoSetters` | 測試內自己 `new Order(...)` | helper 寫 `getDeclaredMethod(name, Object.class)` —— **參數型別硬編 Object**,真的 setter(`setStatus(OrderStatus)`)永遠對不上,回傳恆為 false |

四個指標,三個被這兩個陽性淘汰:

| 指標 | HL2 | HL1 | 判 |
|---|---|---|---|
| PIT 原生 mutation score | 不受影響 | 不受影響 | ❌ 答非所問 —— 恆真測試不會拉低分數 |
| **殺了 0 個 mutant** | 它殺了 **7 個** → 回報乾淨 | — | ❌ 被共用 `@BeforeEach` 打敗:fixture 路徑上的 mutant 讓全班一起紅,恆真測試繼承它沒賺到的擊殺 |
| **獨佔擊殺 = 0** | 抓到,但標 33/47 | 抓到 | ❌ 健康的重疊把訊號淹掉 |
| **沒超出「全班共同集合」** | 抓到(標 3 條) | **漏抓** | ❌ 只對「共用 fixture」那種形狀有效;HL1 在測試內建構,交集不含它殺的 mutant |
| **被支配**(∃ 別條測試殺的是它的超集) | 抓到 | 抓到 | ✅ 兩種形狀都涵蓋,而且比獨佔=0 緊(20/47) |

> HL1 那次的漏抓**在跑之前就預測到了**,理由跟事後解釋一樣(共用 fixture vs 測試內建構)。
> 一個樣本證明不了偵測器 —— 這是第二個樣本才問得出來的。

### ⚠️ 它做不到的事(這句比上面整張表都重要)

**mutation testing 分不出「恆真測試」與「它守的東西 mutation 碰不到」。**
兩者在資料上長得一模一樣:沒有獨佔貢獻、只死在很多測試共用的 mutant 上。
實測:佇列排最前面的全是 **null 守衛與 hashCode 測試** —— 那些是**正當的測試**,
只是 PIT 表達不出它們守的東西,而恆真測試就夾在它們中間
(HL2 排第 8/47、HL1 排第 6/50)。

所以這支 script 交的是**分診佇列**,不是判決:把 47 條縮到 20 條要人讀,
兩個已知陽性都在裡面。判別要靠讀那條測試在斷言什麼 —— 那一步機械化不了。
**這本身就是一個階梯上的事實:假驗收目前最高只搬得到「第 2 階的分診 + 人判」。**

### mutator 選擇會改變答案

同一份 code,`DEFAULTS` 標 6 條、`STRONGER` 標 3 條。多出來的 3 條全是 `*NotBlank` 守衛測試
—— 它們**不是恆真**,是 `DEFAULTS` 表達不出它們守的東西:預設只有 `NegateConditionals`
(把守衛反過來 → 合法輸入也拋例外 → 全班一起紅),沒有「把守衛整條拿掉」。
`STRONGER` 含 `REMOVE_CONDITIONALS`,守衛測試因此賺得到獨佔擊殺。
**所以 `mutators = ['STRONGER']` 不是調參,是這個偵測器能不能用的前提。**

剩下的 3 條裡,2 條(`testDraftLabel` / `testPlacedLabel`)斷言的是**字串常數**,
而 PIT 的 DEFAULTS/STRONGER 都沒有字串 mutator —— 那是真的碰不到,列進 allowlist。
**扣掉那 2 條,偵測器精準指出唯一那條恆真測試。**

### allowlist 的理由是必填的

`--allow-file` 的每一行是 `Class.method  # 理由`,**少了 `#` 那一行會被拒收**。
一年後沒人記得為什麼某條測試被豁免,而沒有理由的豁免會慢慢長成「全部豁免」。
跟 schema 那邊 `provenance_ref NOT NULL` 是同一招。

## 已知缺口(不要當成已經接上)

1. **drift check 還沒綁進任何 build。** `examples/shop/app/build.gradle` 是凍結的,加不了
   `verifyGenerated` task。所以這條檢查目前是手動/hook 綁的 —— **綁法還住第 4 階**,
   檢查本體本身是第 2 階。要綁進 build 得等新骨架或解凍。
   （這正是那條鐵律的意思:檢查本體 runtime 無關,綁法各處不同。Gradle / CI /
   Claude Code Stop hook / Agent SDK / Managed Agents 的 Outcome 都是綁定層。）
2. **支援三種規則形狀,12 條規則裡 6 條住第 2 階。** 還在第 4 階的 6 條:
   A5/A9 標了「搬得上去,需要新的 kind」(allowed_top_level_packages /
   required_location);A7/A12 標了**搬不上去**(都是「必須存在什麼」,
   ArchUnit 只查得到「不該有的出現了」);A8 部分搬得上去;
   A11 已住第 1/2 階但靠凍結清單,不靠 ArchUnit。
3. **`architecture.yaml` 是轉寫,不是訪談產出。** 它把凍結的
   `examples/shop/spec/ARCHITECTURE.md` 逐條搬成結構化資料,所以每條來源都是
   `推導自 <該檔行號>`。真正跑第一、二幕時來源會是 `[Qn]` / `本案自決`。
4. **詞彙表 ↔ 實作命名(2↔3)完全沒有東西在看,而那是刻意擱著的。**
   `glossary_check.py` 只看**對外欄位名**(2↔4)。實作的類別 / 方法 / 變數名叫什麼,
   驗收永遠不會知道 —— 驗收**刻意不 import 任何實作類別**(為了讓兩份長得完全不同的
   實作能被同一套驗收判定)。唯一看得到類別名的是 ArchUnit,而現有三種 rule kind
   沒有一種是命名類的。**要不要開第四種是一個沒拍板的取捨**(票 08-B):
   這條線目前刻意只約束**邊界**,約束命名會吃掉「兩個模型都能被判定」買到的自由度
   —— 而那可能正是對的。**不要順手做掉。**
5. **假驗收偵測還沒綁進 build,而且只驗過一個樣本。** `pitest.gradle` 是待貼的樣板
   —— `examples/shop/app/build.gradle` 凍結中,貼不進去(跟 drift check 同一個處境)。
   已知陽性只有一個(HL2 的 `testOrderNoSetters`);其他分層樣本(HL1、OL1)還沒跑過。
   另外第 2 階的「逐條可紅」目前仍是**手寫的違反物**,那一半還沒自動化。
