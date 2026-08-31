-- InsightX AI — Advanced SQL Analytics (Window Functions)

-- Business Q2: Which customers have the highest lifetime value?
SELECT
    customer_id,
    total_spent,
    RANK() OVER (ORDER BY total_spent DESC) AS spend_rank
FROM (
    SELECT customer_id, SUM(revenue) AS total_spent
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY customer_id
) customer_totals
ORDER BY spend_rank
LIMIT 20;

-- Running total of daily revenue
SELECT
    order_date,
    SUM(revenue) AS daily_revenue,
    SUM(SUM(revenue)) OVER (ORDER BY order_date) AS running_total
FROM orders
WHERE status = 'Delivered'
GROUP BY order_date
ORDER BY order_date;

-- 7-day rolling average of daily revenue
SELECT
    order_date,
    SUM(revenue) AS daily_revenue,
    ROUND(AVG(SUM(revenue)) OVER (
        ORDER BY order_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_7day_avg
FROM orders
WHERE status = 'Delivered'
GROUP BY order_date
ORDER BY order_date;

-- Business Q4: Which products have declining sales? (LAG month-over-month)
WITH monthly_product_sales AS (
    SELECT
        product_id,
        DATE_TRUNC('month', order_date) AS month,
        SUM(revenue) AS monthly_revenue
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY product_id, DATE_TRUNC('month', order_date)
)
SELECT
    product_id,
    month,
    monthly_revenue,
    LAG(monthly_revenue) OVER (PARTITION BY product_id ORDER BY month) AS prev_month_revenue,
    monthly_revenue - LAG(monthly_revenue) OVER (PARTITION BY product_id ORDER BY month) AS change
FROM monthly_product_sales
ORDER BY product_id, month;

-- Business Q5: Monthly customer retention
WITH customer_months AS (
    SELECT DISTINCT customer_id, DATE_TRUNC('month', order_date) AS order_month
    FROM orders
    WHERE status = 'Delivered'
),
retention AS (
    SELECT
        curr.order_month,
        COUNT(DISTINCT curr.customer_id) AS active_customers,
        COUNT(DISTINCT prev.customer_id) AS retained_from_prev_month
    FROM customer_months curr
    LEFT JOIN customer_months prev
        ON curr.customer_id = prev.customer_id
        AND prev.order_month = curr.order_month - INTERVAL '1 month'
    GROUP BY curr.order_month
)
SELECT
    order_month,
    active_customers,
    retained_from_prev_month,
    ROUND(100.0 * retained_from_prev_month / NULLIF(active_customers, 0), 1) AS retention_pct
FROM retention
ORDER BY order_month;

-- Business Q6: Which customers are at risk of churn? (rule-based baseline)
WITH last_order AS (
    SELECT customer_id, MAX(order_date) AS last_order_date
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY customer_id
),
reference AS (
    SELECT MAX(order_date) AS dataset_max_date FROM orders
)
SELECT
    l.customer_id,
    l.last_order_date,
    (r.dataset_max_date - l.last_order_date) AS days_since_last_order,
    CASE
        WHEN (r.dataset_max_date - l.last_order_date) > 120 THEN 'High Risk'
        WHEN (r.dataset_max_date - l.last_order_date) > 60 THEN 'Medium Risk'
        ELSE 'Low Risk'
    END AS churn_risk
FROM last_order l
CROSS JOIN reference r
ORDER BY days_since_last_order DESC;

-- Business Q7: Which marketing campaigns have the highest ROI?
SELECT
    m.campaign,
    COUNT(*) AS total_touches,
    SUM(m.spend) AS total_spend,
    SUM(m.conversion) AS total_conversions,
    SUM(CASE WHEN m.conversion = 1 THEN o.revenue ELSE 0 END) AS attributed_revenue,
    ROUND(
        (SUM(CASE WHEN m.conversion = 1 THEN o.revenue ELSE 0 END) - SUM(m.spend))
        / NULLIF(SUM(m.spend), 0) * 100, 1
    ) AS roi_pct
FROM marketing_campaigns m
LEFT JOIN orders o
    ON m.customer_id = o.customer_id
    AND o.status = 'Delivered'
GROUP BY m.campaign
ORDER BY roi_pct DESC;