package com.shop.adapter.persistence;

import jakarta.persistence.CollectionTable;
import jakarta.persistence.ElementCollection;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OrderColumn;
import jakarta.persistence.Table;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

/** 訂單的落地形狀。JPA 只住在 adapter 層,領域層不認識它。 */
@Entity
@Table(name = "orders")
public class OrderJpaEntity {

    @Id
    private String orderId;

    private String customerName;

    private long shippingFee;

    private LocalDate placedAt;

    private String status;

    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(name = "order_items", joinColumns = @JoinColumn(name = "order_id"))
    @OrderColumn(name = "line_no")
    private List<OrderItemEmbeddable> items = new ArrayList<>();

    protected OrderJpaEntity() {
    }

    OrderJpaEntity(String orderId,
                   String customerName,
                   long shippingFee,
                   LocalDate placedAt,
                   String status,
                   List<OrderItemEmbeddable> items) {
        this.orderId = orderId;
        this.customerName = customerName;
        this.shippingFee = shippingFee;
        this.placedAt = placedAt;
        this.status = status;
        this.items = new ArrayList<>(items);
    }

    String orderId() {
        return orderId;
    }

    String customerName() {
        return customerName;
    }

    long shippingFee() {
        return shippingFee;
    }

    LocalDate placedAt() {
        return placedAt;
    }

    String status() {
        return status;
    }

    List<OrderItemEmbeddable> items() {
        return items;
    }
}
