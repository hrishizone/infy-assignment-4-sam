CREATE TABLE IF NOT EXISTS customer (
  customer_id VARCHAR(64) PRIMARY KEY,
  name        VARCHAR(128) NULL
);

CREATE TABLE IF NOT EXISTS account (
  account_id  VARCHAR(64) PRIMARY KEY,
  customer_id VARCHAR(64) NOT NULL,
  account_type VARCHAR(32) NULL,
  CONSTRAINT fk_account_customer
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transactions (
  transactions_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  account_id      VARCHAR(64) NOT NULL,
  amount          DECIMAL(12,2) NOT NULL,
  txn_time        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_tx_account
    FOREIGN KEY (account_id) REFERENCES account(account_id)
    ON DELETE CASCADE
);


INSERT INTO customer (customer_id, name) VALUES
  ('CUST1', 'Alice'),
  ('CUST2', 'Bob')
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO account (account_id, customer_id, account_type) VALUES
  ('ACC1', 'CUST1', 'SAVINGS'),
  ('ACC2', 'CUST1', 'CHECKING'),
  ('ACC3', 'CUST2', 'SAVINGS')
ON DUPLICATE KEY UPDATE account_type = VALUES(account_type);


INSERT INTO transactions (account_id, amount)
SELECT * FROM (
  SELECT 'ACC1' AS account_id, 100.50 AS amount UNION ALL
  SELECT 'ACC1', -20.00 UNION ALL
  SELECT 'ACC1', 10.00  UNION ALL
  SELECT 'ACC2', 500.00 UNION ALL
  SELECT 'ACC3', 40.00
) AS seed
WHERE NOT EXISTS (SELECT 1 FROM transactions LIMIT 1);
