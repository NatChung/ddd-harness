# 標本:恆真的 `no-setter` 反射測試

`CONTEXT.md` 的**恆真(tautological)**詞條記著一個已知陽性:分層實驗的 `no-setter`
反射測試「掃不到任何真 setter,不管實作怎麼寫都會綠」。這裡是那兩個檔的副本。

⚠️ **只有 HL1 是恆真的。** 原本 `CONTEXT.md` 把 HL1 和 HL2 併稱一類,2026-08-19 逐檔查證
後發現是誤判 —— HL2 那支用完全不同的寫法,真 setter 抓得到。兩支都留在這裡,因為
**「同一條規則、兩份實作、兩種不同的錯法」比單看一支更有教學價值**。

## 出處

原本住在 `kc-log` repo 的兩個分支上(那批分層實驗分支沒有跟著匯出到本 repo):

| 檔 | 來源 | 診斷 |
|---|---|---|
| `HL1-OrderTest.java` | `layered/HL1-domain` @ `b62e517` — `examples/shop/app/src/test/java/com/shop/domain/OrderTest.java` | **恆真** |
| `HL2-OrderTest.java` | `layered/HL2-domain` @ `7baa0b6` — 同路徑 | 不恆真,但**過寬** |

## HL1 病在哪 —— 恆真

```java
assertFalse(hasSetterMethod(order.getClass(), "setStatus"));
...
private boolean hasSetterMethod(Class<?> clazz, String methodName) {
    try {
        clazz.getDeclaredMethod(methodName, Object.class);   // ← 這裡
        return true;
    } catch (NoSuchMethodException e) {
        return false;
    }
}
```

`getDeclaredMethod(name, Object.class)` 找的是**參數型別剛好是 `Object` 的**那個方法。
真的 setter 會是 `setStatus(OrderStatus)`、`setOrderId(OrderId)` —— 參數型別是領域型別,
不是 `Object`。所以這個查詢**永遠**丟 `NoSuchMethodException`,`hasSetterMethod` 永遠回
`false`,`assertFalse` 永遠綠。

**實作寫成什麼樣都不影響結果**——這正是恆真的定義:斷言依構造必然通過,不可能跟程式碼
意見相左。而它看起來很像在守一條真的領域規則(「聚合不得有 setter」),所以在 review 裡
會被讀成「這條有測」。

## HL2 病在哪 —— 不是恆真,是過寬

```java
var methods = Order.class.getDeclaredMethods();
for (var method : methods) {
    String methodName = method.getName();
    if (methodName.startsWith("set")) {
        fail("Order should not have setter method: " + methodName);
    }
}
```

這支**列舉所有宣告的方法**、看到名字以 `set` 開頭就 fail。真的 `setStatus(OrderStatus)`
**會**被它抓到 —— 所以它不恆真,實作寫得不一樣結果就會不一樣。

它的毛病在另一個方向:

- **過寬**:`getDeclaredMethods()` 含 private,一個叫 `setUpItems()` 的私有 helper 會被誤判成
  違規。它守的規則其實是「不得有**公開** setter」,但它沒有查 modifier。
- **同時又漏**:不叫 `set*` 的 mutator(`updateStatus`、`markPlaced`、直接改 public field)
  它一個都抓不到。

也就是說 HL1 和 HL2 是**同一條領域規則、兩份實作、兩種不同的錯法**:一個永遠不會紅,
一個會為了錯的理由紅、又為了錯的理由綠。這正是「規則寫在散文裡、由各自的實作自行詮釋」
會發生的事 —— 而 harness 要處理的就是這個。

## 為什麼留著

HL1 是「全綠不等於有驗到」最短的一個例子,而且不是設計出來的教材——是真的跑出來、
事後才被抓到的。HL2 則是這件事的第二層:**連「抓到了」都可能是為了錯的理由**。
兩支都不是設計出來的。抓法見 `tools/harness/vacuous_tests.py`(它交的是分診佇列,不是判決:
它分不出「恆真」與「碰不到」)。
