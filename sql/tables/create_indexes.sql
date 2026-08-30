-- Indexes on foreign key columns speed up JOINs, which we rely on heavily
-- in Phase 7's SQL analytics work.

CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_product_id ON orders(product_id);
CREATE INDEX idx_reviews_customer_id ON reviews(customer_id);
CREATE INDEX idx_reviews_order_id ON reviews(order_id);
CREATE INDEX idx_marketing_customer_id ON marketing_campaigns(customer_id);