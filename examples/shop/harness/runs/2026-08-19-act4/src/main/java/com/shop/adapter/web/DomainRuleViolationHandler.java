package com.shop.adapter.web;

import com.shop.domain.ordering.DomainRuleViolation;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.Map;

/**
 * 把領域規則的拒絕翻成 HTTP —— 回 400,body 照 §1.2〈錯誤共用格式〉。
 *
 * <p>領域層不認識 HTTP,所以這個對譯只能住在 adapter 層。
 */
@RestControllerAdvice
public class DomainRuleViolationHandler {

    @ExceptionHandler(DomainRuleViolation.class)
    public ResponseEntity<Map<String, Object>> handle(DomainRuleViolation violation) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of(
                "error", Map.of(
                        "code", violation.code(),
                        "message", String.valueOf(violation.getMessage()),
                        "details", Map.of())));
    }
}
