package com.shop.domain.ordering;

import java.util.Objects;

/**
 * 金額(Value Object)—— SPEC.md §1 GLOSSARY「金額」。
 *
 * <p>幣別固定 TWD;整數,單位為「元」,不含小數。
 * 相等性 = 幣別相同且數值相同。
 */
public final class Money {

    /** 本系統唯一的幣別(§1 GLOSSARY「金額」、§5「多幣別」不在範圍)。 */
    public static final String CURRENCY = "TWD";

    private final long amount;

    private Money(long amount) {
        if (amount < 0) {
            throw new DomainRuleViolation("INVALID_AMOUNT", "金額不可為負,收到 " + amount);
        }
        this.amount = amount;
    }

    /** 以 TWD 元建立金額。 */
    public static Money twd(long amount) {
        return new Money(amount);
    }

    /** 以呼叫方帶入的幣別與數值建立金額。 */
    public static Money of(String currency, Long amount) {
        if (currency != null && !CURRENCY.equals(currency)) {
            throw new DomainRuleViolation(
                    "INVALID_CURRENCY", "幣別恆為 " + CURRENCY + ",收到 " + currency);
        }
        if (amount == null) {
            throw new DomainRuleViolation("INVALID_AMOUNT", "單價不可從缺");
        }
        return new Money(amount);
    }

    /** 幣別,恆為 TWD。 */
    public String currency() {
        return CURRENCY;
    }

    /** 數值,單位為 TWD 元。 */
    public long amount() {
        return amount;
    }

    public Money plus(Money other) {
        return new Money(this.amount + other.amount);
    }

    /** 乘上一個數量 —— 品項小計用。 */
    public Money times(int multiplier) {
        return new Money(this.amount * multiplier);
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof Money other)) {
            return false;
        }
        return this.amount == other.amount;
    }

    @Override
    public int hashCode() {
        return Objects.hash(CURRENCY, amount);
    }

    @Override
    public String toString() {
        return CURRENCY + " " + amount;
    }
}
