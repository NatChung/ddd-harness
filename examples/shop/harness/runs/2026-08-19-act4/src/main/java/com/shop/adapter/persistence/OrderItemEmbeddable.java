package com.shop.adapter.persistence;

import jakarta.persistence.Embeddable;

/** 訂單品項的落地形狀。純粹是持久化細節,領域層看不到它。 */
@Embeddable
public class OrderItemEmbeddable {

    private String sku;
    private long unitPrice;
    private int quantity;

    protected OrderItemEmbeddable() {
    }

    OrderItemEmbeddable(String sku, long unitPrice, int quantity) {
        this.sku = sku;
        this.unitPrice = unitPrice;
        this.quantity = quantity;
    }

    String sku() {
        return sku;
    }

    long unitPrice() {
        return unitPrice;
    }

    int quantity() {
        return quantity;
    }
}
