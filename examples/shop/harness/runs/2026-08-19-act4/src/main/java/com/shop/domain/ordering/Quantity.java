package com.shop.domain.ordering;

/** 數量(Value Object)—— SPEC.md §1 GLOSSARY「數量」:同一款鞋買幾雙。 */
public final class Quantity {

    private final int value;

    public Quantity(int value) {
        if (value < 1) {
            throw new DomainRuleViolation(
                    "INVALID_QUANTITY", "數量必須是大於等於 1 的整數,收到 " + value);
        }
        this.value = value;
    }

    /** 以呼叫方帶入的數量建立;從缺跟 0 / 負數一樣是組不出訂單品項的值。 */
    public static Quantity of(Integer value) {
        if (value == null) {
            throw new DomainRuleViolation("INVALID_QUANTITY", "數量不可從缺");
        }
        return new Quantity(value);
    }

    public int value() {
        return value;
    }

    @Override
    public boolean equals(Object o) {
        return o instanceof Quantity other && this.value == other.value;
    }

    @Override
    public int hashCode() {
        return Integer.hashCode(value);
    }

    @Override
    public String toString() {
        return Integer.toString(value);
    }
}
