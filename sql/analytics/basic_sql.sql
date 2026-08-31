-- InsightX AI — Basic SQL Analytics

-- Total revenue from delivered orders
SELECT SUM(revenue) AS total_revenue
FROM orders
WHERE status = 'Delivered';

-- Revenue and order count by payment method
SELECT
    payment_method,
    COUNT(*) AS num_orders,
    SUM(revenue) AS total_revenue,
    ROUND(AVG(revenue), 2) AS avg_order_value
FROM orders
WHERE status = 'Delivered'
GROUP BY payment_method
ORDER BY total_revenue DESC;

-- Payment methods used often enough to matter (HAVING filters groups)
SELECT payment_method, COUNT(*) AS num_orders
FROM orders
GROUP BY payment_method
HAVING COUNT(*) > 500
ORDER BY num_orders DESC;