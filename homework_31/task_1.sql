-- 1. first name, last name, department number, department name
SELECT e.first_name,
       e.last_name,
       e.department_id,
       d.depart_name
FROM employees e
JOIN departments d ON e.department_id = d.department_id


-- 2. first name, last name, department, city, state province
SELECT e.first_name,
       e.last_name,
       d.depart_name,
       l.city,
	   l.state_province
FROM employees e
JOIN departments d ON e.department_id = d.department_id
JOIN locations l ON d.location_id = l.location_id


-- 3. employees from departments 80 or 40
SELECT e.first_name,
       e.last_name,
       e.department_id,
	   d.depart_name
FROM employees e
JOIN departments d ON e.department_id = d.department_id
WHERE e.department_id IN (80, 40)


-- 4. all departments including those without employees
SELECT d.department_id,
       d.depart_name,
	   e.first_name
FROM departments d
LEFT JOIN employees e ON d.department_id = e.department_id


-- 5. employee and manager first name
SELECT e.first_name AS employee,
       m.first_name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.employee_id


-- 6. job title, full name, salary difference from max job salary
SELECT j.job_title,
       e.first_name || ' ' || e.last_name AS full_name,
	   (j.max_salary - e.salary) AS salary_difference
FROM employees e
JOIN jobs j ON e.job_id = j.job_id


-- 7. job title and average salary
SELECT j.job_title,
       AVG(e.salary) AS avg_salary
FROM employees e
JOIN jobs j ON e.job_id = j.job_id
GROUP BY j.job_title


-- 8. employees in London
SELECT e.first_name,
       e.last_name,
       e.salary
FROM employees e
JOIN departments d ON e.department_id = d.department_id
JOIN locations l ON d.location_id = l.location_id
WHERE l.city = 'London'


-- 9. department name and number of employees
SELECT d.depart_name,
       COUNT(e.employee_id) AS employee_count
FROM departments d
LEFT JOIN employees e ON d.department_id = e.department_id
GROUP BY d.depart_name;