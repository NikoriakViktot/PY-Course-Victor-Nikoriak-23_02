-- З'єднання
-- Використовуйте зразкову базу даних SQLite hr.db (ту саму базу даних, яку ви використовували в попередньому уроці для виконання домашніх завдань)
-- У якості виконання домашнього завдання створіть файл із назвою task1.sql, що містить усі запити SQL:
-- напишіть запит на SQL для відображення імені, прізвища, номера відділу та назви відділу для кожного співробітника
-- напишіть запит на SQL для відображення імені та прізвища, відділу, міста та штату для кожного співробітника
-- напишіть запит на SQL для відображення імені, прізвища, номера відділу та назви відділу для всіх співробітників відділів 80 або 40
-- напишіть запит на SQL для відображення всіх відділів, включаючи ті, в яких немає жодного співробітника
-- напишіть запит на SQL для відображення імені всіх співробітників, включаючи ім'я їхнього керівника
-- напишіть запит на SQL для відображення посади, повного імені (ім'я та прізвище) співробітника, а також різниці між максимальною зарплатою за посадою та зарплатою співробітника
-- напишіть запит на SQL для відображення посади та середньої зарплати співробітників
-- напишіть запит на SQL для відображення повного імені (ім'я та прізвище) та зарплати тих співробітників, які працюють у будь-якому відділі, розташованому в Лондоні
-- напишіть запит на SQL для відображення назви відділу та кількості співробітників у кожному відділі
-- 1. Вивести ім'я, прізвище, номер департаменту та назву департаменту для кожного працівника.
-- Використовуємо INNER JOIN, щоб об'єднати працівників з їхніми відділами за збігом department_id.
SELECT e.first_name, e.last_name, e.department_id, d.department_name
FROM employees e
JOIN departments d ON e.department_id = d.department_id;
-- 2. Вивести ім'я, прізвище, департамент, місто та область (state province) для кожного працівника.
-- Робимо послідовне об'єднання трьох таблиць: працівники -> департаменти -> локації.
SELECT e.first_name, e.last_name, d.department_name, l.city, l.state_province
FROM employees e
JOIN departments d ON e.department_id = d.department_id
JOIN locations l ON d.location_id = l.location_id;
-- 3. Вивести ім'я, прізвище, номер та назву департаменту для працівників із департаментів 80 або 40.
-- Додаємо умову фільтрації WHERE з оператором IN.
SELECT e.first_name, e.last_name, e.department_id, d.department_name
FROM employees e
JOIN departments d ON e.department_id = d.department_id
WHERE e.department_id IN (40, 80);
-- 4. Вивести всі департаменти, включаючи ті, в яких немає жодного працівника.
-- Використовуємо LEFT JOIN від таблиці departments (або RIGHT JOIN, якщо міняти місцями),
-- щоб зберегти всі департаменти, навіть якщо для них немає відповідностей в employees.
SELECT d.department_id, d.department_name, e.first_name, e.last_name
FROM departments d
LEFT JOIN employees e ON d.department_id = e.department_id;
-- 5. Вивести ім'я кожного працівника разом з іменем його менеджера.
-- Застосовуємо Self-Join (об'єднання таблиці самої з собою). Пов'язуємо manager_id працівника з employee_id менеджера.
SELECT e.first_name AS "Employee Name", m.first_name AS "Manager Name"
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.employee_id;
-- 6. Вивести назву посади, повне ім'я працівника та різницю між максимальною зарплатою для цієї посади та поточною зарплатою працівника.
-- Об'єднуємо таблиці employees та jobs за допомогою job_id, виконуючи математичне віднімання.
SELECT j.job_title, (e.first_name || ' ' || e.last_name) AS "Full Name", (j.max_salary - e.salary) AS "Salary Difference"
FROM employees e
JOIN jobs j ON e.job_id = j.job_id;
-- 7. Вивести назву посади та середню зарплату працівників на цій посаді.
-- Об'єднуємо працівників з посадами, групуємо за назвою посади (GROUP BY) та вираховуємо середнє значення через AVG().
SELECT j.job_title, AVG(e.salary) AS "Average Salary"
FROM employees e
JOIN jobs j ON e.job_id = j.job_id
GROUP BY j.job_title;
-- 8. Вивести повне ім'я та зарплату тих працівників, які працюють у будь-якому департаменті, розташованому в Лондоні (London).
-- Об'єднуємо три таблиці та додаємо текстовий фільтр WHERE для міста.
SELECT (e.first_name || ' ' || e.last_name) AS "Full Name", e.salary
FROM employees e
JOIN departments d ON e.department_id = d.department_id
JOIN locations l ON d.location_id = l.location_id
WHERE l.city = 'London';
-- 9. Вивести назву департаменту та кількість працівників у кожному з них.
-- Групуємо дані за назвою департаменту та використовуємо функцію COUNT() для підрахунку кількості пов'язаних рядків.
SELECT d.department_name, COUNT(e.employee_id) AS "Number of Employees"
FROM departments d
LEFT JOIN employees e ON d.department_id = e.department_id
GROUP BY d.department_name;