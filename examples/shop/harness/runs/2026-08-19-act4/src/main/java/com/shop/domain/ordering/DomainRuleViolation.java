package com.shop.domain.ordering;

/**
 * 領域規則被違反 —— §3 的 precondition / invariant 擋下來的時候丟這個。
 *
 * <p>帶一個 {@code code},讓 adapter 層可以照 §1.2〈錯誤共用格式〉組出回應,
 * 而領域層不需要認識 HTTP。
 */
public class DomainRuleViolation extends RuntimeException {

    private final String code;

    public DomainRuleViolation(String code, String message) {
        super(message);
        this.code = code;
    }

    public String code() {
        return code;
    }
}
