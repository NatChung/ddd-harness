package com.shop;

import org.junit.jupiter.api.Test;

/**
 * 守 C1;C7 是打字錯(store 沒有)。
 * @covers C1, C7
 */
class ATest {
    @Test
    void x() { Order.place(OrderId.of("x")); }
}
