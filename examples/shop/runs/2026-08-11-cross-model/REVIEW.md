# 跨模型實驗 · 兩軸 code review(2026-08-11)

方法:mattpocock-skills 的 `/code-review` 適配成 4 份實作 × 2 軸 = **8 個並行
subagent**(每個 reviewer 只看自己那份 diff + 該軸的判準文件,互不見彼此結論)。
Standards 軸判準 = `spec/ARCHITECTURE.md` + `spec/GLOSSARY.md` + Fowler smell
baseline;Spec 軸判準 = `spec/SPEC.md`。ArchUnit 已機械強制的相依方向一律不報。
兩軸刻意不合併、不互相重排。Reviewer 全部用 Opus 5,唯讀。

**先講這份 review 對實驗結論的修正**:輪 1 報告寫「第 4 階散文規則 4/4 守住」,
那是 **grep 探測深度**的結論。review 深度翻出了探測看不到的洞——最重的兩個都在
H2b:public 建構子直接收外部可變 List 與任意 total(= 事實上的 setter 後門),
以及 `recalculateTotal` 用 `cents()==0` 判首筆導致幣別檢查存在可跳過的分支。
O2(Opus)也有真 bug:`addItem` 先動集合再重算,跨幣別例外時明細已進、總額停舊值。
**「守住」要分層敘述:表面形狀(方法簽章層)4/4 守住;語義(不變式真的封閉)
O1 全守、O2/H1b/H2b 各有破口,嚴重度 H2b > H1b ≈ O2 > O1。**

## 總表

| | Standards 硬違規 | Standards judgement | Spec 缺漏 | Spec 越界 | Spec 可疑 | 最嚴重一項 |
|---|---|---|---|---|---|---|
| O1 | 2 | ~6 | 0 | 0(僅無用 surface) | 2(張力非違規) | 詞彙表外命名 `Line`/`Item` |
| O2 | 0(2 邊界) | ~6 | 0 | 2(ORDER BY、「草稿」) | 2 | **`addItem` 例外路徑破一致性** + INNER JOIN 掉單 |
| H1b | 5 | ~5 | 1(乘法繞過 Money) | 3 | 3 | **壞死碼 `findById` 會毀 `placedAt`** + 捏造 rationale |
| H2b | 4 | ~5 | 2 | 4 | 4 | **public 建構子 = total/items 後門** + 幣別檢查可跳過 |

品質梯度第一次看得見:**O1 > O2 > H1b > H2b**。
(驗收 + ArchUnit 全綠對四份一視同仁——這個梯度只有 review 才量得出來。)

## 跨四份的系統性發現

1. **驗收打不到的地方就是洞聚集的地方**。四份的所有實質問題(封裝後門、
   例外路徑不一致、掉單)全部在 HTTP 驗收的射程外。Opus 自加的單元測試
   蓋掉了一部分,但連 O2 自己的測試也沒蓋到自己的 `addItem` 破口。
2. **`Money` 沒有 multiply 是規格自己的缺口**:SPEC 說「金額運算一律走 Money」
   但只示範了加法;H1b 於是裸乘 `cents() * quantity`。**型別缺一個方法,
   規則就會被繞過**——第 1 階的修法是給 `Money.times(int)`,兩份 Opus 都自己補了。
3. **範圍外的死碼是 Haiku 的穩定特徵**:兩份 Haiku 都做了 `findById` + 整段
   反向重建(規格明列「查單筆訂單…不要做」),而且都是壞的
   (H1b 重建會把 `placedAt` 蓋成今天;H2b 靠 public 建構子後門)。
4. **顯示文字「已成立」四份都放錯或放兩份**:GLOSSARY 說它是「狀態的顯示文字」,
   四份全在 domain enum 帶了 label(O1 經 query 側 import 使用;其餘三份
   是死碼 + query 側另有一份硬編)。規格沉默處的一致性錯誤 = 規格的問題。
5. **ASSUMPTIONS 的品質也有梯度**:O1/O2 各 22/21 條、理由可查;
   H1b 有一條**捏造的技術 rationale**(#6「原生 SQL Query API 在單元測試中
   行為不一致」——並無此事);H2b 有一條自己發明的歧義(place() 回傳值)。
   agent 為決定編造理由,是獨立於 code 品質的一類 harness 風險。

## 各份詳情

### run-O1(Opus 5,`d396a36`)

**Standards** — 硬違規 2:(1) `PlaceOrderCommand.Line` 與 `PlaceOrderRequest.Item`
為同一概念另創兩個詞彙表外名字(GLOSSARY「不得另創同義詞」);(2) `Order.place()`
自加「無明細不得成立」前置條件,未記入 ASSUMPTIONS(PROMPT 要求逐條記錄)。
Judgement:`OrderEntity`/`OrderItemEmbeddable` 11 個 getter 全 repo 零呼叫、
`OrderStatus.DRAFT("草稿")` 死碼(Speculative Generality);空明細檢查在
usecase 與 domain 重複;三個 id record 逐字同形;`currency` 全線裸 String
(SPEC 只禁裸 long,非硬違規);`OrderStatus.label()` 讓 domain 帶呈現語彙。

**Spec** — 缺漏 0;「明確不在範圍內」**零違反**(四份中唯一,SQL 連 ORDER BY
都沒有)。可疑 2(皆 ASSUMPTIONS 自陳):「已成立」放 domain、query 側 import
enum 翻譯,與第 6 課讀寫分家有張力;訂單幣別隱含取自第一筆明細,混幣請求
對外呈現 500。另:`addItem` 先算後改,跨幣別失敗時訂單停在原一致狀態——
**比 SPEC 要求更嚴**。

### run-O2(Opus 5,`2ea8dd0`)

**Standards** — 硬違規 0;邊界 2:`Money.times(int multiplier)` 參數名未用
領域詞 `quantity`;`ORDER BY`(移交 Spec 軸)。Judgement:11 個 getter 零呼叫、
`currency` 欄位只寫不讀、`DRAFT -> "草稿"` 不可達分支(Speculative Generality);
`(productId, quantity, unitPriceCents, currency)` 四欄三處逐字重複(Data Clumps,
其中 usecase/adapter 那份是承重的);status 轉換散兩檔(Shotgun 輕)。

**Spec** — 越界 2:`ORDER BY o.placed_at, o.order_id`(ASSUMPTIONS #3 辯稱
決定性,理由成立但字面踩線);「草稿」自創顯示文字。可疑 2(**皆真 bug**):
(1) `addItem` 先 `items.add` 再 `recalculateTotal`,跨幣別例外時**明細已進、
total 停舊值**——直接違反「總額必須在同一個方法內重算」;(2) INNER JOIN
使不存在顧客的訂單 POST 回 201 卻**永不出現在列表**,違反情境 2;驗收只用
C-001/C-002 所以測不出。

### run-H1b(Haiku 4.5,`1841719`)

**Standards** — 硬違規 5:(1) `findById` + 整段重建邏輯屬「查單筆訂單」禁區,
全 repo 零呼叫,且重建走 `place()` 會把 `placedAt` 蓋成 `LocalDate.now()`
(**壞的死碼**,ASSUMPTIONS #5 自承);(2) `OrderItem.subtotal()` 裸乘
`unitPrice.cents() * quantity`(SPEC「不得把金額拆成裸的 long」;根因:
`Money` 沒 multiply);(3) `OrderStatus.label()` 顯示文字進 domain 且為死碼,
query 側另有硬編一份;(4) `ORDER BY o.id DESC`(排 UUID,語意也無意義);
(5) `ItemRequest` 詞彙表外命名。Judgement:status 以字串跨三檔硬編
(Primitive Obsession + Shotgun);三個 id 類逐字相同;`addItem` 與 `OrderItem`
建構子檢查同形重複;空單時 `total = null`(「明細與總額永遠一致」鬆脫);
`PlaceOrderResponse` setter/無參建構子無人用。

**Spec** — 半殘 1(裸乘繞過 Money);越界 3(ORDER BY、findById 死碼、
「草稿」label);可疑 3:壞死碼毀 `placedAt`;statusLabel 兩份真值來源且
生效的那份 fallback 會把 `"DRAFT"` 字串漏給前端;**ASSUMPTIONS #6 的技術
rationale 是捏造的**。

### run-H2b(Haiku 4.5,`2ff7e35`)

**Standards** — 硬違規 4:(1) **`Order` 六參數 public 建構子直接持有外部
mutable List、不做防禦複本、直接吃任意 total 不重算**——`JpaOrderRepository`
就傳了 mutable `ArrayList` 進去;items 後門 + 事實上的 total setter,
「無 setter」只在字面成立;(2) `ORDER BY … DESC NULLS LAST`;(3) `findById` +
`toOrder()` 整套反向對映零呼叫(禁區 + 死碼);(4) `OrderStatusEntity` 與
`OrderStatus` 逐字相同的同義詞複製(`@Enumerated(EnumType.STRING)` 可直接吃
domain enum)。Judgement:`toDomainEntity(Order)` **命名方向相反**(實為
domain→JPA);「已成立/草稿」兩份對映;`(cents, currency)` 三處成對旅行;
零元明細誤判首筆、撞上硬編的 `new Money(0,"TWD")`。

**Spec** — 缺漏 2(**最嚴重的兩個**):(1) 建構子後門,見上;(2)
`recalculateTotal` 用 `sum.cents() == 0` 判「第一筆」,首筆小計為 0 時
第二筆走取代分支,**幣別檢查被跳過**,且 `new Money(0,"TWD")` 硬編預設幣別。
越界 4(排序、findById、`displayLabel()`、出向 View Model 帶全套 setter
+「JSON 反序列化用」註解)。可疑:statusLabel 兩份真值來源;query 側硬編
欄位名耦合 Hibernate 命名策略;ASSUMPTIONS #3 是自己發明的歧義。

## 對輪 2 的輸入(三個證據源此刻收斂)

R8 探測、review 兩軸、與 Haiku 跨執行重現,三路指向同一批「沉默處」:

1. **`Money` 補 `times(int)` 進規格的介面要求**(第 1 階:讓裸乘沒有存在理由)。
2. **「領域規則每條配單元測試」進 PROMPT**(第 3 階)——O2 的 addItem 破口
   證明連 Opus 的自發測試都有涵蓋缺口,要求要指名到規則。
3. **命名規則進 GLOSSARY**(禁 `Impl` 後綴、類名反映實作技術、DTO 命名用
   詞彙表的詞)+ 可機械化的部分上 ArchUnit(第 2 階)。
4. **「明確不在範圍內」要機械化**:禁 `ORDER BY`、`OrderRepository` 介面
   凍結為 `save` only——四份中三份踩了範圍外,散文禁令對「多做」幾乎無力。
5. **顯示文字歸屬寫死**(「已成立」只准存在於 Query 側)——四份全錯的地方
   是規格的錯,不是 model 的錯。
