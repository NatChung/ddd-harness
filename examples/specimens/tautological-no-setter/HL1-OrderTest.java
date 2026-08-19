package com.shop.domain;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("Order - Aggregate Root")
class OrderTest {

    @Test
    @DisplayName("建立新訂單，初始狀態為 DRAFT")
    void testConstructWithDraftStatus() {
        OrderId orderId = new OrderId("ORD-001");
        CustomerId customerId = new CustomerId("C-001");
        Order order = new Order(orderId, customerId);
        assertEquals(orderId, order.getOrderId());
        assertEquals(customerId, order.getCustomerId());
        assertEquals(OrderStatus.DRAFT, order.getStatus());
        assertTrue(order.items().isEmpty());
    }

    @Test
    @DisplayName("訂單識別為 null 時拋 NullPointerException")
    void testConstructWithNullOrderId() {
        CustomerId customerId = new CustomerId("C-001");
        assertThrows(NullPointerException.class, () -> new Order(null, customerId));
    }

    @Test
    @DisplayName("顧客識別為 null 時拋 NullPointerException")
    void testConstructWithNullCustomerId() {
        OrderId orderId = new OrderId("ORD-001");
        assertThrows(NullPointerException.class, () -> new Order(orderId, null));
    }

    @Test
    @DisplayName("items() 回傳複本，修改副本不影響原本")
    void testItemsReturnsCopy() {
        Order order = new Order(new OrderId("ORD-001"), new CustomerId("C-001"));
        ProductId productId = new ProductId("P-100");
        Money unitPrice = new Money(1500, "TWD");
        order.addItem(productId, 2, unitPrice);

        // 取得複本並嘗試修改
        List<OrderItem> itemsCopy = order.items();
        assertFalse(itemsCopy.isEmpty());

        // 修改副本不應該影響原本
        try {
            itemsCopy.add(new OrderItem(new ProductId("P-200"), 1, new Money(2000, "TWD")));
            fail("Should not be able to modify returned list");
        } catch (UnsupportedOperationException e) {
            // 預期的行為 - List.copyOf 回傳不可修改的清單
        }
    }

    @Test
    @DisplayName("空訂單呼叫 total() 拋 IllegalStateException")
    void testTotalWithEmptyOrder() {
        Order order = new Order(new OrderId("ORD-001"), new CustomerId("C-001"));
        assertThrows(IllegalStateException.class, order::total);
    }

    @Test
    @DisplayName("單一明細的訂單計算總額")
    void testTotalWithSingleItem() {
        Order order = new Order(new OrderId("ORD-001"), new CustomerId("C-001"));
        ProductId productId = new ProductId("P-100");
        Money unitPrice = new Money(1500, "TWD");
        order.addItem(productId, 2, unitPrice);

        Money total = order.total();
        assertEquals(new Money(3000, "TWD"), total);
    }

    @Test
    @DisplayName("多個明細的訂單計算總額")
    void testTotalWithMultipleItems() {
        Order order = new Order(new OrderId("ORD-001"), new CustomerId("C-001"));
        order.addItem(new ProductId("P-100"), 2, new Money(1500, "TWD"));
        order.addItem(new ProductId("P-101"), 3, new Money(2000, "TWD"));

        Money total = order.total();
        assertEquals(new Money(9000, "TWD"), total);
    }

    @Test
    @DisplayName("新增明細到 DRAFT 訂單")
    void testAddItemToDraftOrder() {
        Order order = new Order(new OrderId("ORD-001"), new CustomerId("C-001"));
        ProductId productId = new ProductId("P-100");
        Money unitPrice = new Money(1500, "TWD");

        order.addItem(productId, 2, unitPrice);
        assertEquals(1, order.items().size());
        assertEquals(new Money(3000, "TWD"), order.total());
    }

    @Test
    @DisplayName("新增明細到 PLACED 訂單拋 IllegalStateException")
    void testAddItemToPlacedOrderThrows() {
        Order order = new Order(new OrderId("ORD-001"), new CustomerId("C-001"));
        order.addItem(new ProductId("P-100"), 2, new Money(1500, "TWD"));
        order.place();

        assertThrows(IllegalStateException.class, () ->
                order.addItem(new ProductId("P-101"), 1, new Money(2000, "TWD"))
        );
    }

    @Test
    @DisplayName("新增不同幣別的明細拋 IllegalArgumentException")
    void testAddItemWithDifferentCurrencyThrows() {
        Order order = new Order(new OrderId("ORD-001"), new CustomerId("C-001"));
        order.addItem(new ProductId("P-100"), 2, new Money(1500, "TWD"));

        assertThrows(IllegalArgumentException.class, () ->
                order.addItem(new ProductId("P-101"), 1, new Money(2000, "USD"))
        );
    }

    @Test
    @DisplayName("驗證失敗時訂單狀態不變（原子性）")
    void testAddItemAtomicity() {
        Order order = new Order(new OrderId("ORD-001"), new CustomerId("C-001"));
        order.addItem(new ProductId("P-100"), 2, new Money(1500, "TWD"));
        int initialSize = order.items().size();

        // 嘗試新增不同幣別的明細
        assertThrows(IllegalArgumentException.class, () ->
                order.addItem(new ProductId("P-101"), 1, new Money(2000, "USD"))
        );

        // 驗證明細清單大小未改變
        assertEquals(initialSize, order.items().size());
    }

    @Test
    @DisplayName("下單：把訂單從 DRAFT 變成 PLACED")
    void testPlace() {
        Order order = new Order(new OrderId("ORD-001"), new CustomerId("C-001"));
        order.addItem(new ProductId("P-100"), 2, new Money(1500, "TWD"));

        assertEquals(OrderStatus.DRAFT, order.getStatus());
        order.place();
        assertEquals(OrderStatus.PLACED, order.getStatus());
    }

    @Test
    @DisplayName("已成立的訂單重複下單拋 IllegalStateException")
    void testPlaceAlreadyPlacedOrderThrows() {
        Order order = new Order(new OrderId("ORD-001"), new CustomerId("C-001"));
        order.addItem(new ProductId("P-100"), 2, new Money(1500, "TWD"));
        order.place();

        assertThrows(IllegalStateException.class, order::place);
    }

    @Test
    @DisplayName("addItem 的商品識別為 null 拋 NullPointerException")
    void testAddItemWithNullProductId() {
        Order order = new Order(new OrderId("ORD-001"), new CustomerId("C-001"));
        assertThrows(NullPointerException.class, () ->
                order.addItem(null, 2, new Money(1500, "TWD"))
        );
    }

    @Test
    @DisplayName("addItem 的單價為 null 拋 NullPointerException")
    void testAddItemWithNullUnitPrice() {
        Order order = new Order(new OrderId("ORD-001"), new CustomerId("C-001"));
        assertThrows(NullPointerException.class, () ->
                order.addItem(new ProductId("P-100"), 2, null)
        );
    }

    @Test
    @DisplayName("addItem 的數量 <= 0 拋 IllegalArgumentException")
    void testAddItemWithInvalidQuantity() {
        Order order = new Order(new OrderId("ORD-001"), new CustomerId("C-001"));
        Money unitPrice = new Money(1500, "TWD");
        ProductId productId = new ProductId("P-100");

        assertThrows(IllegalArgumentException.class, () ->
                order.addItem(productId, 0, unitPrice)
        );
        assertThrows(IllegalArgumentException.class, () ->
                order.addItem(productId, -1, unitPrice)
        );
    }

    @Test
    @DisplayName("訂單無 setter，狀態改變只能經由具領域意義的方法")
    void testNoSetters() {
        Order order = new Order(new OrderId("ORD-001"), new CustomerId("C-001"));

        // 驗證沒有 setOrderId、setCustomerId、setStatus 等 setter
        // 只能透過 addItem 和 place 等具領域意義的方法改變狀態
        assertFalse(hasSetterMethod(order.getClass(), "setStatus"));
        assertFalse(hasSetterMethod(order.getClass(), "setOrderId"));
        assertFalse(hasSetterMethod(order.getClass(), "setCustomerId"));
    }

    @Test
    @DisplayName("新增多個明細，順序保持")
    void testAddMultipleItemsPreserveOrder() {
        Order order = new Order(new OrderId("ORD-001"), new CustomerId("C-001"));
        order.addItem(new ProductId("P-100"), 1, new Money(1000, "TWD"));
        order.addItem(new ProductId("P-101"), 2, new Money(2000, "TWD"));
        order.addItem(new ProductId("P-102"), 3, new Money(3000, "TWD"));

        List<OrderItem> items = order.items();
        assertEquals(3, items.size());
        assertEquals(new ProductId("P-100"), items.get(0).getProductId());
        assertEquals(new ProductId("P-101"), items.get(1).getProductId());
        assertEquals(new ProductId("P-102"), items.get(2).getProductId());
    }

    /**
     * 檢查類別是否存在特定方法（用於驗證沒有 setter）。
     */
    private boolean hasSetterMethod(Class<?> clazz, String methodName) {
        try {
            clazz.getDeclaredMethod(methodName, Object.class);
            return true;
        } catch (NoSuchMethodException e) {
            return false;
        }
    }
}
