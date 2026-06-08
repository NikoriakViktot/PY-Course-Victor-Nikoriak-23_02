-- 1. Створення таблиці
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER
);

-- 2. Перейменування таблиці
ALTER TABLE students RENAME TO learners;

-- 3. Додавання нового стовпця
ALTER TABLE learners ADD COLUMN grade TEXT;

-- 4. Вставка кількох рядків
INSERT INTO learners (name, age, grade) VALUES ('Anna', 20, 'A');
INSERT INTO learners (name, age, grade) VALUES ('Bohdan', 22, 'B');
INSERT INTO learners (name, age, grade) VALUES ('Svitlana', 19, 'A');

-- 5. Оновлення даних (UPDATE)
UPDATE learners
SET grade = 'C'
WHERE name = 'Bohdan';

-- 6. Видалення рядка (DELETE)
DELETE FROM learners
WHERE name = 'Svitlana';
