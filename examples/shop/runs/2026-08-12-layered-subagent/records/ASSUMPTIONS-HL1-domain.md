# 實作假設與設計決定

本文件記錄規格實作中的假設與消歧決定。

## 1. Order 的不可變性

**假設**: Order 的核心屬性（orderId、customerId）一旦建立不可變。

**決定**: 
- `orderId` 和 `customerId` 設定為 `final`，無 setter。
- `status` 雖為變動狀態，但只能經由 `place()` 方法改變。
- 規格明確要求「`Order` 不得有任何 setter」。

## 2. 明細集合的保護

**假設**: Order 內部的 items 清單必須受保護，外部程式碼不得直接修改。

**決定**:
- `items()` 方法回傳 `List.copyOf(items)` 而非直接回傳內部集合。
- 內部 items 欄位為 `final` 但可變（ArrayList），清單本身可透過 `add()` 改變但引用不變。
- OrderItem 建構子設定為 package-private，只允許 Order 類別建立新明細。

## 3. 原子性保證

**假設**: `addItem()` 方法的所有驗證都通過後才修改狀態。

**決定**:
- 先驗證訂單狀態（必須為 DRAFT）
- 驗證幣別一致性（與現有明細比較）
- 建立新 OrderItem（OrderItem 建構子自行驗證非空、數量正數）
- 最後才 `items.add(newItem)`
- 若任何驗證失敗，Order 不變

## 4. 貨幣一致性

**假設**: 同一訂單內所有明細必須使用相同幣別。

**決定**:
- 首個明細決定幣別
- 後續明細必須與首個明細幣別相同，否則拋 `IllegalArgumentException`
- 使用 `unitPrice.getCurrency()` 比較（Money 的 currency 已自動 toUpperCase）

## 5. Money 的加法

**假設**: Money.add() 必須檢查幣別，不同幣別拋例外。

**決定**:
- `Money.add(Money other)` 檢查 `this.currency.equals(other.currency)`
- 不符合拋 `IllegalArgumentException` 與詳細訊息
- `total()` 方法利用此性質確保計算正確

## 6. Empty Order 的 total() 行為

**假設**: 空訂單（無明細）不應能計算總額。

**決定**:
- `total()` 方法先檢查 `items.isEmpty()`
- 空訂單拋 `IllegalStateException` 與訊息「Cannot compute total of an empty order」
- 這是程式邏輯錯誤（外部程式碼不應呼叫空訂單的 total），非業務例外

## 7. place() 後禁止修改明細

**假設**: 已成立（PLACED）的訂單不得新增明細，也不得再次下單。

**決定**:
- `addItem()` 檢查 `status == DRAFT`，非 DRAFT 拋 `IllegalStateException`
- `place()` 檢查 `status != PLACED`，已下單拋 `IllegalStateException`
- 這些都是呼叫方的邏輯錯誤，不是業務例外（用 IllegalStateException 而非 Exception）

## 8. OrderItem 的相等性

**假設**: OrderItem 以值相等比較（productId、quantity、unitPrice）。

**決定**:
- `OrderItem.equals()` 和 `hashCode()` 實作完整的值比較
- 包括 productId、quantity 和 unitPrice 三個欄位
- 用於測試和查詢時的相等性判定

## 9. Value Object 的識別碼格式

**假設**: OrderId、CustomerId、ProductId 都以字串值為基礎，無額外驗證格式。

**決定**:
- 僅檢查非 null 和非 blank
- 不驗證前綴、編號格式等（如不驗證 OrderId 必須 "ORD-" 開頭）
- 格式驗證由 usecase 層負責（如有需要）

## 10. Order.total() 的計算順序

**假設**: Order 總額 = 逐項明細小計的加總。

**決定**:
- 第一項：直接取 `items.get(0).subtotal()`
- 後續項：逐項 `result.add(items.get(i).subtotal())`
- 利用 Money.add() 的幣別檢查確保安全性
- OrderItem.subtotal() = unitPrice.multiply(quantity)

## 11. 建構子的 null 檢查

**假設**: Order、OrderItem、Money、各 ID 類別都應檢查必要引數非 null。

**決定**:
- 使用 `Objects.requireNonNull(obj, "message")` 拋 `NullPointerException`
- blank 字串（如 ""、"  "）視同無效，拋 `IllegalArgumentException`
- currency 會自動 `toUpperCase()`

## 12. 測試範疇

**假設**: 領域層測試涵蓋所有公開 API 和領域規則。

**決定**:
- OrderTest：Order Aggregate 的完整測試（建構、addItem、place、total 等）
- 各 Value Object 測試：基本構造、null/blank 檢查、值相等性、特有方法
- OrderItemTest：OrderItem 的特性（建構、subtotal、相等性）
- 未包含 usecase 或 adapter 層的測試（這些由上層負責）
