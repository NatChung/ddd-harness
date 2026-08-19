package com.shop.domain.ordering;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * 內圈測試 —— 契約 C3(invariant):訂單至少有一個訂單品項。
 * 守在「訂單」這個聚合根內(SPEC.md §3 C3;依據 §6 A-9「空訂單無業務意義」)。
 */
@DisplayName("C3:訂單至少有一個訂單品項")
class OrderItemsRequiredTest {

    @Test
    void C3_訂單至少要有一個訂單品項() {
        assertThatThrownBy(() -> Order.place(
                OrderId.newId(),
                new CustomerName("王小明"),
                List.of(),
                Money.twd(0),
                LocalDate.of(2026, 8, 19)))
                .isInstanceOf(DomainRuleViolation.class);

        assertThatCode(() -> Order.place(
                OrderId.newId(),
                new CustomerName("王小明"),
                List.of(new OrderItem(new Sku("NIKE-DUNK-LOW-US9"), Money.twd(3200), new Quantity(1))),
                Money.twd(0),
                LocalDate.of(2026, 8, 19)))
                .doesNotThrowAnyException();
    }
}
