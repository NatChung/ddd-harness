package com.shop;

import org.junit.jupiter.api.Test;

/**
 * 守 C1 與 S1。
 * @covers C1, S1
 */
class ATest {
    @Test
    void x() { Order.place(OrderId.of("x")); }
}
