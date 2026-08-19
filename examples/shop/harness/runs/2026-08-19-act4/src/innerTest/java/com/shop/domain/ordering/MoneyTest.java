package com.shop.domain.ordering;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * 內圈測試 —— 契約 C4(invariant):金額的幣別恆為 TWD,數值為非負整數。
 * 守在「訂單」的金額 Value Object 自身(SPEC.md §3 C4),所以測試打在 {@link Money} 上。
 *
 * <p>幣別的字面值 TWD 抄自 §1 GLOSSARY「金額」與 §1.2 名詞對照(currency 恆為 "TWD");
 * 被拒的 -3200 抄自 §2 G17。
 */
@DisplayName("C4:金額幣別恆為 TWD,數值為非負整數")
class MoneyTest {

    @Test
    void C4_金額的幣別恆為TWD且數值不可為負() {
        assertThat(Money.twd(3200).currency()).isEqualTo("TWD");

        assertThatThrownBy(() -> Money.twd(-3200))
                .isInstanceOf(DomainRuleViolation.class);
        assertThatThrownBy(() -> Money.of("USD", 3200L))
                .isInstanceOf(DomainRuleViolation.class);

        assertThatCode(() -> Money.twd(0)).doesNotThrowAnyException();
        assertThatCode(() -> Money.of("TWD", 3200L)).doesNotThrowAnyException();
    }
}
