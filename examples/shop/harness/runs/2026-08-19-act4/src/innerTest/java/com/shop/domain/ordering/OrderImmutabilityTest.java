package com.shop.domain.ordering;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * 內圈測試 —— 契約 C8(precondition):訂單成立後,除狀態外的任何欄位皆不得修改。
 * 守在「訂單」這個聚合根內(SPEC.md §3 C8;來源 [Q24]「只會更改狀態」)。
 *
 * <p>期望值來自規格那一句話本身:<b>唯一</b>被允許的變更是狀態。所以這裡驗的是
 * 「訂單身上除了改狀態那一個方法以外,沒有第二個能改到它的東西」——
 * 日後有人加一個 setter,這條就會紅。
 */
@DisplayName("C8:訂單成立後除狀態外不得修改")
class OrderImmutabilityTest {

    /** 規格允許的唯一變更(§3 C8 / C9),其餘一律不得存在。 */
    private static final String THE_ONLY_ALLOWED_MUTATOR = "changeStatusTo";

    private static Order placedOrder(List<OrderItem> items) {
        return Order.place(
                OrderId.of("44444444-4444-4444-8444-444444444444"),
                new CustomerName("王小明"),
                items,
                Money.twd(120),
                LocalDate.of(2026, 8, 19));
    }

    @Test
    void C8_訂單成立後除了狀態以外沒有任何欄位改得動() {
        List<OrderItem> mutableItems = new ArrayList<>(List.of(
                new OrderItem(new Sku("NIKE-DUNK-LOW-US9"), Money.twd(3200), new Quantity(2))));
        Order order = placedOrder(mutableItems);

        // (一)訂單身上唯一收得下外部輸入的方法,就是改狀態那一個。
        List<String> otherMutators = new ArrayList<>();
        for (Method method : Order.class.getDeclaredMethods()) {
            boolean isInstanceApi = Modifier.isPublic(method.getModifiers())
                    && !Modifier.isStatic(method.getModifiers());
            if (isInstanceApi
                    && method.getParameterCount() > 0
                    && !THE_ONLY_ALLOWED_MUTATOR.equals(method.getName())) {
                otherMutators.add(method.getName());
            }
        }
        assertThat(otherMutators)
                .as("訂單成立後只允許改狀態,不該有第二個改得動它的方法")
                .isEmpty();

        // (二)拿得到的品項清單改不動它。
        assertThatThrownBy(() -> order.items().clear())
                .isInstanceOf(UnsupportedOperationException.class);

        // (三)交出去以後,呼叫方手上那份清單再怎麼動都影響不到訂單。
        mutableItems.add(new OrderItem(new Sku("NIKE-AIR-FORCE1-US9"), Money.twd(4500), new Quantity(1)));
        assertThat(order.items()).hasSize(1);
        // 6520 是 §2 G1 算過的字面值 —— 訂單的總價沒有跟著外面那份清單變。
        assertThat(order.totalAmount()).isEqualTo(Money.twd(6520));
    }
}
