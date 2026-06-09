import sqlite3

# 1. Підключаємося до бази даних (файл створиться автоматично в папці проекту)
conn = sqlite3.connect('my_database.db')
cursor = conn.cursor()

# 2. Читаємо наш файл task1.sql
with open('task1.sql', 'r', encoding='utf-8') as f:
    sql_script = f.read()

try:
    # 3. Виконуємо всі SQL-команди з файлу за один раз
    cursor.executescript(sql_script)
    conn.commit()
    print("Усі SQL команди виконано успішно! ✓")

    # 4. Перевіримо, що залишилося в базі даних після UPDATE та DELETE
    cursor.execute("SELECT * FROM phone_book")
    rows = cursor.fetchall()

    print("\nПоточний вміст таблиці 'phone_book':")
    for row in rows:
        print(f"ID: {row[0]} | Ім'я: {row[1]} | Прізвище: {row[2]} | Телефон: {row[3]}")

except sqlite3.Error as e:
    print(f"Помилка при виконанні SQL: {e}")
finally:
    conn.close()
