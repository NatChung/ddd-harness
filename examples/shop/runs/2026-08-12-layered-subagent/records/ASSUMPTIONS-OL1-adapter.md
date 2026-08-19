# ASSUMPTIONS(adapter 層)

規格沒講到、或講得不夠死而由實作自己決定的地方,一條一行:遇到什麼歧義、選了什麼、為什麼。
範圍限於轉接層(`com/shop/adapter/`);`domain/` 與 `usecase/` 是既有的唯讀輸入,未更動。

## 持久化

1. **表名用 `orders` / `order_items`,不用 `order`** —— `ORDER` 是 SQL 保留字,表名叫 `order`
   會讓查詢在多數方言(含 H2)需要引號才跑得動。規格沒指定表名,選了不需要引號的複數形。
2. **明細用 `@ElementCollection` + `@Embeddable`,不建第二個 `@Entity`** —— `OrderItem` 是
   Aggregate 內部物件、沒有獨立身分,存成從屬表比給它一個獨立 entity 身分更貼近領域;
   也省掉 cascade / orphan-removal 的設定。規格沒規定持久化模型的形狀。
3. **總額不落地** —— `orders` 表沒有 total 欄位,列表頁的總額由明細即時加總。規格說
   「明細與總額的一致性由 `Order` 自己維護」,存一份總額就等於在資料庫裡放了第二份可能
   跟明細對不起來的真相。代價是列表查詢要 `SUM`,在本規格的規模下無所謂。
4. **`save()` 走 Spring Data 的 `save()`(merge 語意)** —— 新建與更新同一條路徑,符合
   `OrderRepository.save` 的 javadoc(「新建或更新皆走這個方法」)。
5. **`nextOrderId()` 用 `UUID.randomUUID()`** —— 介面 javadoc 直接建議這個做法。
6. **沒有實作「載入 Aggregate」的路徑** —— `OrderRepository` 只宣告 `nextOrderId` / `save`,
   讀取側完全不經過 `Order`,因此 `Order.reconstitute` 在本規格下沒有呼叫端。不預先建一條
   沒人用的還原路徑(要用時再加)。

## Query 側

7. **用 `JdbcTemplate` 而非 JPQL/JPA 查詢** —— 列表要 join 的 `customers` 表刻意沒有領域物件、
   本實作也不為它建 JPA entity(ARCHITECTURE 明講不要為它建領域物件),用 SQL 直接查最直接;
   同時 `RowMapper` 能明確控制型別轉換,不必應付 native query 回傳 `Object[]` 的型別意外。
8. **一句 SQL 組出整列** —— 訂單、明細加總、顧客姓名在同一次查詢接起來,不 findAll 領域物件
   再逐筆 map(ARCHITECTURE 的 Query 側規則)。
9. **加總「分」時忽略幣別** —— `OrderListItem.totalCents` 的形狀裡沒有幣別。同一筆訂單的明細
   幣別必然一致(寫入時由 `Order.addItem` / `Money.add` 守住),所以直接加總是安全的。
10. **查無顧客時 `customerName` 退回 `customerId`** —— `OrderListItem` 要求 `customerName`
    非 null,而 `customers` 是外部系統維護的表,訂單的 `CustomerId` 不保證找得到對應列。
    選擇 `COALESCE(c.name, o.customer_id)` 讓列表仍然顯示得出東西,而不是整個查詢炸掉。
    (驗收用的 C-001/C-002 都在表內,這條只在資料缺漏時才會生效。)
11. **不加排序** —— 規格明講排序不在範圍內,所以 SQL 沒有 `ORDER BY`,順序由資料庫決定。
12. **狀態顯示文字一律走 `OrderListItem.of(...)`** —— 「PLACED 顯示成『已成立』」歸 usecase 層
    所有,adapter 不自己編這個字串,只負責把資料庫的狀態字串轉回 `OrderStatus`。

## HTTP

13. **請求 DTO 與 use case 的 `Command` 分開兩個型別** —— controller 的
    `PlaceOrderRequest` 只描述傳輸格式,轉成 `PlaceOrderUseCase.Command` 是 controller 的工作。
    多一次轉換的代價,換 HTTP 形狀改變時不必動 use case。
14. **不做錯誤回應的對映(沒有 `@ExceptionHandler`)** —— 規格只定義了 201/200 兩條成功路徑,
    錯誤回應的形狀完全沒講,驗證框架也明列在範圍外。因此輸入不合領域規則時,領域丟出的
    `IllegalArgumentException` / `IllegalStateException` 會以 Spring 預設的 500 呈現。
    要有 400/409 的話應該是規格先講清楚形狀,而不是在這裡自己發明一套。
15. **`GET /orders` 直接回 `OrderListItem`,`POST /orders` 回 adapter 自己的 response 物件**
    —— 兩者都不是 `domain/` 型別,符合 ARCHITECTURE「往外傳的形狀」那條。
    `placedAt` 靠 Spring Boot 預設的 Jackson JSR-310 設定序列化成 `YYYY-MM-DD`,沒有另外設定。

## 沒有動到的東西

16. **`application.properties` 與 `data.sql` 一個字都沒改** —— `ddl-auto=create-drop` 會依
    entity 建出 `orders` / `order_items`,`defer-datasource-initialization=true` 保證
    `data.sql` 在那之後才跑,harness 給的設定不需要為這份實作調整。
17. **沒有寫 `INTERFACE-REQUESTS.md`** —— `domain/` 與 `usecase/` 現有的公開介面
    (`Order.create/addItem/place` 與各 accessor、`OrderListItem.of`、兩個 repository 介面、
    `PlaceOrderUseCase.Command/Item`)足以完成整個轉接層,沒有任何一處需要內層加方法、
    開建構子或放寬可見性,因此沒有需要提出的介面請求。

## 現況

全部測試綠:58 個測試、0 失敗(驗收 5、機械檢查 4、既有內兩層 49)。沒有卡住的項目。
