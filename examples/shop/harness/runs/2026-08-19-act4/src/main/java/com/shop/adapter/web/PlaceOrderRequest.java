package com.shop.adapter.web;

import java.util.List;

/**
 * {@code POST /orders} 的 request 形狀。
 *
 * <p>欄位名照這套驗收釘住的 wire 合約:{@code customer} 是一個字串(客戶的名字),
 * 品項只有 {@code sku} / {@code quantity} / {@code unitPrice} / {@code currency}。
 */
public record PlaceOrderRequest(String customer, List<Item> items) {

    public record Item(String sku, Integer quantity, Long unitPrice, String currency) {
    }
}
