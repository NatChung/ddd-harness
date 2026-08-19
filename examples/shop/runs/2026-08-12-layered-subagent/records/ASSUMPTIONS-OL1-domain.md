# ASSUMPTIONS(領域層)

規格沒有明說、但實作非決定不可的地方。每條記:**遇到什麼歧義 → 選了什麼 → 為什麼**。
層級只限 `com.shop.domain`;跨層的需求走 `INTERFACE-REQUESTS.md`。

## 1. `Money` 的數值單位是「分」的整數

- **歧義**:GLOSSARY 只說「金額 = 數值 + 幣別」,沒說數值型別。
- **決定**:`long amountCents`,不用 `BigDecimal`、不用浮點數。
- **理由**:SPEC 的 request/response 一律是 `unitPriceCents` / `totalCents` 整數分。
  領域內用同一種單位,邊界上就不必做精度轉換,也避開浮點數加總誤差。

## 2. 幣別型別用 `String`,不用 `java.util.Currency`

- **歧義**:幣別(`TWD`)沒指定型別。
- **決定**:`String currency`,只檢查非 null / 非空白,不檢查是不是 ISO 4217 有效代碼。
- **理由**:規格只要求「不同幣別不能相加」,那條規則靠相等比較就成立。
  驗證代碼合法性屬於輸入驗證,而 SPEC「明確不在範圍內」已排除驗證框架。

## 3. `Money` 不允許負數金額

- **歧義**:沒說金額可否為負。
- **決定**:建構時 `amountCents < 0` 丟 `IllegalArgumentException`;`multiply` 的倍數為負也丟。
- **理由**:本規格的金額只有單價與總額兩種用途,兩者都不可能為負。
  沒有退款 / 折扣情境(不在範圍內),所以窄的不變量比寬的安全。

## 4. 空訂單的 `total()` 丟例外,而不是回傳零

- **歧義**:沒有明細時總額是多少?
- **決定**:`total()` 丟 `IllegalStateException`。
- **理由**:`Money` 一定要有幣別,而沒有任何明細時**幣別是未知的** —— 回
  `Money.zero("TWD")` 等於憑空捏造一個幣別。與其猜,不如讓「談總額」這件事在
  沒有明細時就不合法。實務上訂單一定先有明細才會被問總額。

## 5. 一筆訂單只能有單一幣別

- **歧義**:SPEC 只說「不同幣別不能相加」,沒直接說訂單能不能混幣別。
- **決定**:混幣別的 `addItem` 會丟 `IllegalArgumentException`(是總額重算時
  `Money.add` 丟出來的,不是另外加的檢查)。
- **理由**:「明細與總額永遠一致」+「不同幣別不能相加」兩條合起來,單一幣別是
  邏輯結果而不是新規則。刻意讓它從既有規則長出來,不另立檢查。

## 6. 幣別不合時 `Order` 維持原狀(操作具原子性)

- **歧義**:`addItem` 失敗時 Aggregate 的狀態沒有規定。
- **決定**:先算出新總額、成功之後才動明細集合與總額(`Order.appendItem`),
  所以丟例外時明細數與總額都跟呼叫前一樣。
- **理由**:「明細與總額永遠一致」是**不變量**,不變量在例外路徑上一樣要成立。
  若先 `items.add()` 再算總額,例外會留下一個明細已加、總額沒跟上的破碎 Aggregate。

## 7. 數量必須 > 0

- **歧義**:沒說數量下界。
- **決定**:`OrderItem` 建構時 `quantity <= 0` 丟 `IllegalArgumentException`。
- **理由**:數量 0 的明細對總額無貢獻卻佔一列,是無意義狀態;負數量等於變相退貨,
  不在範圍內。擋在 `OrderItem` 而不是 `Order`,讓明細自己守自己的不變量。

## 8. 識別(`OrderId` / `CustomerId` / `ProductId`)包一層,值為非空白字串

- **歧義**:SPEC 的 JSON 用裸字串(`"C-001"`),沒說領域內要不要包型別。
- **決定**:三個各自是 `record`,值不得 null 或空白;三者互不相容(型別不同即不相等)。
- **理由**:GLOSSARY 明列它們是 Value Object 且「以值相等比較」。包型別後,把
  `ProductId` 傳進 `CustomerId` 的位置會編譯不過 —— 這是裸 `String` 給不了的。

## 9. `OrderId` 由外部給,領域不自己生

- **歧義**:沒說 `orderId` 誰產生。
- **決定**:`Order.create(OrderId, CustomerId)` 要求呼叫端帶 `OrderId` 進來。
- **理由**:產生識別要嘛靠 UUID、要嘛靠資料庫序號,兩者都是外層的決定。
  領域層不猜策略,只要求「給我一個合法的識別」。

## 10. `placedAt` 由呼叫端傳入,領域層不讀時鐘

- **歧義**:成立日期怎麼來?SPEC 只說列表要顯示 ISO 日期。
- **決定**:`place(LocalDate placedAt)` 由參數注入;領域層不呼叫 `LocalDate.now()`。
- **理由**:讀時鐘是對外部世界的相依,會讓領域規則不可重現地測。把「現在幾號」
  留給外層決定,`Order` 只負責「成立時要記下日期」。用 `LocalDate` 而非
  `Instant`,因為 SPEC 的 `placedAt` 形狀就是 `YYYY-MM-DD`。

## 11. 成立(`place`)要求至少一條明細

- **歧義**:SPEC 沒說空訂單能不能成立。
- **決定**:沒有明細時 `place()` 丟 `IllegalStateException`。
- **理由**:已成立的訂單一定會被列表頁問 `totalCents`(情境 4),而空訂單沒有總額
  可談(見第 4 條)。允許空訂單成立會直接造出一個問不出總額的已成立訂單。

## 12. 重複 `place()` 丟 `IllegalStateException`

- **歧義**:SPEC 只規定 `addItem` 在非 DRAFT 時的行為,沒規定重複 `place`。
- **決定**:比照 `addItem`,非 DRAFT 時 `place()` 丟 `IllegalStateException`。
- **理由**:同一個判準 —— 這是呼叫方的 bug,不是業務例外。兩個方法用同一種
  例外語意,呼叫端不必記兩套規則。

## 13. 多了一個 `Order.reconstitute(...)` 給持久化層還原用

- **歧義**:SPEC 要求 adapter 層自建持久化模型並負責對映,但沒說領域層要開什麼
  還原入口。只靠 `create` + `addItem` 無法還原一筆已成立的訂單(`addItem` 會擋)。
- **決定**:提供 `reconstitute(OrderId, CustomerId, OrderStatus, LocalDate, List<OrderItem>)`,
  且**刻意不收總額參數** —— 總額一律由明細重算。
- **理由**:一致性不外包給持久化層。若還原時接受一個存下來的總額,資料庫裡任何一筆
  壞資料都會變成一個明細與總額不一致的 Aggregate,「一致性由 Order 自己維護」就破了。
  還原時一樣檢查狀態與 `placedAt` / 明細相不相符,不讓壞資料進到記憶體。

## 14. `PLACED` 的顯示文字「已成立」不放在 `OrderStatus`

- **歧義**:GLOSSARY 同時定義了 `PLACED` 與顯示文字「已成立」(`statusLabel`)。
- **決定**:`OrderStatus` 只有 `DRAFT` / `PLACED` 兩個值,沒有 `label()` 方法。
- **理由**:ARCHITECTURE 說 `statusLabel` 是 `OrderListItem`(usecase 層 View Model)
  的欄位,走 Query 側。顯示文字是給人看的呈現,不是領域概念;放進領域層等於讓
  內層知道外層要怎麼顯示。

## 15. `Order` 的相等以 `OrderId` 判定

- **歧義**:GLOSSARY 說 Value Object「以值相等比較」,但沒說 Aggregate Root 怎麼比。
- **決定**:`Order.equals` / `hashCode` 只看 `orderId`;`OrderItem` 等 VO 則是全欄位相等。
- **理由**:Entity 的身分不隨欄位變動而改變 —— 同一筆訂單加了明細之後還是同一筆。
  這正是 Entity 與 Value Object 的分野,GLOSSARY 把兩者分開列就是這個意思。

## 16. `OrderItem` 做成不可變的 `record`

- **歧義**:GLOSSARY 說明細「只能經由 `Order` 修改」,沒說怎麼落實。
- **決定**:`OrderItem` 是不可變的 `record`,連 `Order` 自己也不改它,只增減集合成員。
- **理由**:「只能經由 Order 修改」用「根本不能改」達成最省事 —— 加上
  `items()` 回傳 `List.copyOf`,呼叫端既換不掉集合、也改不動裡面的元素,
  不必靠約定或防禦式拷貝每個元素。
