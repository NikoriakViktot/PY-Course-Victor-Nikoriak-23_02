## 📄 Файл `task1.sql`

Для цього завдання ми створимо таблицю `books` (книги), потім перейменуємо її на `library`, додамо колонку для року видання, внесемо дані та протестуємо оновлення й видалення.

SQL

```
-- 1. Створення таблиці
CREATE TABLE books (
    book_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL
);

-- 2. Перейменування таблиці
ALTER TABLE books RENAME TO library;

-- 3. Додавання нової колонки
ALTER TABLE library ADD COLUMN table_year INTEGER;

-- 4. Вставка кількох рядків (insert)
INSERT INTO library (title, author, table_year) 
VALUES ('The Hobbit', 'J.R.R. Tolkien', 1937);

INSERT INTO library (title, author, table_year) 
VALUES ('1984', 'George Orwell', 1949);

INSERT INTO library (title, author, table_year) 
VALUES ('To Kill a Mockingbird', 'Harper Lee', 1960);

-- 5. Оновлення даних (update)
UPDATE library 
SET table_year = 1948 
WHERE title = '1984';

-- 6. Видалення рядка (delete)
DELETE FROM library 
WHERE title = 'To Kill a Mockingbird';
```

## 📄 Файл `task2.sql`

Тут зібрані всі необхідні вибірки (SELECT) для бази даних `hr.db`. Кожен запит чітко відповідає твоєму списку вимог.

SQL

```
-- 1. Запит для відображення імен та прізвищ з аліасами "First Name" та "Last Name"
SELECT first_name AS "First Name", last_name AS "Last Name" 
FROM employees;

-- 2. Запит для отримання унікальних ID департаментів
SELECT DISTINCT department_id 
FROM employees;

-- 3. Запит для отримання всіх деталей про працівників, відсортованих за ім'ям (від Я до А)
SELECT * FROM employees 
ORDER BY first_name DESC;

-- 4. Запит для отримання імен, прізвищ, зарплати та PF (12% від зарплати)
SELECT first_name, last_name, salary, (salary * 0.12) AS PF 
FROM employees;

-- 5. Запит для отримання максимальної та мінімальної зарплати
SELECT MAX(salary) AS max_salary, MIN(salary) AS min_salary 
FROM employees;

-- 6. Запит для отримання місячної зарплати кожного працівника (округленої до 2 знаків)
-- Примітка: Якщо в базі 'salary' вказана як річна, ми ділимо на 12. Якщо вона вже місячна, залишаємо просто ROUND(salary, 2).
SELECT first_name, last_name, ROUND(salary / 12.0, 2) AS monthly_salary 
FROM employees;
```