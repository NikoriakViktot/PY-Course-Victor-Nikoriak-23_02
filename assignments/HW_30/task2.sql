-- 1. Display first_name, last_name with aliases
SELECT first_name AS "First Name",
       last_name  AS "Last Name"
FROM employees;

-- 2. Get unique department IDs
SELECT DISTINCT department_id
FROM employees;

-- 3. All employees ordered by first_name descending
SELECT *
FROM employees
ORDER BY first_name DESC;

-- 4. first_name, last_name, salary, PF (12% of salary)
SELECT first_name,
       last_name,
       salary,
       ROUND(salary * 0.12, 2) AS PF
FROM employees;

-- 5. Maximum and minimum salary
SELECT MAX(salary) AS max_salary,
       MIN(salary) AS min_salary
FROM employees;

-- 6. Monthly salary (annual salary / 12, rounded to 2 decimal places)
SELECT first_name,
       last_name,
       ROUND(salary / 12.0, 2) AS monthly_salary
FROM employees;