package com.shop.domain.ordering;

import java.time.LocalDate;
import java.util.List;

/**
 * 訂單(Aggregate Root)—— SPEC.md §1 GLOSSARY:客人付費成功之後產生的一筆購買紀錄。
 */
public final class Order {

    private final OrderId orderId;
    private final CustomerName customerName;
    private final List<OrderItem> items;
    private final Money shippingFee;
    private final LocalDate placedAt;
    private OrderStatus status;

    private Order(OrderId orderId,
                  CustomerName customerName,
                  List<OrderItem> items,
                  Money shippingFee,
                  LocalDate placedAt,
                  OrderStatus status) {
        this.orderId = orderId;
        this.customerName = customerName;
        this.items = List.copyOf(items);
        this.shippingFee = shippingFee;
        this.placedAt = placedAt;
        this.status = status;
    }

    /** 產生一張新訂單,狀態為已成立(§6 A-3)。 */
    public static Order place(OrderId orderId,
                              CustomerName customerName,
                              List<OrderItem> items,
                              Money shippingFee,
                              LocalDate placedAt) {
        if (items == null || items.isEmpty()) {
            throw new DomainRuleViolation("EMPTY_ORDER", "訂單至少要有一個訂單品項");
        }
        return new Order(orderId, customerName, items, shippingFee, placedAt, OrderStatus.PLACED);
    }

    /** 從既有的落地資料還原一張訂單(狀態照原樣,不重跑「產生」這件事)。 */
    public static Order restore(OrderId orderId,
                                CustomerName customerName,
                                List<OrderItem> items,
                                Money shippingFee,
                                LocalDate placedAt,
                                OrderStatus status) {
        return new Order(orderId, customerName, items, shippingFee, placedAt, status);
    }

    public OrderId orderId() {
        return orderId;
    }

    public CustomerName customerName() {
        return customerName;
    }

    public List<OrderItem> items() {
        return items;
    }

    public Money shippingFee() {
        return shippingFee;
    }

    public LocalDate placedAt() {
        return placedAt;
    }

    public OrderStatus status() {
        return status;
    }

    /**
     * 改狀態 —— 訂單成立後唯一被允許的變更(C8、[Q24]「只會更改狀態」)。
     * 只能沿 已成立 → 已出貨 → 收到 單向前進(C9);走不通就原地不動(C17)。
     */
    public void changeStatusTo(OrderStatus target) {
        if (target != status.next()) {
            throw new DomainRuleViolation(
                    "INVALID_STATUS_TRANSITION", "訂單狀態不能從 " + status + " 改成 " + target);
        }
        this.status = target;
    }

    /** 商品金額合計 = 所有品項小計加總(不含運費;§1 禁用同義詞清單)。 */
    public Money itemsSubtotal() {
        Money sum = Money.twd(0);
        for (OrderItem item : items) {
            sum = sum.plus(item.lineSubtotal());
        }
        return sum;
    }

    /** 總價 = 商品金額合計 + 運費(C2,§7-1 由 [Q26] 裁決取這一個公式)。 */
    public Money totalAmount() {
        return itemsSubtotal().plus(shippingFee);
    }

    /** 所有品項的數量加總(不是品項種類數;§1.2 E3)。 */
    public int itemCount() {
        int count = 0;
        for (OrderItem item : items) {
            count += item.quantity().value();
        }
        return count;
    }
}
