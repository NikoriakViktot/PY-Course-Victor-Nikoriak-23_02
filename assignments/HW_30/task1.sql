-- Create table
CREATE TABLE students (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT    NOT NULL,
    grade   INTEGER NOT NULL
);

-- Rename table
ALTER TABLE students RENAME TO course_students;

-- Add new column
ALTER TABLE course_students ADD COLUMN email TEXT;

-- Insert rows
INSERT INTO course_students (name, grade, email)
VALUES ('Alice Johnson', 90, 'alice@example.com');

INSERT INTO course_students (name, grade, email)
VALUES ('Bob Smith', 75, 'bob@example.com');

-- Update row
UPDATE course_students
SET grade = 95
WHERE name = 'Alice Johnson';

-- Delete row
DELETE FROM course_students
WHERE name = 'Bob Smith';