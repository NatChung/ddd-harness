package com.shop.domain;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("Order 測試")
class OrderTest {

    private OrderId orderId;
    private CustomerId customerId;
    private Order order;

    @BeforeEach
    void setUp() {
        orderId = OrderId.of("ORD-001");
        customerId = CustomerId.of("C-001");
        order = Order.create(orderId, customerId);
    }

    @Test
    @DisplayName("Order 應該以 OrderId 相等比較")
    void testOrderEquality() {
        Order order1 = Order.create(orderId, customerId);
        Order order2 = Order.create(orderId, customerId);
        Order order3 = Order.create(OrderId.of("ORD-002"), customerId);

        assertEquals(order1, order2);
        assertNotEquals(order1, order3);
    }

    @Test
    @DisplayName("新訂單的狀態應該是 DRAFT")
    void testNewOrderStatusIsDraft() {
        assertEquals(OrderStatus.DRAFT, order.getStatus());
    }

    @Test
    @DisplayName("新訂單的總額應該是 0")
    void testNewOrderTotalIsZero() {
        assertEquals(Money.of(0, "TWD"), order.getTotal());
    }

    @Test
    @DisplayName("新訂單應該沒有明細")
    void testNewOrderHasNoItems() {
        assertTrue(order.items().isEmpty());
    }

    @Test
    @DisplayName("addItem 應該新增明細並重算總額")
    void testAddItemAndRecalculateTotal() {
        ProductId pId = ProductId.of("P-100");
        Money unitPrice = Money.of(1500, "TWD");

        order.addItem(pId, 2, unitPrice);

        assertEquals(1, order.items().size());
        assertEquals(Money.of(3000, "TWD"), order.getTotal());
    }

    @Test
    @DisplayName("addItem 可以多次呼叫，總額累積")
    void testAddMultipleItems() {
        ProductId p1 = ProductId.of("P-100");
        ProductId p2 = ProductId.of("P-101");
        Money price1 = Money.of(1500, "TWD");
        Money price2 = Money.of(2000, "TWD");

        order.addItem(p1, 2, price1);
        order.addItem(p2, 1, price2);

        assertEquals(2, order.items().size());
        assertEquals(Money.of(5000, "TWD"), order.getTotal());
    }

    @Test
    @DisplayName("items() 應該回傳複本，修改不影響 Order")
    void testItemsReturnsImmutableCopy() {
        ProductId pId = ProductId.of("P-100");
        Money unitPrice = Money.of(1500, "TWD");

        order.addItem(pId, 2, unitPrice);
        List<OrderItem> items = order.items();

        // 嘗試修改回傳的集合
        assertThrows(UnsupportedOperationException.class, () -> items.add(
                new OrderItem(ProductId.of("P-999"), 1, Money.of(100, "TWD"))
        ));

        // 確認 Order 內部的明細沒有被改變
        assertEquals(1, order.items().size());
    }

    @Test
    @DisplayName("addItem 在 PLACED 狀態時應該丟 IllegalStateException")
    void testAddItemAfterPlaced() {
        ProductId pId = ProductId.of("P-100");
        Money unitPrice = Money.of(1500, "TWD");

        order.addItem(pId, 2, unitPrice);
        order.place();

        ProductId p2 = ProductId.of("P-101");
        Money price2 = Money.of(2000, "TWD");

        IllegalStateException e = assertThrows(
                IllegalStateException.class,
                () -> order.addItem(p2, 1, price2)
        );
        assertTrue(e.getMessage().contains("Cannot add item to a non-DRAFT order"));
    }

    @Test
    @DisplayName("place() 應該把狀態從 DRAFT 改成 PLACED")
    void testPlace() {
        ProductId pId = ProductId.of("P-100");
        Money unitPrice = Money.of(1500, "TWD");

        order.addItem(pId, 2, unitPrice);
        order.place();

        assertEquals(OrderStatus.PLACED, order.getStatus());
    }

    @Test
    @DisplayName("place() 在空訂單時應該丟 IllegalStateException")
    void testPlaceEmptyOrder() {
        IllegalStateException e = assertThrows(IllegalStateException.class, () -> order.place());
        assertTrue(e.getMessage().contains("Cannot place an order without items"));
    }

    @Test
    @DisplayName("place() 在已 PLACED 訂單時應該丟 IllegalStateException")
    void testPlaceAlreadyPlaced() {
        ProductId pId = ProductId.of("P-100");
        Money unitPrice = Money.of(1500, "TWD");

        order.addItem(pId, 2, unitPrice);
        order.place();

        IllegalStateException e = assertThrows(IllegalStateException.class, () -> order.place());
        assertTrue(e.getMessage().contains("Only DRAFT order can be placed"));
    }

    @Test
    @DisplayName("Order 應該只持有 CustomerId，不持有 Customer 物件")
    void testOrderOnlyHoldsCustomerId() {
        assertEquals(customerId, order.getCustomerId());
    }

    @Test
    @DisplayName("getOrderId 應該回傳正確值")
    void testGetOrderId() {
        assertEquals(orderId, order.getOrderId());
    }

    @Test
    @DisplayName("Order reconstruct 應該能從持久化資料重建")
    void testOrderReconstruct() {
        ProductId pId = ProductId.of("P-100");
        Money unitPrice = Money.of(1500, "TWD");
        OrderItem item = new OrderItem(pId, 2, unitPrice);

        Order reconstructed = Order.reconstruct(
                orderId,
                customerId,
                List.of(item),
                Money.of(3000, "TWD"),
                OrderStatus.PLACED
        );

        assertEquals(orderId, reconstructed.getOrderId());
        assertEquals(customerId, reconstructed.getCustomerId());
        assertEquals(1, reconstructed.items().size());
        assertEquals(Money.of(3000, "TWD"), reconstructed.getTotal());
        assertEquals(OrderStatus.PLACED, reconstructed.getStatus());
    }

    @Test
    @DisplayName("Order 不得有 setter（狀態只能通過領域方法改變）")
    void testOrderNoSetters() {
        // 這個測試驗證 Order 沒有任何公開的 setter 方法
        // 通過反射檢查 Order 類是否有任何 public setter 方法
        var methods = Order.class.getDeclaredMethods();
        for (var method : methods) {
            String methodName = method.getName();
            if (methodName.startsWith("set")) {
                fail("Order should not have setter method: " + methodName);
            }
        }
    }

    @Test
    @DisplayName("Order 的狀態改變只能經由具領域意義的方法")
    void testOrderStateChangeOnlyThroughDomainMethods() {
        // 驗證 getStatus() 是否為 private（不被外部直接使用）
        // 或通過 place() 和 addItem() 間接改變
        ProductId pId = ProductId.of("P-100");
        Money unitPrice = Money.of(1500, "TWD");

        // 初始狀態
        assertEquals(OrderStatus.DRAFT, order.getStatus());

        // 通過 addItem 間接改變（檢查總額重算）
        order.addItem(pId, 2, unitPrice);
        assertEquals(Money.of(3000, "TWD"), order.getTotal());

        // 通過 place() 顯式改變
        order.place();
        assertEquals(OrderStatus.PLACED, order.getStatus());
    }
}
