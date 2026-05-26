-- 1. Names
SELECT first_name AS 'First name',
       last_name AS 'Last name'
FROM employees;

-- 2. Unique department IDs
SELECT DISTINCT department_id
FROM employees;

-- 3. Employees ordered by first name DESC
SELECT *
FROM employees
ORDER BY first_name DESC;

-- 4. Salary + PF
SELECT first_name,
       last_name,
       salary,
       salary * 0.12 AS PF
FROM employees;

-- 5. Max and Min salary
SELECT MIN(salary) AS max_salary,
       MAX(salary) AS min_salary
FROM employees;

-- 6. Monthly salary (rounded)
SELECT first_name,
       last_name,
       ROUND(salary / 12, 2) AS monthly_salary
FROM employees;