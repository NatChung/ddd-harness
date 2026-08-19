/*
 * ⚠️ 受測品(ADR 0006 §6):骨架是餵給第四幕 agent 的輸入,改了它後續的跑就不能跟
 *    先前比 —— 跟 tools/harness/interview-prompt.md、act1/ 三份、run_act2.sh 的
 *    heredoc 是同一種性質。每跑在 run 目錄留 blob 雜湊,寫報告前先 diff。
 *    洩題面清單見 .scratch/ddd-harness/10-PREDICTION.md。
 */
package com.shop;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * 由 harness 提供,實作者不需要修改這個檔案。
 *
 * 它存在的唯一理由是讓驗收套件有東西可以啟動 —— 驗收打在 HTTP 層,
 * 所以它必須先能開得起一個真的 web 應用程式。
 *
 * 生成的兩支驗收寫死 {@code classes = com.shop.Application.class},
 * 所以 base package 是 com.shop —— 那不是這份規格宣告的,是生成器寫死的。
 */
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
