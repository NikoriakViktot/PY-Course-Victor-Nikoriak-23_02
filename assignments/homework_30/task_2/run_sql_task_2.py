import sqlite3

conn = sqlite3.connect('hr.db')
cursor = conn.cursor()

with open('task2.sql', 'r', encoding='utf-8') as f:
    sql_script = f.read()

cursor.executescript(sql_script)
conn.commit()
print("Усі SQL команди виконано успішно! ✓")



def run_and_print(title, query):
    print(f"\n--- {title} ---")
    try:
        cursor.execute(query)
        # Отримуємо назви стовпців
        headers = [description[0] for description in cursor.description]
        print(" | ".join(headers))
        print("-" * 40)
        for row in cursor.fetchall():
            print(" | ".join(str(val) for val in row))
    except sqlite3.Error as e:
        print(f"Помилка: {e}")

run_and_print("1. Псевдоніми для імен", 'SELECT first_name AS "First Name", last_name AS "Last Name" FROM employees;')
run_and_print("2. Унікальні ID відділів", 'SELECT DISTINCT department_id FROM employees;')
run_and_print("3. Сортування за іменами (спадання)", 'SELECT * FROM employees ORDER BY first_name DESC;')
run_and_print("4. Розрахунок PF (12%)", 'SELECT first_name, last_name, salary, (salary * 0.12) AS PF FROM employees;')
run_and_print("5. Мін та макс зарплати", 'SELECT MAX(salary) AS "Maximum Salary", MIN(salary) AS "Minimum Salary" FROM employees;')
run_and_print("6. Місячна зарплата (округлена)", 'SELECT first_name, last_name, ROUND(salary / 12.0, 2) AS "Monthly Salary" FROM employees;')

conn.close()

