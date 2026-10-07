-- Task 3(a): Order totals
-- NULL discounts are treated as 0%. Returned orders are included.
-- Output:
-- total_orders | total_revenue | avg_order_value
-- 180          | 99860.20      | 554.78

SELECT
    COUNT(*) AS total_orders,
    ROUND(SUM(
        o.quantity * p.price *
        (1 - COALESCE(o.discount_pct, 0) / 100.0)
    ), 2) AS total_revenue,
    ROUND(AVG(
        o.quantity * p.price *
        (1 - COALESCE(o.discount_pct, 0) / 100.0)
    ), 2) AS avg_order_value
FROM orders AS o
JOIN products AS p
    ON o.product_id = p.product_id;

-- Task 3(b): COUNT(*) vs COUNT(column)
-- COUNT(*) includes all rows; COUNT(rating) excludes NULL ratings.
-- Output:
-- total_orders | rated_orders | unrated_orders
-- 180          | 165          | 15

SELECT
    COUNT(*) AS total_orders,
    COUNT(rating) AS rated_orders,
    COUNT(*) - COUNT(rating) AS unrated_orders
FROM orders;

-- Task 3(c): Customers with zero orders using LEFT JOIN
-- COUNT(o.order_id) excludes the NULL produced for an unmatched customer.
-- Output:
-- customer_id | name
-- C045        | Vihaan

SELECT
    c.customer_id,
    c.name
FROM customers AS c
LEFT JOIN orders AS o
    ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
HAVING COUNT(o.order_id) = 0;


-- Task 3(c): Independent verification using NOT IN
-- orders.customer_id is NOT NULL, so the subquery cannot contain NULL.
-- Output:
-- customer_id | name
-- C045        | Vihaan

SELECT
    customer_id,
    name
FROM customers
WHERE customer_id NOT IN (
    SELECT DISTINCT customer_id
    FROM orders
);

-- Task 3(d): Cities with a return rate above 20%
-- returned = 1 identifies a returned order.
-- Output:
-- city      | total_orders | returned_orders | return_rate_pct
-- Jaipur    | 19           | 8               | 42.1
-- Lucknow   | 49           | 15              | 30.6
-- Bangalore | 33           | 8               | 24.2

SELECT
    c.city,
    COUNT(*) AS total_orders,
    SUM(o.returned) AS returned_orders,
    ROUND(
        100.0 * SUM(o.returned) / COUNT(*),
        1
    ) AS return_rate_pct
FROM orders AS o
JOIN customers AS c
    ON o.customer_id = c.customer_id
GROUP BY c.city
HAVING return_rate_pct > 20
ORDER BY return_rate_pct DESC;

-- Task 3(e): Top five customers by total spend
-- customer_id ASC gives a consistent order when total_spend is tied.
-- Output:
-- customer_id | name    | total_spend
-- C043        | Reyansh | 12920.00
-- C026        | Isha    | 8371.60
-- C008        | Meera   | 4564.60
-- C011        | Arjun   | 4111.00
-- C042        | Sanya   | 3785.00

SELECT
    c.customer_id,
    c.name,
    ROUND(SUM(
        o.quantity * p.price *
        (1 - COALESCE(o.discount_pct, 0) / 100.0)
    ), 2) AS total_spend
FROM orders AS o
JOIN products AS p
    ON o.product_id = p.product_id
JOIN customers AS c
    ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 5;

-- Task 3(e): Customers ranked third to fifth
-- OFFSET 2 skips the first two customers; LIMIT 3 returns the next three.
-- Output:
-- customer_id | name  | total_spend
-- C008        | Meera | 4564.60
-- C011        | Arjun | 4111.00
-- C042        | Sanya | 3785.00

SELECT
    c.customer_id,
    c.name,
    ROUND(SUM(
        o.quantity * p.price *
        (1 - COALESCE(o.discount_pct, 0) / 100.0)
    ), 2) AS total_spend
FROM orders AS o
JOIN products AS p
    ON o.product_id = p.product_id
JOIN customers AS c
    ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 3 OFFSET 2;

-- Task 3(f): Orders and revenue by category using a three-table JOIN
-- Output:
-- category     | order_count | category_revenue
-- Haircare     | 54          | 44956.10
-- Skincare     | 60          | 27346.00
-- Babycare     | 30          | 16805.00
-- PersonalCare | 36          | 10753.10

SELECT
    p.category,
    COUNT(*) AS order_count,
    ROUND(SUM(
        o.quantity * p.price *
        (1 - COALESCE(o.discount_pct, 0) / 100.0)
    ), 2) AS category_revenue
FROM orders AS o
JOIN products AS p
    ON o.product_id = p.product_id
JOIN customers AS c
    ON o.customer_id = c.customer_id
GROUP BY p.category
ORDER BY category_revenue DESC;

-- Task 3(g): Customers whose names start with A
-- Output: 10 rows
-- customer_id | name
-- C001        | Aarav
-- C003        | Aditi
-- C004        | Ananya
-- C011        | Arjun
-- C021        | Aryan
-- C030        | Anika
-- C031        | Aditya
-- C036        | Aisha
-- C041        | Ayaan
-- C044        | Aria

SELECT
    customer_id,
    name
FROM customers
WHERE name LIKE 'A%'
ORDER BY customer_id;

-- Task 3(h): Distinct customer acquisition sources
-- Output:
-- acquisition_source
-- Ad
-- Organic
-- Referral
-- Social

SELECT DISTINCT acquisition_source
FROM customers
ORDER BY acquisition_source;

-- Task 3(i): Add and populate loyalty_tier
-- Run this ALTER TABLE once, after creating customers with schema.sql.

ALTER TABLE customers
ADD COLUMN loyalty_tier VARCHAR(10);

-- Assign a loyalty tier to every customer in one UPDATE.
-- Temporarily disable safe updates for this required UPDATE without WHERE.
-- Restore the previous setting afterwards.

SET @previous_safe_updates = @@SQL_SAFE_UPDATES;
SET SQL_SAFE_UPDATES = 0;

UPDATE customers
SET loyalty_tier = CASE
    WHEN city_tier = 1 THEN 'Gold'
    ELSE 'Silver'
END;

COMMIT;

SET SQL_SAFE_UPDATES = @previous_safe_updates;

-- Task 3(i): Verify loyalty tier counts
-- Output:
-- loyalty_tier | customer_count
-- Gold         | 28
-- Silver       | 17

SELECT
    loyalty_tier,
    COUNT(*) AS customer_count
FROM customers
GROUP BY loyalty_tier
ORDER BY loyalty_tier;
