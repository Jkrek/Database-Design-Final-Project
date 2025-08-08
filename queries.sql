
-- Q1: Customer names with names of products they purchased where product price > 100
SELECT DISTINCT c.name AS customer_name, p.name AS product_name, p.price
FROM Customer c
JOIN "Order" o  ON o.customer_id = c.id
JOIN OrderItem oi ON oi.order_id = o.id
JOIN Product p ON p.id = oi.product_id
WHERE p.price > 100;

-- Q2: Top 5 products by revenue
SELECT p.id, p.name, SUM(oi.line_total) AS revenue
FROM OrderItem oi
JOIN Product p ON p.id = oi.product_id
GROUP BY p.id, p.name
ORDER BY revenue DESC
LIMIT 5;

-- Q3: Orders with item counts and totals in a date range (last 30 days)
SELECT o.id AS order_id, c.email, o.created_at, COUNT(oi.id) AS items, o.total_amount
FROM "Order" o
JOIN Customer c ON c.id = o.customer_id
LEFT JOIN OrderItem oi ON oi.order_id = o.id
WHERE o.created_at >= datetime('now', '-30 days')
GROUP BY o.id, c.email, o.created_at, o.total_amount
ORDER BY o.created_at DESC;

-- Q4: Customers who have never ordered
SELECT c.id, c.name, c.email
FROM Customer c
LEFT JOIN "Order" o ON o.customer_id = c.id
WHERE o.id IS NULL;

-- Q5: Low inventory report (threshold <= 10 units)
SELECT p.id, p.name, p.inventory_qty
FROM Product p
WHERE p.inventory_qty <= 10
ORDER BY p.inventory_qty ASC;
