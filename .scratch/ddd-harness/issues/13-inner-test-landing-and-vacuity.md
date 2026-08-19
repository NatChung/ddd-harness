# 13 — 內圈測試的落點檢查 + 恆真分診

**What to build:** 兩支報表。**兩個都不是判決。**

**Blocked by:** 票 10(要先有骨架跑得出內圈測試);內圈測試的位置由票 12 定

**Status:** **needs-triage**(2026-08-19 從 blocked 改)—— **blocked 的前提已滿足**(`runs/2026-08-19-act4/` 有 9 條真內圈測試 + **兩個已知陽性**),但**形狀變了**:多了第三類病(**範圍不足** —— 落點檢查與恆真分診都抓不到),落點檢查要多印「打在哪個入口」。⚠️ **先定形狀再開工**,見檔末。

## 主:落點檢查

**每條契約要指得出至少一條內圈測試。** 這是今天已經做過兩次的同一個形狀
(票 05 答案落點、票 06 契約指名測試),差別是這次落點在**內圈**。
它只問「有沒有」,不判斷好不好 —— 所以不會犯「懲罰寫得好的那一方」那個病
(票 03 / 票 08 的假陽性家族)。

它也讓 2026-08-18 量到的 `enforcement = none 20/20` 第一次有機會動起來。

⚠️ **上限(要印進報表,不是只寫在票裡)**:內圈測試靠**方法名帶契約編號**指認自己,
而那是一條約定 —— 隨便一條測試取名 `C1_xxx` 就通過。
**它只證明落點存在,不證明那條測試真的在驗 C1。**

## 副:恆真分診

對內圈跑一次 `vacuous_tests`,印分診佇列。它**分不出「恆真」與「碰不到」**,
所以是佇列不是判決。

已知陽性參考:分層實驗 HL1/HL2 的 `no-setter` 反射測試 —— 掃不到任何真 setter,
**不管實作怎麼寫都會綠**。

## 不做

**PIT 守內圈** —— 票 09 已判定撐不起來,理由是 `vacuous_tests` 交的是佇列不是判決。

⚠️ 先寫預測。票 09 給的可落空寫法:**預測 agent 產出的內圈測試裡,拿 `vacuous_tests`
掃會有 ≥1 條進分診佇列** —— 或反過來預測一條都沒有,然後去看它是真的乾淨,
還是偵測器又失效了。

---

## 2026-08-19 · 兩個已知陽性(第四幕跑通後,架構 review 抓到)

本票原本沒有已知陽性,只有「內圈測試預設就該假設有恆真成分」這個推論。
現在有兩個實例,**而且兩個都是 TDD 產出的測試沒抓到 TDD 產出的 bug**。
語料:`examples/shop/harness/runs/2026-08-19-act4/`(9 條內圈測試,覆蓋 8 條契約)。

### 陽性一:守 C8 的測試用 `!isStatic` 過濾,看不見 `Order.restore`

`Order` 有兩個 static 工廠,只有一個守不變式:

```java
// Order.java:38-41   place —— 有守
if (items == null || items.isEmpty()) throw new DomainRuleViolation("EMPTY_ORDER", …);
// Order.java:45-52   restore —— 沒有,直接進 private constructor
public static Order restore(…) { return new Order(…); }
```

而守 C8「訂單成立後只允許改狀態」的那支測試這樣列舉入口:

```java
// innerTest/…/OrderImmutabilityTest.java:47-48
boolean isInstanceApi = Modifier.isPublic(method.getModifiers())
        && !Modifier.isStatic(method.getModifiers());
```

**`restore` 是 static,被濾掉。** 一支宣稱「訂單身上沒有第二個改得動它的東西」的測試,
**看不見那條能憑空造出任意狀態訂單的路**。唯一呼叫者是 persistence adapter
(`JpaOrderRepository.java:62`)—— 資料庫裡的壞資料讀回來不會叫。

⚠️ **這條對本票的意義**:落點檢查(主)會說「C8 有內圈測試 ✅」——**而它是對的,也是沒用的**。
落點存在,但那條測試的**列舉範圍**漏掉了半個 interface。**落點檢查抓不到這個,恆真分診也抓不到**
(它不是恆真,它是**範圍不足**)。這是第三種病,本票原本只列了兩種。

### 陽性二:`changeStatusTo(null)` 讓狀態變成 null,而三條非法轉移都沒試 null

```java
// OrderStatus.java:22   終點回 null
case RECEIVED -> null;
// Order.java:83         守衛用 != 比對它
if (target != status.next()) throw new DomainRuleViolation("INVALID_STATUS_TRANSITION", …);
```

一張 `RECEIVED` 的訂單:`status.next()` 是 `null`,`changeStatusTo(null)` →
`null != null` → **false** → 不丟例外 → **`this.status = null`**。

C9(單向前進)與 C17(被拒時原地不動)宣稱擋的正是這個。
而 `OrderStatusTransitionTest.java:44-52` 的三條非法轉移**都沒有試 `null`**。

⚠️ **這條正是本票「逐條可紅」該抓的**:把 `Order.java:83` 的守衛整條刪掉,
那三條非法轉移測試**會不會紅?** 會 —— 所以 mutation 抓得到守衛消失。
但把 `RECEIVED -> null` 改成 `RECEIVED -> RECEIVED`,**九條內圈測試一條都不會紅**,
而那個改動會讓「收到」的訂單可以重複被設成「收到」。**這種 mutant 現在活得下來。**

## 對本票設計的三個修正

1. **落點檢查(主)要多印一欄:那條測試「打在哪個入口」。** 只證明「C8 有測試」不夠 ——
   陽性一的測試存在、命名正確、而且**綠**。⚠️ 這一欄多半只能靠人讀,
   **那就誠實印成第 4 階**,不要假裝機械查得到。
2. **恆真分診(副)分不出「範圍不足」。** `vacuous_tests` 找的是「不管實作怎麼寫都會綠」,
   而陽性一的測試**會因為實作改變而變紅**(加一個 public 實例 mutator 就紅),
   它只是**看不到 static 那一半**。**這是第三類,要在報表裡跟前兩類分開。**
3. **「逐條可紅」延伸到內圈,現在有具體的 mutant 可用**:
   - 刪掉 `Order.java:83` 的守衛 → 預期三條轉移測試紅(**若不紅,那三條是白綠的**)
   - `RECEIVED -> null` 改成 `RECEIVED -> RECEIVED` → **預期一條都不紅**(已知漏)
   - 拿掉 `place` 的 `EMPTY_ORDER` 檢查 → 預期 `OrderItemsRequiredTest` 紅
   - `Money.java:32` 的 `currency != null &&` 拿掉 → **預期一條都不紅**(`MoneyTest` 沒打 null)

   **前兩個一紅一不紅,正好是「偵測器有沒有用」的最小對照組。**

## Blocked 狀態更新

本票原本 blocked 在「要先有骨架跑通、有真的內圈測試」。**那個前提 2026-08-19 已經滿足**
(`runs/2026-08-19-act4/` 有 9 條真的內圈測試,而且有兩個已知陽性)。
⚠️ 但**不要直接改 Status** —— 本票的形狀因為上面三條修正而變了(多了第三類病、
落點檢查要多一欄),**那個形狀要先定**,跟票 15 / 02 那組同一個道理。
