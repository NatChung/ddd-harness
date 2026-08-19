package com.shop.domain.ordering;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * 內圈測試 —— 契約 C2(invariant):總價 = Σ(每個品項的單價 × 數量) + 運費。
 * 守在「訂單」這個聚合根內(SPEC.md §3 C2),所以測試打在 {@link Order} 上。
 *
 * <p>期望值一律抄規格算過的字面值(§2 G1 的 6520、§2 G2 的 11020),
 * 測試裡<b>不重跑 Σ(單價 × 數量) + 運費</b> —— 重算出來的期望值不管實作怎麼寫都會綠。
 */
@DisplayName("C2:總價 = Σ(單價 × 數量) + 運費")
class OrderTotalAmountTest {

    /** §2 G1:單價 3200 × 數量 2,運費 120 —— 規格算出 6520。 */
    @Test
    void C2_總價等於品項小計加總再加運費_單一品項() {
        Order order = Order.place(
                OrderId.of("11111111-1111-4111-8111-111111111111"),
                new CustomerName("王小明"),
                List.of(new OrderItem(new Sku("NIKE-DUNK-LOW-US9"), Money.twd(3200), new Quantity(2))),
                Money.twd(120),
                LocalDate.of(2026, 8, 19));

        assertThat(order.totalAmount()).isEqualTo(Money.twd(6520));
    }

    /** §2 G2:3200 × 2 與 4500 × 1,運費 120 —— 規格算出 11020。 */
    @Test
    void C2_總價等於品項小計加總再加運費_多個品項() {
        Order order = Order.place(
                OrderId.of("22222222-2222-4222-8222-222222222222"),
                new CustomerName("王小明"),
                List.of(
                        new OrderItem(new Sku("NIKE-DUNK-LOW-US9"), Money.twd(3200), new Quantity(2)),
                        new OrderItem(new Sku("NIKE-AIR-FORCE1-US9"), Money.twd(4500), new Quantity(1))),
                Money.twd(120),
                LocalDate.of(2026, 8, 19));

        assertThat(order.totalAmount()).isEqualTo(Money.twd(11020));
    }
}
