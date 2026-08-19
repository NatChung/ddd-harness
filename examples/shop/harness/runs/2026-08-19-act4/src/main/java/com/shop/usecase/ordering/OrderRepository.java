package com.shop.usecase.ordering;

import com.shop.domain.ordering.Order;

import java.util.List;

/**
 * 訂單的儲存埠(port)。介面宣告在內層,實作在外層(adapter),
 * 所以 usecase 不認識任何持久化技術。
 */
public interface OrderRepository {

    /** 落地一張訂單。 */
    void save(Order order);

    /** 所有訂單 —— §1.2 E3「後台人員看所有訂單」。 */
    List<Order> findAll();
}
