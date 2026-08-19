package com.shop.domain.ordering;

/**
 * 訂單品項(Entity,隸屬訂單)—— SPEC.md §1 GLOSSARY:一張訂單裡的一種鞋及其數量。
 */
public final class OrderItem {

    private final Sku sku;
    private final Money unitPrice;
    private final Quantity quantity;

    public OrderItem(Sku sku, Money unitPrice, Quantity quantity) {
        this.sku = sku;
        this.unitPrice = unitPrice;
        this.quantity = quantity;
    }

    public Sku sku() {
        return sku;
    }

    /** 單價 —— 下單當時的價錢。 */
    public Money unitPrice() {
        return unitPrice;
    }

    public Quantity quantity() {
        return quantity;
    }

    /** 品項小計 = 單價 × 數量(§1 GLOSSARY「品項小計」)。 */
    public Money lineSubtotal() {
        return unitPrice.times(quantity.value());
    }
}
