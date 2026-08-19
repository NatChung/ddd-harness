package com.shop.adapter.web;

import com.shop.domain.ordering.Order;

/** 訂單列表的一列 —— §1.2 E3。{@code itemCount} 是所有品項的數量加總,不是品項種類數。 */
public record OrderListRow(String orderId,
                           String placedAt,
                           String status,
                           String customerName,
                           int itemCount,
                           String currency,
                           long totalAmount) {

    public static OrderListRow from(Order order) {
        return new OrderListRow(
                order.orderId().value(),
                order.placedAt().toString(),
                order.status().name(),
                order.customerName().value(),
                order.itemCount(),
                order.totalAmount().currency(),
                order.totalAmount().amount());
    }
}
