package com.shop;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * 由 harness 提供,實作者不需要修改這個檔案。
 *
 * 它存在的唯一理由是讓驗收套件有東西可以啟動 —— 驗收打在 HTTP 層,
 * 所以它必須先能開得起一個真的 web 應用程式。
 */
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
