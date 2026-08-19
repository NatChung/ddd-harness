package com.shop.adapter.config;

import com.shop.usecase.ordering.ListOrders;
import com.shop.usecase.ordering.OrderRepository;
import com.shop.usecase.ordering.PlaceOrder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Clock;

/**
 * 把 usecase 接上框架的地方。
 *
 * <p>usecase 層不得認識 Spring(機械檢查第 2 條),所以那幾個 class 身上沒有任何註解,
 * 由這個 adapter 層的設定檔把它們組起來。
 */
@Configuration
public class OrderingConfiguration {

    @Bean
    public Clock clock() {
        return Clock.systemDefaultZone();
    }

    @Bean
    public PlaceOrder placeOrder(OrderRepository orders, Clock clock) {
        return new PlaceOrder(orders, clock);
    }

    @Bean
    public ListOrders listOrders(OrderRepository orders) {
        return new ListOrders(orders);
    }
}
