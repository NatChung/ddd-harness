package com.shop.usecase.ordering;

import java.util.List;

/**
 * 下單的輸入 —— 只帶原始值,不帶任何 wire / 框架型別。
 *
 * <p>{@code unitPrice} 由呼叫方帶入,這是 §6 A-7 的權宜作法(商品主檔 B-1 是阻斷級規格沉默),
 * <b>不是最終設計</b>。
 */
public record PlaceOrderCommand(String customer, List<Line> items) {

    /** 一列下單品項。 */
    public record Line(String sku, Integer quantity, Long unitPrice, String currency) {
    }
}
