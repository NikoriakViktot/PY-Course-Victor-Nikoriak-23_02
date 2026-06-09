--# Task 1
--# Створіть таблицю
--# Створіть таблицю на свій вибір у зразковій базі даних SQLite, перейменуйте її та
-- додайте новий стовпець. Вставте кілька рядків у таблицю. Крім того, виконайте
-- оператори UPDATE та DELETE для вставлених рядків.
--# Як відповідь на це завдання створіть файл із назвою task1.sql, що міститиме всі
-- оператори SQL, які ви використовували для виконання цього завдання
-- 1. Створення початкової таблиці (структура для відстеження товарів)
CREATE TABLE products_old (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    price REAL NOT NULL
);
-- 2. Перейменування таблиці відповідно до умов завдання
ALTER TABLE products_old RENAME TO products;
-- 3. Додавання нової колонки до перейменованої таблиці
ALTER TABLE products ADD COLUMN stock_quantity INTEGER DEFAULT 0;
-- 4. Вставка декількох рядків (записів) у таблицю
INSERT INTO products (product_name, price, stock_quantity)
VALUES ('Laptop', 1200.00, 15);
INSERT INTO products (product_name, price, stock_quantity)
VALUES ('Smartphone', 800.00, 30);
INSERT INTO products (product_name, price, stock_quantity)
VALUES ('Wireless Headphones', 150.00, 50);
-- 5. Виконання операції UPDATE (окремий запис оновлюється за його ID)
UPDATE products
SET price = 750.00, stock_quantity = 28
WHERE product_id = 2;
-- 6. Виконання операції DELETE (видалення конкретного рядка)
DELETE FROM products
WHERE product_id = 3;
-- # CREATE TABLE: Створює таблицю products_old з трьома базовими атрибутами.
--# ALTER TABLE ... RENAME TO: Перейменовує її на чисту назву products
--# ALTER TABLE ... ADD COLUMN: Додає нову характеристику зберігання зі значенням за замовчуванням 0
--# INSERT INTO: Наповнює базу тестовими даними
--# UPDATE: Знижує ціну та коригує залишок для смартфона
--# DELETE: Повністю вилучає навушники (product_id = 3) з асортименту

