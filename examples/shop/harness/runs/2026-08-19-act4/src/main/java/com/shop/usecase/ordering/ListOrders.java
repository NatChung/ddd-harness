package com.shop.usecase.ordering;

import com.shop.domain.ordering.Order;

import java.util.List;

/** 看所有訂單 —— §1.2 E3;依 §10 的阻斷指示,本次一律回所有訂單(後台語意),不做身分判斷。 */
public final class ListOrders {

    private final OrderRepository orders;

    public ListOrders(OrderRepository orders) {
        this.orders = orders;
    }

    public List<Order> all() {
        return orders.findAll();
    }
}
