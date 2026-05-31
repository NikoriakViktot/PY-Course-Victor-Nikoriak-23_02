-- Create table
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    name TEXT,
    age INTEGER
);

-- Insert rows
INSERT INTO students (id, name, age) VALUES (1, 'Ivan', 20);
INSERT INTO students (id, name, age) VALUES (2, 'Anna', 22);

-- Add new column
ALTER TABLE students ADD COLUMN grade TEXT;

-- Update rows
UPDATE students
SET grade = 'A'
WHERE id = 1;

UPDATE students
SET grade = 'B'
WHERE id = 2;

-- Delete a row
DELETE FROM students
WHERE id = 2;

-- Rename table
ALTER TABLE students RENAME TO university_students;