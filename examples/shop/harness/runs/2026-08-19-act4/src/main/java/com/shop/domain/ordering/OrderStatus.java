package com.shop.domain.ordering;

/**
 * 訂單狀態 —— SPEC.md §6 A-3(已成立 / PLACED)、`暫定 [Q27]`(已出貨 / 收到)。
 */
public enum OrderStatus {
    /** 已成立 */
    PLACED,
    /** 已出貨 */
    SHIPPED,
    /** 收到 */
    RECEIVED;

    /**
     * 這個狀態下一個(且唯一)可以走到的狀態;已經是終點就回 {@code null}。
     * 單向不可回退 —— §6 A-12。
     */
    OrderStatus next() {
        return switch (this) {
            case PLACED -> SHIPPED;
            case SHIPPED -> RECEIVED;
            case RECEIVED -> null;
        };
    }
}
