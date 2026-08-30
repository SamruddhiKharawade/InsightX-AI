-- InsightX AI — Core schema
-- Run this connected to the 'insightx' database (not 'postgres').
-- Order matters: dimension tables first, then fact tables that reference them.

CREATE TABLE customers (
    customer_id      INTEGER PRIMARY KEY,
    customer_name    VARCHAR(100),
    age              INTEGER,
    gender           VARCHAR(20),
    city             VARCHAR(50),
    signup_date      DATE,
    customer_segment VARCHAR(20),
    tenure_days      INTEGER
);

CREATE TABLE products (
    product_id     INTEGER PRIMARY KEY,
    category       VARCHAR(50),
    brand          VARCHAR(50),
    cost           NUMERIC(10,2),
    selling_price  NUMERIC(10,2),
    inventory      INTEGER,
    profit_margin  NUMERIC(10,2),
    margin_pct     NUMERIC(5,3)
);

CREATE TABLE orders (
    order_id        INTEGER PRIMARY KEY,
    customer_id     INTEGER REFERENCES customers(customer_id),
    product_id      INTEGER REFERENCES products(product_id),
    order_date      DATE,
    quantity        INTEGER,
    price           NUMERIC(10,2),
    discount        NUMERIC(4,2),
    payment_method  VARCHAR(30),
    delivery_time   INTEGER,
    status          VARCHAR(20),
    revenue         NUMERIC(10,2)
);

CREATE TABLE reviews (
    review_id    INTEGER PRIMARY KEY,
    customer_id  INTEGER REFERENCES customers(customer_id),
    order_id     INTEGER REFERENCES orders(order_id),
    rating       INTEGER,
    review_text  TEXT,
    review_date  DATE
);

CREATE TABLE marketing_campaigns (
    campaign_id  INTEGER PRIMARY KEY,
    customer_id  INTEGER REFERENCES customers(customer_id),
    campaign     VARCHAR(50),
    spend        NUMERIC(10,2),
    clicks       INTEGER,
    conversion   INTEGER
);