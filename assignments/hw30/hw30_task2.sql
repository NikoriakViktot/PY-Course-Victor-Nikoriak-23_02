-- 1. First Name, Last Name with aliases
SELECT
    first_name AS "First Name",
    last_name AS "Last Name"
FROM employees;


-- 2. Unique department IDs
SELECT DISTINCT department_id
FROM employees;


-- 3. Employees ordered by first name descending
SELECT *
FROM employees
ORDER BY first_name DESC;


-- 4. First name, last name, salary, PF (12% of salary)
SELECT
    first_name,
    last_name,
    salary,
    salary * 0.12 AS PF
FROM employees;


-- 5. Maximum and minimum salary
SELECT
    MAX(salary) AS max_salary,
    MIN(salary) AS min_salary
FROM employees;


-- 6. Monthly salary (rounded 2 decimals)
SELECT
    first_name,
    last_name,
    ROUND(salary / 12.0, 2) AS monthly_salary
FROM employees;