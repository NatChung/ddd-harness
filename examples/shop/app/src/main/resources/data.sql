-- 由 harness 提供,實作者不需要修改這個檔案。
--
-- customers 這張表刻意「不是」任何 Aggregate 的一部分:
-- 訂單只持有 CustomerId,顧客姓名住在這裡。列表頁要顯示姓名時,
-- 讀取側必須自己來這裡取 —— 這是第 6 課 CQRS 那個缺口的實體版本。

CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(64) PRIMARY KEY,
    name        VARCHAR(255) NOT NULL
);

DELETE FROM customers;
INSERT INTO customers (customer_id, name) VALUES ('C-001', 'Alice');
INSERT INTO customers (customer_id, name) VALUES ('C-002', 'Bob');
