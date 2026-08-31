-- InsightX AI — Intermediate SQL Analytics

-- Business Q1: Which products generate the most revenue?
SELECT
    p.category,
    p.brand,
    SUM(o.revenue) AS total_revenue,
    COUNT(o.order_id) AS num_orders
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'Delivered'
GROUP BY p.category, p.brand
ORDER BY total_revenue DESC
LIMIT 10;

-- Order value tiers using CASE
SELECT
    order_id,
    revenue,
    CASE
        WHEN revenue >= 5000 THEN 'High Value'
        WHEN revenue >= 1500 THEN 'Medium Value'
        ELSE 'Low Value'
    END AS order_tier
FROM orders
WHERE status = 'Delivered';

-- Customers spending above the average order value (subquery)
SELECT customer_id, order_id, revenue
FROM orders
WHERE revenue > (SELECT AVG(revenue) FROM orders WHERE status = 'Delivered')
AND status = 'Delivered'
ORDER BY revenue DESC
LIMIT 20;

-- Business Q3: Which cities generate the most profit? (CTE)
WITH city_orders AS (
    SELECT c.city, o.revenue, p.cost, o.quantity
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN products p ON o.product_id = p.product_id
    WHERE o.status = 'Delivered'
)
SELECT
    city,
    SUM(revenue) AS total_revenue,
    SUM(cost * quantity) AS total_cost,
    SUM(revenue) - SUM(cost * quantity) AS total_profit
FROM city_orders
GROUP BY city
ORDER BY total_profit DESC;