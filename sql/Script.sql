
-- 1. Общая выручка и ключевые метрики


-- Общая выручка и прибыль
SELECT 
    ROUND(SUM(payment_value), 2) AS total_revenue,
    ROUND(SUM(CASE WHEN order_status = 'delivered' THEN payment_value ELSE 0 END), 2) AS delivered_revenue,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT CASE WHEN o.order_status = 'delivered' THEN o.order_id END) AS delivered_orders
FROM olist_order_payments_dataset p
JOIN olist_orders_dataset o ON p.order_id = o.order_id;

-- 2. Топ-10 категорий по выручке

SELECT TOP 10
    COALESCE(pt.product_category_name_english, p.product_category_name) AS category,
    ROUND(SUM(oi.price * oi.order_item_id), 2) AS total_revenue,   -- исправил на сумму по количеству
    COUNT(*) AS items_sold
FROM olist_order_items_dataset oi
JOIN olist_products_dataset p ON oi.product_id = p.product_id
LEFT JOIN product_category_name_translation pt ON p.product_category_name = pt.product_category_name
GROUP BY COALESCE(pt.product_category_name_english, p.product_category_name)
ORDER BY total_revenue DESC;


-- 3. Ключевые бизнес-метрики
-- Average Order Value (AOV)
SELECT 
    ROUND(AVG(order_total), 2) AS aov
FROM (
    SELECT order_id, SUM(payment_value) AS order_total
    FROM olist_order_payments_dataset
    GROUP BY order_id
) t;

-- Среднее время задержки доставки 
SELECT 
    ROUND(AVG(CAST(DATEDIFF(DAY, order_estimated_delivery_date, order_delivered_customer_date) AS FLOAT)), 2) AS avg_delay_days
FROM olist_orders_dataset
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL
  AND order_estimated_delivery_date IS NOT NULL
  AND order_delivered_customer_date > order_estimated_delivery_date;

-- Repeat Rate
WITH customer_orders AS (
    SELECT 
        customer_id,
        COUNT(DISTINCT order_id) AS order_count
    FROM olist_orders_dataset
    GROUP BY customer_id
)
SELECT 
    COUNT(DISTINCT customer_id) AS total_customers,
    COUNT(CASE WHEN order_count > 1 THEN customer_id END) AS repeat_customers,
    ROUND(100.0 * COUNT(CASE WHEN order_count > 1 THEN customer_id END) * 1.0 / COUNT(DISTINCT customer_id), 2) AS repeat_rate_percent
FROM customer_orders;

-- Распределение оценок отзывов
SELECT 
    review_score,
    COUNT(*) AS review_count,
    ROUND(100.0 * COUNT(*) * 1.0 / SUM(COUNT(*)) OVER(), 2) AS percentage
FROM olist_order_reviews_dataset
GROUP BY review_score
ORDER BY review_score;

-- 4. География продаж

SELECT TOP 10
    c.customer_state,
    ROUND(SUM(p.payment_value), 2) AS total_revenue,
    COUNT(DISTINCT o.order_id) AS orders_count
FROM olist_customers_dataset c
JOIN olist_orders_dataset o ON c.customer_id = o.customer_id
JOIN olist_order_payments_dataset p ON o.order_id = p.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY total_revenue DESC;