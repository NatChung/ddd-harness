package com.shop.domain.ordering;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * 內圈測試 —— 契約 C9(precondition)、C16 / C17(postcondition)。
 * 三條都守在「訂單」這個聚合根內(SPEC.md §3),所以測試打在 {@link Order} 上。
 *
 * <p>狀態值 PLACED / SHIPPED / RECEIVED 與每一條轉移的合法與否抄自 §2 G10 / G11 / G12
 * 與 §6 A-12「已成立 → 已出貨 → 收到,不可回退」。
 */
@DisplayName("C9 / C16 / C17:訂單狀態單向前進")
class OrderStatusTransitionTest {

    private static Order placedOrder() {
        return Order.place(
                OrderId.of("33333333-3333-4333-8333-333333333333"),
                new CustomerName("王小明"),
                List.of(new OrderItem(new Sku("NIKE-DUNK-LOW-US9"), Money.twd(3200), new Quantity(2))),
                Money.twd(120),
                LocalDate.of(2026, 8, 19));
    }

    /** §2 G10 / G11:已成立 → 已出貨 → 收到 走得通;§2 G12:收到 → 已出貨 被擋下。 */
    @Test
    void C9_訂單狀態只能沿已成立到已出貨到收到單向前進() {
        Order order = placedOrder();
        assertThat(order.status()).isEqualTo(OrderStatus.PLACED);

        order.changeStatusTo(OrderStatus.SHIPPED);
        assertThat(order.status()).isEqualTo(OrderStatus.SHIPPED);

        order.changeStatusTo(OrderStatus.RECEIVED);
        assertThat(order.status()).isEqualTo(OrderStatus.RECEIVED);

        // 回退(§2 G12)
        assertThatThrownBy(() -> order.changeStatusTo(OrderStatus.SHIPPED))
                .isInstanceOf(DomainRuleViolation.class);
        // 跳過中間那一段
        Order another = placedOrder();
        assertThatThrownBy(() -> another.changeStatusTo(OrderStatus.RECEIVED))
                .isInstanceOf(DomainRuleViolation.class);
        // 原地不動
        assertThatThrownBy(() -> another.changeStatusTo(OrderStatus.PLACED))
                .isInstanceOf(DomainRuleViolation.class);
    }

    /** §3 C16:狀態變更成功後,訂單除 status 外的欄位逐欄不變。 */
    @Test
    void C16_狀態變更成功後除了狀態以外逐欄不變() {
        Order order = placedOrder();

        order.changeStatusTo(OrderStatus.SHIPPED);

        assertThat(order.orderId()).isEqualTo(OrderId.of("33333333-3333-4333-8333-333333333333"));
        assertThat(order.customerName()).isEqualTo(new CustomerName("王小明"));
        assertThat(order.placedAt()).isEqualTo(LocalDate.of(2026, 8, 19));
        assertThat(order.shippingFee()).isEqualTo(Money.twd(120));
        assertThat(order.items()).hasSize(1);
        assertThat(order.items().get(0).sku()).isEqualTo(new Sku("NIKE-DUNK-LOW-US9"));
        assertThat(order.items().get(0).unitPrice()).isEqualTo(Money.twd(3200));
        assertThat(order.items().get(0).quantity()).isEqualTo(new Quantity(2));
        // 6520 是 §2 G1 算過的字面值
        assertThat(order.totalAmount()).isEqualTo(Money.twd(6520));
        assertThat(order.itemCount()).isEqualTo(2);
    }

    /** §3 C17:狀態變更被拒時,訂單狀態停在原狀態,不留中間態。 */
    @Test
    void C17_狀態變更被拒時停在原狀態() {
        Order order = placedOrder();

        assertThatThrownBy(() -> order.changeStatusTo(OrderStatus.RECEIVED))
                .isInstanceOf(DomainRuleViolation.class);

        assertThat(order.status()).isEqualTo(OrderStatus.PLACED);
    }
}
