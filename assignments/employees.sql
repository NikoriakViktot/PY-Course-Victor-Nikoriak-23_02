-- Таблиця співробітників
CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    department_id INTEGER,
    job_id INTEGER,
    salary REAL
);

INSERT INTO employees (first_name, last_name, department_id, job_id, salary) VALUES
('Anna', 'Ivanenko', 10, 101, 1200),
('Bohdan', 'Petrenko', 20, 102, 1500),
('Olena', 'Shevchenko', 10, 103, 1800),
('Mykola', 'Tkachenko', 30, 104, 2000),
('Svitlana', 'Koval', 20, 105, 2500);

-- Таблиця відділів
CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY,
    department_name TEXT
);

INSERT INTO departments (department_id, department_name) VALUES
(10, 'HR'),
(20, 'Finance'),
(30, 'IT');

-- Таблиця посад
CREATE TABLE jobs (
    job_id INTEGER PRIMARY KEY,
    job_title TEXT,
    min_salary REAL,
    max_salary REAL
);

INSERT INTO jobs (job_id, job_title, min_salary, max_salary) VALUES
(101, 'HR Assistant', 1000, 2000),
(102, 'Accountant', 1200, 2500),
(103, 'Recruiter', 1500, 3000),
(104, 'Developer', 1800, 4000),
(105, 'Manager', 2000, 5000);

