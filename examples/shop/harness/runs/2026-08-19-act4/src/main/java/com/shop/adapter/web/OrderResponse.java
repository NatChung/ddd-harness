package com.shop.adapter.web;

import com.shop.domain.ordering.Order;
import com.shop.domain.ordering.OrderItem;

import java.util.ArrayList;
import java.util.List;

/** 一張訂單的完整回應 —— §1.2 E2。 */
public record OrderResponse(String orderId,
                            String status,
                            String placedAt,
                            String currency,
                            String customerName,
                            List<Item> items,
                            long shippingFee,
                            long totalAmount) {

    public record Item(String sku, long unitPrice, int quantity, long lineSubtotal) {
    }

    public static OrderResponse from(Order order) {
        List<Item> items = new ArrayList<>();
        for (OrderItem item : order.items()) {
            items.add(new Item(
                    item.sku().value(),
                    item.unitPrice().amount(),
                    item.quantity().value(),
                    item.lineSubtotal().amount()));
        }
        return new OrderResponse(
                order.orderId().value(),
                order.status().name(),
                order.placedAt().toString(),
                order.totalAmount().currency(),
                order.customerName().value(),
                items,
                order.shippingFee().amount(),
                order.totalAmount().amount());
    }
}
