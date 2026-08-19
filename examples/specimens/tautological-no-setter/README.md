# 標本:恆真的 `no-setter` 反射測試

`CONTEXT.md` 的**恆真(tautological)**詞條記著一個已知陽性:分層實驗 HL1/HL2 的
`no-setter` 反射測試「掃不到任何真 setter,不管實作怎麼寫都會綠」。這裡是那兩個檔的副本。

## 出處

原本住在 `kc-log` repo 的兩個分支上(那批分層實驗分支沒有跟著匯出到本 repo):

| 檔 | 來源 |
|---|---|
| `HL1-OrderTest.java` | `layered/HL1-domain` @ `b62e517` — `examples/shop/app/src/test/java/com/shop/domain/OrderTest.java` |
| `HL2-OrderTest.java` | `layered/HL2-domain` @ `7baa0b6` — 同路徑 |

## 病在哪

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

## 為什麼留著

它是「全綠不等於有驗到」最短的一個例子,而且不是設計出來的教材——是真的跑出來、
事後才被抓到的。抓法見 `tools/harness/vacuous_tests.py`(它交的是分診佇列,不是判決:
它分不出「恆真」與「碰不到」)。
