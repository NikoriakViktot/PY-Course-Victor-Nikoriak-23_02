-- 1. First name, last name, department number, department name for each employee
SELECT 
    e.first_name,
    e.last_name,
    e.department_id,
    d.department_name
FROM employees e
JOIN departments d
    ON e.department_id = d.department_id;


-- 2. First and last name, department, city, state province for each employee
SELECT 
    e.first_name,
    e.last_name,
    d.department_name,
    l.city,
    l.state_province
FROM employees e
JOIN departments d
    ON e.department_id = d.department_id
JOIN locations l
    ON d.location_id = l.location_id;


-- 3. Employees from departments 80 or 40
SELECT 
    e.first_name,
    e.last_name,
    e.department_id,
    d.department_name
FROM employees e
JOIN departments d
    ON e.department_id = d.department_id
WHERE e.department_id IN (80, 40);


-- 4. All departments including those without employees
SELECT 
    d.department_id,
    d.department_name,
    e.first_name,
    e.last_name
FROM departments d
LEFT JOIN employees e
    ON d.department_id = e.department_id;


-- 5. Employee first name and their manager first name
SELECT 
    e.first_name AS employee_first_name,
    m.first_name AS manager_first_name
FROM employees e
LEFT JOIN employees m
    ON e.manager_id = m.employee_id;


-- 6. Job title, full name, difference between max salary and employee salary
SELECT 
    j.job_title,
    e.first_name || ' ' || e.last_name AS full_name,
    (j.max_salary - e.salary) AS salary_difference
FROM employees e
JOIN jobs j
    ON e.job_id = j.job_id;


-- 7. Job title and average salary
SELECT 
    j.job_title,
    AVG(e.salary) AS average_salary
FROM employees e
JOIN jobs j
    ON e.job_id = j.job_id
GROUP BY j.job_title;


-- 8. Employees working in departments located in London
SELECT 
    e.first_name,
    e.last_name,
    e.salary
FROM employees e
JOIN departments d
    ON e.department_id = d.department_id
JOIN locations l
    ON d.location_id = l.location_id
WHERE l.city = 'London';


-- 9. Department name and number of employees in each department
SELECT 
    d.department_name,
    COUNT(e.employee_id) AS employee_count
FROM departments d
LEFT JOIN employees e
    ON d.department_id = e.department_id
GROUP BY d.department_name;