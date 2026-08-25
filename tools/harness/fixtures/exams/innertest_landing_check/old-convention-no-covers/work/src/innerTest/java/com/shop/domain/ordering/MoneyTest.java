package com.shop.domain.ordering;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * 內圈測試 —— 契約 C4(invariant):金額的幣別恆為 TWD,數值為非負整數。
 * 守在「訂單」的金額 Value Object 自身(SPEC.md §3 C4),所以測試打在 {@link Money} 上。
 */
@DisplayName("C4:金額幣別恆為 TWD,數值為非負整數")
class MoneyTest {

    @Test
    void C4_金額的幣別恆為TWD且數值不可為負() {
        assertThat(Money.twd(3200).currency()).isEqualTo("TWD");
    }
}
