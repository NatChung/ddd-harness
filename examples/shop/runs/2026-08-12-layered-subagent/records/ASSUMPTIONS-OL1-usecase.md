# ASSUMPTIONS —— usecase 層實作時自行決定的事

規格(`spec/SPEC.md`、`GLOSSARY.md`、`ARCHITECTURE.md`)沒有講死、而實作必須有個
答案的地方,逐條記在這裡。決定者:usecase 層實作 agent。範圍僅限
`com/shop/usecase/`(以及它對 adapter 層的期待)。

## A1. 訂單識別由 `OrderRepository.nextOrderId()` 發放

規格說 `POST /orders` 要回 `orderId`,但沒說誰產生。決定:放在 Command 側的
`OrderRepository` 上(DDD 的 next-identity),不另開一個 `OrderIdGenerator` port。

- 理由一:`ARCHITECTURE.md` 把 usecase 層的內容列得很死(兩個 use case、兩個介面、
  一個 View Model),多開一個頂層 port 就偏離那份清單。
- 理由二:身分由儲存側發放,use case 拿到識別之後才 `Order.create(...)`,
  因此不存在「還沒有 id 的 Order」這種中間狀態。
- 理由三:測試裡由假的 repository 發序號(`O-1`、`O-2`),下單流程完全可預期。
- 對 adapter 的影響:實作一行即可,例如
  `OrderId.of(UUID.randomUUID().toString())`。

## A2. 成立日期用可注入的 `java.time.Clock`

`Order.place(LocalDate)` 要一個日期,規格沒說時區也沒說怎麼取。決定:
`PlaceOrderUseCase` 建構子吃 `Clock`,並提供一個只吃 repository 的便利建構子
(內部用 `Clock.systemDefaultZone()`)。`Clock` 是 JDK 型別,不違反「usecase 不
依賴框架」。adapter 不必特地準備 `Clock` bean;測試用 `Clock.fixed(...)`。

## A3. 沒有顧客存在性檢查

情境 1 的「Given 一位存在的顧客」是前置條件,不是要 use case 去驗。系統裡沒有
Customer Aggregate,也沒有查顧客的 port(`GLOSSARY.md` 只給了兩個介面),
所以下單**不查** `customers` 表、不驗 `customerId` 是否存在;只驗它非空白
(由 `CustomerId` 這個 Value Object 自己守)。查不到姓名是 Query 側的事。

## A4. 空明細的下單直接讓領域層丟例外

規格沒有定義「items 是空陣列」要回什麼。決定:不在 use case 加防呆,
讓 `Order.place()` 丟 `IllegalStateException`(「沒有明細的訂單不得成立」)往外傳。
理由:與規格對 `addItem` 的態度一致——這類是**呼叫方的 bug,不是業務例外**;
要翻成什麼 HTTP 狀態碼是 adapter 層的事,usecase 不預先決定。同理,幣別不一致
、數量非正也一律讓 `Money` / `OrderItem` 丟出來,use case 不攔不吞。
(已由測試釘住:例外往外傳,而且**什麼都沒存下**。)

## A5. `PlaceOrderUseCase` 的輸入是巢狀 record `Command` / `Item`

`ARCHITECTURE.md` 列出的 usecase 層內容裡沒有「輸入 DTO」。決定:把輸入定義成
`PlaceOrderUseCase.Command` 與 `PlaceOrderUseCase.Item` 兩個**巢狀** record,
讓頂層類別清單剛好等於架構文件列的那五個。輸入用「外面的形狀」(String / long),
把它翻成領域型別是 use case 的工作,不是 controller 的工作。

## A6. 下單回傳 `OrderId`(領域 Value Object),不是裸字串

`PlaceOrderUseCase.placeOrder(...)` 回傳 `OrderId`。`ARCHITECTURE.md` 只禁止
**controller 往 HTTP 回應**丟領域型別,沒有禁止 use case 對 adapter 回傳領域型別。
- 對 adapter 的影響:回應物件請自己組,取值用 `orderId.value()`。
  **不要**把 `OrderId` 直接交給 Jackson 序列化——record 會被序列化成
  `{"value":"…"}`,與規格要的 `{"orderId":"…"}` 不合。

## A7. `OrderListItem` 的欄位型別:字串 + 原始型別 + `LocalDate`

規格只給了 JSON 形狀。決定:
- `orderId` 用 `String`(不是 `OrderId`)、`totalCents` 用 `long`(不是 `Money`)。
  這是**往外傳的形狀**,鍵值要與規格的 JSON 逐字一致;用領域 Value Object 會讓
  序列化結果多一層(`{"value":…}`),也會逼外層認識領域型別。
  幣別不在列表頁的形狀內,所以這裡沒有幣別欄位——這是規格的選擇,照抄。
- `placedAt` 用 `LocalDate`。**對 adapter 的期待:序列化成 ISO 日期字串
  `YYYY-MM-DD`**(Spring Boot 預設的 Jackson JSR-310 設定即為此形狀,不要關掉)。

## A8. 狀態顯示文字的對映放在 usecase 層,`DRAFT` 顯示為「草稿」

`GLOSSARY.md` 只定義了 `PLACED` → 「已成立」。決定:
- 對映放在 `OrderListItem.statusLabelOf(OrderStatus)` / `OrderListItem.of(...)`,
  由 usecase 層擁有——領域的 `OrderStatus` 自己說了顯示文字不歸它管,而 adapter
  也不該自己編字串。Query 側實作手上若是狀態值,走 `OrderListItem.of(...)`。
- `DRAFT` 補上「草稿」(取自 `GLOSSARY.md` 對 `DRAFT` 的括號註解)。目前的下單流程
  是「建立 → 加明細 → 成立 → 存檔」一氣呵成,不會存下草稿,所以這個標籤實際上
  出不了現;但工廠方法必須對每個列舉值有定義,選「補字串」而不是「丟例外」。

## A9. `OrderListUseCase` 是一層很薄的轉手

`ARCHITECTURE.md` 要求 `OrderQueryRepository` 直接組出 `OrderListItem`,所以這個
use case 幾乎沒有邏輯(只做 `List.copyOf` 回唯讀複本)。它仍然存在,因為入口的
形狀要對稱:controller 對 Command 與 Query 都只認識 use case,不會有一條路徑
繞過 use case 直接抓 repository。排序與分頁明確不在範圍內,所以不做。

## A10. usecase 層不帶任何 annotation,由 adapter 層負責接線

usecase 不得 import 框架,所以 `PlaceOrderUseCase` / `OrderListUseCase` 上**沒有**
`@Service`、`@Component`,component scan 掃不到它們。
**對 adapter 的期待**:在 adapter 層自己的 `@Configuration` 裡用 `@Bean` 明確
建構這兩個 use case(傳入 adapter 的 repository 實作)。這是相依性倒轉的代價,
也是它的重點——接線知識屬於最外層。

## A11. 交易邊界不在 usecase 層表達

`@Transactional` 是框架,usecase 不得 import。下單流程對儲存只有一次 `save(order)`
的呼叫,原子性由 adapter 層的實作負責(單次 save 天然是一個工作單元)。
usecase 不宣告交易語意,也不假設有交易。
