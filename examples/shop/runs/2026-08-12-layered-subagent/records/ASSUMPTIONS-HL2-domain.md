# 領域層實作的歧義解決與假設

本文件記錄在實作領域層時遇到的規格歧義、做出的設計決定，以及為什麼這樣決定。

## 1. Order 的初始幣別

**歧義**: 規格要求 Order 的 `total` 與明細一致（每條明細有 `Money` 包含幣別），但新訂單未加入任何明細前，`total` 應該是多少？

**決定**: 新訂單的 `total` 初始化為 `Money.of(0, "TWD")`。

**理由**:
- 題目是訂單系統，通常使用台幣（TWD）
- 第一條明細加入時，`recalculateTotal()` 會基於該明細的幣別重算，確保幣別一致
- 若所有明細都是同一幣別，總額幣別會自動與之相同
- 若明細幣別不同會在加法時丟異常，防止混淆

## 2. Order 的 reconstruct 方法

**歧義**: 規格未明確說明 repository 如何重建 Order 實體（從持久化層）。

**決定**: 提供公開的 `reconstruct(orderId, customerId, items, total, status)` 工廠方法。

**理由**:
- 領域層不應知曉持久化細節，但需提供方式讓外層重建已持久化的訂單
- 由 repository（adapter 層）負責呼叫 `reconstruct()` 把資料庫資料轉成 Order 物件
- 這符合「依賴性倒轉」原則：內層提供介面，外層實作

## 3. OrderItem 的建構子可見性

**歧義**: OrderItem 是 Aggregate 內部物件，規格要求「只能經由 Order 修改」，但如何保證呢？

**決定**: OrderItem 的建構子設為**包級別可見** (`package-private`)，不是 public。

**理由**:
- 同一包內（com.shop.domain）的類別可以存取包級別成員
- Order 與 OrderItem 都在 com.shop.domain 包內，Order 可以創建 OrderItem
- 測試也在 com.shop.domain 包內，可以直接造 OrderItem（方便單元測試）
- 外部代碼（usecase、adapter）無法直接 `new OrderItem(...)`，保證一致性邊界

## 4. items() 回傳不可變複本

**歧義**: 「回傳複本」確切的語義是什麼？集合裡的 OrderItem 本身也要複製嗎？

**決定**: `items()` 回傳 `List.copyOf(items)`，集合本身不可修改，但 OrderItem 物件本身是同一個引用。

**理由**:
- OrderItem 本身是不可變物件（無 setter），所以即使持有同一個引用也安全
- `List.copyOf()` 回傳的 List 是不可變的，修改會丟 `UnsupportedOperationException`
- 這符合規格要求「呼叫端拿到的集合改不到 Order 本體」
- 避免不必要的深複製開銷

## 5. addItem 時的幣別檢查

**歧義**: addItem(ProductId, int, Money) 是否應該檢查新明細的幣別與既有明細是否相同？

**決定**: 不主動檢查。在 `recalculateTotal()` 時會自動檢查（Money.add 會丟異常）。

**理由**:
- 如果試圖加入不同幣別的明細，在重算總額時 Money.add() 會丟 `IllegalArgumentException`
- 這樣設計更簡潔：Money 本身掌管幣別規則
- 若想要提前檢查，應在 addItem 內加檢查邏輯，但現階段保持簡單

## 6. place() 的前置條件

**決定**: `place()` 要求訂單至少有一條明細。空訂單無法 place。

**理由**:
- 業務上沒有「空訂單」這回事
- 規格未明確禁止，但規格情景 1 的「一筆含單一明細的訂單」暗示訂單必有明細
- 提前檢查避免後續查詢/持久化時的異常

## 7. OrderStatus 的標籤

**決定**: 
- `DRAFT` 的標籤是「草稿」
- `PLACED` 的標籤是「已成立」

**理由**:
- SPEC.md 第 16 行明確寫「已成立」是 PLACED 的顯示文字
- 「草稿」是對稱的中文詞彙，对应 DRAFT 状态

## 8. Value Object 的 null 檢查

**決定**: 所有 Value Object（OrderId、CustomerId、ProductId、Money）在構造時驗證 null 和空白字串。

**理由**:
- Value Object 應該自我守護不變式
- 防止無效的標識符或金額在領域層傳播
- 盡早失敗（fail-fast），錯誤在最早被偵測到

## 9. Order 以 OrderId 比較相等

**決定**: `Order.equals()` 只比較 `orderId`。

**理由**:
- OrderId 是訂單的唯一識別
- 兩份有相同 OrderId 的 Order 物件在領域概念上是同一筆訂單
- 即使其他欄位（明細、狀態）不同，仍應視為同一個聚合根

## 10. OrderItem 以完整內容比較相等

**決定**: `OrderItem.equals()` 比較 `productId`、`quantity`、`unitPrice` 三項。

**理由**:
- OrderItem 是值物件式的內部物件，應以完整內容判斷相等
- 如果兩條明細的商品、數量、單價都相同，就是同一條
- 這支持業務邏輯中的「檢查是否重複」等操作
