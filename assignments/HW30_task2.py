import sqlite3

# Підключення до бази hr.db
conn = sqlite3.connect("hr.db")
cursor = conn.cursor()

# 1. Ім’я та прізвище з псевдонімами
cursor.execute("""
SELECT first_name AS "Ім'я", last_name AS "Прізвище"
FROM employees
""")
print("Імена та прізвища:", cursor.fetchall())

# 2. Унікальні відділи
cursor.execute("SELECT DISTINCT department_id FROM employees")
print("Унікальні відділи:", cursor.fetchall())

# 3. Всі дані, відсортовані за ім’ям у спадному порядку
cursor.execute("SELECT * FROM employees ORDER BY first_name DESC")
print("Всі співробітники:", cursor.fetchall())

# 4. Ім’я, прізвище, зарплата та пенсійний фонд
cursor.execute("""
SELECT first_name, last_name, salary, salary * 0.12 AS pension_fund
FROM employees
""")
print("З зарплатами та пенсійним фондом:", cursor.fetchall())

# 5. Максимальна та мінімальна зарплата
cursor.execute("SELECT MAX(salary), MIN(salary) FROM employees")
print("Макс/мін зарплата:", cursor.fetchall())

# 6. Місячна зарплата (округлена до 2 знаків)
cursor.execute("""
SELECT first_name, last_name, ROUND(salary / 12.0, 2) AS monthly_salary
FROM employees
""")
print("Місячна зарплата:", cursor.fetchall())

conn.close()
import sqlite3

conn = sqlite3.connect("hr.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())

conn.close()
