package com.shop.domain.ordering;

import java.util.Objects;

/** 名字(Value Object)—— SPEC.md §1 GLOSSARY「名字」:客戶的姓名。 */
public final class CustomerName {

    private final String value;

    public CustomerName(String value) {
        this.value = value;
    }

    public String value() {
        return value;
    }

    @Override
    public boolean equals(Object o) {
        return o instanceof CustomerName other && Objects.equals(this.value, other.value);
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
