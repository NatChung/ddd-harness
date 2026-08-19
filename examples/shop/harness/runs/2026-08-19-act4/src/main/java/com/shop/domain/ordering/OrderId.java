package com.shop.domain.ordering;

import java.util.Objects;
import java.util.UUID;

/** 訂單識別碼 —— SPEC.md §1 GLOSSARY;格式為 UUID v4 字串(§6 A-2)。 */
public final class OrderId {

    private final String value;

    private OrderId(String value) {
        this.value = value;
    }

    public static OrderId of(String value) {
        return new OrderId(value);
    }

    /** 產生一個新的訂單識別碼(UUID v4,§6 A-2)。 */
    public static OrderId newId() {
        return new OrderId(UUID.randomUUID().toString());
    }

    public String value() {
        return value;
    }

    @Override
    public boolean equals(Object o) {
        return o instanceof OrderId other && Objects.equals(this.value, other.value);
    }

    @Override
    public int hashCode() {
        return Objects.hashCode(value);
    }

    @Override
    public String toString() {
        return value;
    }
}
