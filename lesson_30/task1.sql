DROP TABLE IF EXISTS student_courses;
DROP TABLE IF EXISTS courses;

CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    duration_weeks INTEGER NOT NULL,
    price REAL NOT NULL
);

ALTER TABLE courses RENAME TO student_courses;

ALTER TABLE student_courses ADD COLUMN teacher TEXT;

INSERT INTO student_courses (name, duration_weeks, price, teacher)
VALUES
    ('Python Basic', 12, 300.00, 'John Smith'),
    ('SQL Basic', 8, 200.00, 'Anna Brown'),
    ('Web Development', 16, 500.00, 'Michael Green');

UPDATE student_courses
SET price = 350.00
WHERE name = 'Python Basic';

UPDATE student_courses
SET teacher = 'Kate Wilson'
WHERE name = 'SQL Basic';

DELETE FROM student_courses
WHERE name = 'Web Development';

SELECT * FROM student_courses;
