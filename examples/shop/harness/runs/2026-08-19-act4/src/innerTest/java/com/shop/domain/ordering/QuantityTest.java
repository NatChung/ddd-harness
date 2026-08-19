package com.shop.domain.ordering;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * 內圈測試 —— 契約 C5(invariant):訂單品項的數量為 ≥ 1 的整數。
 * 守在「訂單」這個聚合根內(SPEC.md §3 C5),數量這個 Value Object 是它的守門處。
 *
 * <p>下限的字面值 1 抄自 §1 GLOSSARY「數量:正整數,最小 1」與 §6 A-6;
 * 被拒的值 0 與 -1 抄自 §2 G16。
 */
@DisplayName("C5:訂單品項的數量為 ≥ 1 的整數")
class QuantityTest {

    @Test
    void C5_數量必須是大於等於1的整數() {
        assertThatThrownBy(() -> new Quantity(0))
                .isInstanceOf(DomainRuleViolation.class);
        assertThatThrownBy(() -> new Quantity(-1))
                .isInstanceOf(DomainRuleViolation.class);

        assertThatThrownBy(() -> Quantity.of(null))
                .isInstanceOf(DomainRuleViolation.class);

        assertThatCode(() -> new Quantity(1)).doesNotThrowAnyException();
        assertThatCode(() -> new Quantity(2)).doesNotThrowAnyException();
    }
}
