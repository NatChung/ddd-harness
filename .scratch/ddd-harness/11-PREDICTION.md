# 票 11 的預測(寫在寫程式之前,2026-08-18)

形狀由 `docs/adr/0006` §3 定死,這裡不重複論證形狀。這份只寫死一件事:
**這支檢查拿凍結骨架跑,會量到什麼數字**——包含哪幾格會被誤判成缺。

「檢查跑得起來」「宣告過的 package 數 > 0」不可能失敗,**不用**。
下面每一條都寫得出「什麼結果會讓它落空」。

## 它做什麼

`tools/harness/package_landing_check.py`。吃 `<src_root> <spec.yaml…>`
(跟 `verify_generated.py` 同一種入口:`load_specs` + `build_store` 到 tmp,
**不吃現成的 spec.db** —— repo 裡根本沒有 committed 的 db)。

從 store 的三張參數子表(`forbidden_dependency` / `forbidden_annotation` /
`forbidden_return_type`)撈出所有宣告過的 package 名,對 `src_root` 底下的 `.java`
掃一次,**每個宣告過的自有 package 必須至少含一個 class**。沒有的話報「**不適用**」
—— 自成一類、印在報表最上面、**不算通過**(ADR 0005 §6,ADR 0006 §1 沿用)。

## 動手前先查證過的事(不是預測,是事實)

- `examples/shop/app/src/main/java` 底下**只有** `Application.java`,`package com.shop;`。
- `architecture.yaml` 裡 `enforcement <> none` 的規則是 A1 / A2 / A3 / A4 / A6 / A10。
- 凍結的 `examples/shop/app/.../ArchitectureTest.java` 只有 4 條(A1–A4),
  `examples/shop/harness/generated/` 那份才是生成器產的。**這支吃 store,兩份 java 都不吃**
  —— 記在這裡只是免得日後看到 4 vs 6 以為是這支的 bug。

## 掃源碼樹,不掃編譯產出(決定,不是預測)

理由寫進模組 docstring:**編譯產出不在時,「掃不到 class」跟「還沒 build」長得一模一樣**
—— 那正是這張票要抓的那種病的翻版(不適用偽裝成乾淨)。源碼樹永遠在。
代價是它證不了「編得起來」,而 ArchUnit 讀的是 `.class`。**這條上限印進報表。**

package 取自檔案裡的 `package X;` **宣告**,不是目錄路徑 —— 宣告才是編譯器與 ArchUnit
認的那個。凍結骨架兩者一致,所以**這份語料分不出兩種做法**,用合成測試釘。

## 預測(逐條可落空)

### P1 去重後宣告過的 package = **7 個**,其中只有 **3 個**是本案自己的

三張子表的 package 欄位全撈出來去重:`com.shop.domain..` / `com.shop.usecase..` /
`com.shop.adapter..` / `org.springframework..` / `jakarta.persistence..` /
`jakarta.transaction..` / `com.fasterxml.jackson..`。

→ **7 個宣告,3 個自有 + 4 個第三方。**
→ 天真寫法「每個宣告過的 package 都必須有 class」會把那 4 個第三方判成缺,
  報表變成「7 缺 4」的噪音,而**噪音會讓真正的 3 個缺被讀者跳過去**。
落空條件:去重後不是 7,或第三方不是 4 個。

### P1b 推導出來的 root = **`com.shop`**,不是 `com`

`from` 欄的三個值取**點號分段**的共同前綴。字串前綴會在
`com.shop.domain` vs `com.shopping.x` 這種資料上給出 `com.shop` 這個假 root
—— 本語料驗不到,合成測試釘。

→ 落空條件:推導出 `com` 或 `com.shop.`(帶尾點)或空字串。

### P2 拿凍結骨架跑,3 個自有 package **全部**是空的,**M = 3**

`Application.java` 的 `com.shop` **不屬於** `com.shop.domain..`
(`com.shop` 不是 `com.shop.domain` 的子孫)。

→ **M = 3。不是 0、不是 2。**
落空條件:M ≠ 3。特別是 **M = 0 表示我把比對寫成了無邊界的字串前綴**
(`com.shop` 被 `com.shop.domain..` 誤配)—— 那個錯的方向是**假通過**。

### P2b 那 1 個 class 會落在「**宣告外**」那一段:`com.shop`,1 個

→ 報表的「有 class 但沒有任何規則宣告」那段 = 恰好 1 個 package(`com.shop`)、1 個 class。
落空條件:那段是空的(表示我沒把 Application 掃到)或多於 1 個。

### P3 6 條規則裡,**from 側落在空 package 的 = 6/6** —— 整套架構檢查一條都沒在跑

A1/A3/A6 的 from 是 `com.shop.domain..`,A2/A4 是 `com.shop.usecase..`,
A10 是 `com.shop.adapter..`。三個全空 → **6 條全部整條不適用**。
配上 `allowEmptyShould(true)`,它們**必然綠**,而且綠得跟「完全遵守架構規則」一樣。

→ 落空條件:store 裡 `enforcement <> none` 的規則不是 6 條,
  或有任何一條的 from 側不在那 3 個空 package 裡。

⚠️ from 側空 = **整條不適用**;to / annotation / return 側空 = 規則還在跑,
只是那個禁止目標不存在。**兩者都算缺(判定照票的字面:宣告過就要有 class)**,
但報表要分開解釋 —— 不分開的話讀者會以為 A3 的兩半一樣嚴重。

### P4 破壞式:在 `com/shop/domain/` 放一個 class → **M 3→2、A1/A3/A6 三條從不適用變適用**

先斷言「破壞本身被看見」(掃描器報 `com.shop.domain` 非空),再斷言數字。
上一輪在這裡假通過過一次,所以這順序是硬性的。

→ 落空條件:M 不是掉到 2,或翻面的不是恰好 A1/A3/A6 這 3 條。

### P5 **本票的攻擊情境**:class 放到 `order.domain` → **M 仍然是 3**,而那個 package 出現在「宣告外」

這就是這張票存在的理由(ADR 0006 §3:訪談那份 §10 用 `order/domain`,凍結骨架用
`com.shop.domain`,**兩套本來就對不上**)。

→ 落空條件:M 掉到 2 或更少(表示我的比對太鬆,`order.domain` 被算進
  `com.shop.domain..`),或「宣告外」那段沒有 `order.domain`。

### P6 離開碼:凍結骨架 = **1**;一條 package 都沒宣告的 store = **3**

- `0` 全部自有宣告 package 都有 class
- `1` **有空的 → 不適用,不算通過**(這是凍結骨架的值)
- `2` 用法錯 / 吃錯目錄(`landing_check` 的「吃錯目錄要當場掛」先例)
- `3` store 一條 package 都沒宣告 → **檢查本身不適用**(照 `contract_triage` 的 3)

→ 落空條件:凍結骨架回 0。**「不適用」絕不回 0。**

⚠️ 目錄存在但**零個 `.java`** 不是用法錯,是合法的空骨架 → M = 全部、exit 1,不是 exit 2。

## 已知上限(要印進報表,不是只寫在票裡)

1. **它只看「package 裡有沒有 class」,不看那些 class 對不對。**
   在 `com.shop.domain` 放一個空的 `Placeholder.java` 就能讓這支全綠 ——
   它證明的是**落點存在**,不證明那裡的東西是領域模型。
   (跟 ADR 0006 §5 對內圈落點檢查那條上限逐字同型:形式滿足得了。)
2. **掃源碼樹,不掃編譯產出** —— 證不了編得起來,而 ArchUnit 讀的是 `.class`。
   一個語法錯的檔案在這支眼裡照樣算「有 class」。
3. **比對規則是機械的、大小寫敏感的**:`com.shop.domain..` 去掉尾巴 `..` 之後,
   `pkg == base` 或 `pkg.startswith(base + '.')` 才算。
   `com.shop` **不算**在 `com.shop.domain..` 裡;`com.shop.Domain` 也**不算**
   (Java package 大小寫敏感)。`com.shop.domainhelper` 不算。
4. **含萬用字元的 pattern(`*`)比不了** —— 自成一類丟進「不適用」,**絕不當通過**。
   今天的 CHECK 只逼 `%..`,寫得出 `com.*.domain..`。
5. **排除清單(第三方 package)是這支最大的假通過來源。**
   root 推導錯 → 某個自有 package 被歸成第三方 → 它空著也不會被報。
   所以報表**逐個印出被排除的 package**,並要人看過。
6. **「宣告外的 package」只印,不進判定。** 把 class 放到別的 package 不是這條的違規
   (票的字面是「宣告過的要有」),但它是**最常見的成因**,所以印在旁邊。

## 驗收(綠 + 逐條可紅)

- [ ] 凍結骨架:7 宣告 / 3 自有 / M=3 / 6 條全不適用 / exit 1
- [ ] 「宣告外」印出 `com.shop`(1 個 class)
- [ ] 破壞式:先印 `mutated ok`(斷言掃描器看見了),再驗 M 3→2、A1/A3/A6 翻面
- [ ] 攻擊情境:`order.domain` → M 仍 3,`order.domain` 進「宣告外」
- [ ] `com.shop` 不得滿足 `com.shop.domain..`(合成,錯的方向是假通過)
- [ ] 單一 from_package 時 root 推導的洞(合成)
- [ ] 【不適用】印在最上面、明講「不是通過」、上限印在報表裡
- [ ] 吃錯目錄當場掛(exit 2);空目錄不是掛,是 M=全部 / exit 1
- [ ] `python3 -m pytest tools/harness -q` 全綠(基線 **161 passed**)
