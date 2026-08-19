package com.shop.usecase.ordering;

import com.shop.domain.ordering.CustomerName;
import com.shop.domain.ordering.Money;
import com.shop.domain.ordering.Order;
import com.shop.domain.ordering.OrderId;
import com.shop.domain.ordering.OrderItem;
import com.shop.domain.ordering.Quantity;
import com.shop.domain.ordering.Sku;

import java.time.Clock;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.List;

/**
 * 下單 —— 把 {@link PlaceOrderCommand} 變成一張訂單並落地。
 *
 * <p>所有的業務規則都守在訂單聚合根裡(§3 C2–C5),這裡只做組裝與落地。
 */
public final class PlaceOrder {

    /** 分月與成立日期一律用 Asia/Taipei(§6 A-11)。 */
    private static final ZoneId TAIPEI = ZoneId.of("Asia/Taipei");

    private final OrderRepository orders;
    private final Clock clock;

    public PlaceOrder(OrderRepository orders, Clock clock) {
        this.orders = orders;
        this.clock = clock;
    }

    public Order place(PlaceOrderCommand command) {
        List<OrderItem> items = new ArrayList<>();
        for (PlaceOrderCommand.Line line : itemsOf(command)) {
            items.add(new OrderItem(
                    new Sku(line.sku()),
                    Money.of(line.currency(), line.unitPrice()),
                    Quantity.of(line.quantity())));
        }

        Order order = Order.place(
                OrderId.newId(),
                new CustomerName(command.customer()),
                items,
                noShippingFee(),
                LocalDate.now(clock.withZone(TAIPEI)));

        orders.save(order);
        return order;
    }

    private static List<PlaceOrderCommand.Line> itemsOf(PlaceOrderCommand command) {
        return command.items() == null ? List.of() : command.items();
    }

    /**
     * 這份 wire 合約沒有運費欄位(見 ASSUMPTIONS),呼叫方送不進運費,故一律以 TWD 0 帶入。
     * 訂單聚合根裡的 C2 公式本身仍然含運費那一項。
     */
    private static Money noShippingFee() {
        return Money.twd(0);
    }
}
