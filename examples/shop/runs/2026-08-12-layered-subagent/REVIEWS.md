# 兩軸 review 彙整(6 個 Opus reviewer,互不見彼此;完整輸出在 session,此為逐條保真摘錄)

路徑省略共同前綴 `app/src/main/java/com/shop/`(測試路徑註明)。

## OL1(Opus-layered)

**Standards 軸**:🔴 無。
- 🟠 死碼叢集:`domain/Order.reconstitute` + `adapter/OrderEntity`/`OrderItemEmbeddable` 9 個 accessor + `Money.zero`,production 零呼叫者(讀取走 JDBC 直查,永不讀回 Aggregate);reconstitute 會重算總額驗前置,**非封裝破口**,問題是為不存在需求撐大的公開面
- 🟠 總額規則 Java/SQL 雙實作(`JdbcOrderQueryRepository:41` SUM vs `Order.appendItem`),無測試綁定兩者
- 🟡 `COALESCE(c.name, o.customer_id)` fallback 語義自創;🟡 不可達 null 檢查;🟡 重複防禦複本;🟡 DRAFT 顯示文字生產不可達;🟡 request/Command 明細 record 重複
- 最嚴重:reconstitute 死碼叢集(「多出來的正確程式碼仍是要維護的程式碼」)

**Spec 軸**:缺漏 **零**(六條領域規則逐條對照全到位,含:appendItem 先算後改、例外路徑 Order 不變、no-setter 有反射測試真的掃 getMethods)。
- 越界(輕):COALESCE fallback;Money 自加禁負數;空訂單 total() 丟例外;LABEL_DRAFT 不可達;reconstitute/Money.zero 無呼叫者
- 可疑:總額雙實作(最嚴重項——「唯一會隨時間惡化的東西」);`rs.getDate().toLocalDate()` 時區相依;SQL 跨幣別安全靠註解
- 特別檢查:原子性成立(三路徑);LEFT JOIN×2 不掉單;placedAt 不被讀取破壞

## HL1(Haiku-layered #1)

**Standards 軸**:🔴 無。
- 🟠 `test/domain/OrderTest.hasSetterMethod` 用 `getDeclaredMethod(name, Object.class)` ——**恆真測試**,真 setter 也抓不到,no-setter 規則零守衛
- 🟠 `place()` 不檢查空明細 → 可達「PLACED 但 total() 即炸」狀態,守衛落在 usecase 層
- 🟠 讀寫兩側裸字串 "PLACED" 對接;🟠 Query 側 repository `extends JpaRepository`(把寫入能力注進讀取路徑);🟠 `IllegalStateException`→409(SPEC 明說那是呼叫方 bug 非業務例外)
- 🟡 ×11:OrderEntity.getItems 洩漏可變集合(死碼)、COALESCE(SUM,0) 與 total() 行為不一致、三層驗證重複、幣別雙檢查、三份 byte-identical VO 測試、`LocalDate.now()` 無 Clock 接縫、items null → NPE 500、**INNER JOIN customers**(→Spec 軸主洞)、"草稿"不可達分支等
- 最嚴重:恆真 no-setter 測試(「保護網看起來在、實際不在」)

**Spec 軸**:
- 缺漏:**`OrderListQueryJpaRepository:25` INNER JOIN customers + 下單不驗顧客 → 未知 customerId 回 201 但列表永不出現(靜默掉單,最嚴重項)**;恆真 no-setter 測試(測試層缺漏)
- 越界:**`ORDER BY o.order_id`(SPEC 不在範圍明列排序「不要做」;且按隨機 UUID 排序無意義)**;"草稿" 顯示文字自創(不可達)
- 可疑:Order.total() 在生產路徑是死碼(對外總額全由 SQL 算);controller items 缺失 NPE→500
- 特別檢查:失敗路徑原子性成立(驗證全在 save 前,save 單一交易 cascade);placedAt 不被讀取破壞;無明細不掉單(LEFT JOIN order_items 正確)

## HL2(Haiku-layered #2)

**Standards 軸**:
- **🔴 `domain/Order.java:104-108` addItem 先 `items.add` 後 `recalculateTotal`,跨幣別例外時明細已進、總額停舊值——Aggregate 在例外路徑自毀一致性(= 輪 1 O2 同型,最嚴重項)**
- **🔴 `domain/Order.java:50-67` `public static reconstruct(...)` 收任意 items/total/status 零複驗——可造出「明細 3000、總額 0 的 PLACED 訂單」;production 零呼叫者、`OrderItem` package-private 令 adapter 根本用不了它(= H2b 後門同型,以投機通用性形式再現)**
- 🟠 顯示文字下沉 domain enum(三處重複、兩處死碼);🟠 placedAt 由 save 當下 `LocalDate.now()` 決定、re-save 會重寫+重建明細(orphanRemoval);🟠 OrderRepository 摻 generateOrderId 職責
- 🟡 ×12:Jpa 命名不符實作(實為 JdbcTemplate)、toDomainEntity 方向反、subtotal 裸 long 乘法(Money 無 multiply,溢位無護)、空訂單硬編 TWD、no-setter 測試只掃 `set*` 字面(reconstruct 從旁走過)、DTO setter 噪音等
- 特別檢查:後門=reconstruct(有);items() 複本(有);例外路徑不變量(**破**,finding 1)

**Spec 軸**:
- 缺漏:addItem 失敗路徑破不變量(同上,類別層級;HTTP 路徑因例外先於 save 未污染 DB);subtotal 裸 long 乘法違「金額運算一律走 Money」
- 越界:**`ORDER BY o.order_id`**(同 HL1 型);OrderStatus 帶中文 label;reconstruct 後門(死碼);Money 自加禁負數
- 可疑:**INNER JOIN customers 掉單(同 HL1 型:C-999 回 201、列表永不出現)**;DRAFT 列 NPE/「草稿」未定義行為(不可達);placedAt=save 副作用;原子性成立但靠「只有一次寫入」的偶然,非宣告的邊界;驗證失敗一律 500 未定義
- 最嚴重:addItem 例外路徑髒 Aggregate(「整份規格的核心主張在失敗路徑上失效,且沒有任何測試看得見」)

## 跨樣本綜合(reviewer 各自獨立指出、三份皆有)

1. 總額規則 Java/SQL 雙實作、無測試綁定——「Query 側不經 Aggregate」的系統成本。
2. 投機通用性(reconstitute/reconstruct、DRAFT label、未用 accessor)三樣本都有,Opus 的版本守住不變量、Haiku 的版本(HL2)開了洞。
3. 測試品質是新的洞層:恆真反射測試(HL1/HL2)讓「規則有測試」≠「規則有守衛」。
