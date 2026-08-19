package com.shop.adapter.web;

import com.shop.domain.ordering.Order;
import com.shop.usecase.ordering.ListOrders;
import com.shop.usecase.ordering.PlaceOrder;
import com.shop.usecase.ordering.PlaceOrderCommand;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.List;

/** 下單與訂單列表的 HTTP 入口。這一層只做對譯,沒有任何業務規則。 */
@RestController
public class OrderController {

    private final PlaceOrder placeOrder;
    private final ListOrders listOrders;

    public OrderController(PlaceOrder placeOrder, ListOrders listOrders) {
        this.placeOrder = placeOrder;
        this.listOrders = listOrders;
    }

    @PostMapping("/orders")
    public ResponseEntity<OrderResponse> place(@RequestBody PlaceOrderRequest request) {
        Order order = placeOrder.place(toCommand(request));
        return ResponseEntity.status(HttpStatus.CREATED).body(OrderResponse.from(order));
    }

    @GetMapping("/orders")
    public List<OrderListRow> list() {
        List<OrderListRow> rows = new ArrayList<>();
        for (Order order : listOrders.all()) {
            rows.add(OrderListRow.from(order));
        }
        return rows;
    }

    private static PlaceOrderCommand toCommand(PlaceOrderRequest request) {
        List<PlaceOrderCommand.Line> lines = new ArrayList<>();
        if (request.items() != null) {
            for (PlaceOrderRequest.Item item : request.items()) {
                lines.add(new PlaceOrderCommand.Line(
                        item.sku(), item.quantity(), item.unitPrice(), item.currency()));
            }
        }
        return new PlaceOrderCommand(request.customer(), lines);
    }
}
