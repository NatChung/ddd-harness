package com.shop.adapter.persistence;

import com.shop.domain.ordering.CustomerName;
import com.shop.domain.ordering.Money;
import com.shop.domain.ordering.Order;
import com.shop.domain.ordering.OrderId;
import com.shop.domain.ordering.OrderItem;
import com.shop.domain.ordering.OrderStatus;
import com.shop.domain.ordering.Quantity;
import com.shop.domain.ordering.Sku;
import com.shop.usecase.ordering.OrderRepository;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.List;

/** {@link OrderRepository} 這個 port 的 JPA 實作 —— 負責領域物件與落地形狀之間的對譯。 */
@Repository
public class JpaOrderRepository implements OrderRepository {

    private final SpringDataOrderRepository jpa;

    public JpaOrderRepository(SpringDataOrderRepository jpa) {
        this.jpa = jpa;
    }

    @Override
    public void save(Order order) {
        List<OrderItemEmbeddable> rows = new ArrayList<>();
        for (OrderItem item : order.items()) {
            rows.add(new OrderItemEmbeddable(
                    item.sku().value(),
                    item.unitPrice().amount(),
                    item.quantity().value()));
        }
        jpa.save(new OrderJpaEntity(
                order.orderId().value(),
                order.customerName().value(),
                order.shippingFee().amount(),
                order.placedAt(),
                order.status().name(),
                rows));
    }

    @Override
    public List<Order> findAll() {
        List<Order> orders = new ArrayList<>();
        for (OrderJpaEntity entity : jpa.findAll()) {
            orders.add(toDomain(entity));
        }
        return orders;
    }

    private static Order toDomain(OrderJpaEntity entity) {
        List<OrderItem> items = new ArrayList<>();
        for (OrderItemEmbeddable row : entity.items()) {
            items.add(new OrderItem(
                    new Sku(row.sku()),
                    Money.twd(row.unitPrice()),
                    new Quantity(row.quantity())));
        }
        return Order.restore(
                OrderId.of(entity.orderId()),
                new CustomerName(entity.customerName()),
                items,
                Money.twd(entity.shippingFee()),
                entity.placedAt(),
                OrderStatus.valueOf(entity.status()));
    }
}
