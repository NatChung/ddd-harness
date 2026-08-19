package com.shop.domain.ordering;

import java.util.Objects;

/** 鞋子 SKU(識別碼,字串)—— SPEC.md §1 GLOSSARY「鞋子 SKU」。 */
public final class Sku {

    private final String value;

    public Sku(String value) {
        this.value = value;
    }

    public String value() {
        return value;
    }

    @Override
    public boolean equals(Object o) {
        return o instanceof Sku other && Objects.equals(this.value, other.value);
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
