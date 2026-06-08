import sqlite3

# Підключення до бази
conn = sqlite3.connect("mydatabase.db")
cursor = conn.cursor()

# 1. Створення таблиці
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER
)
""")

# 2. Перейменування таблиці
cursor.execute("ALTER TABLE students RENAME TO learners")

# 3. Додавання нового стовпця
cursor.execute("ALTER TABLE learners ADD COLUMN grade TEXT")

# 4. Вставка кількох рядків
cursor.execute("INSERT INTO learners (name, age, grade) VALUES (?, ?, ?)", ("Anna", 20, "A"))
cursor.execute("INSERT INTO learners (name, age, grade) VALUES (?, ?, ?)", ("Bohdan", 22, "B"))
cursor.execute("INSERT INTO learners (name, age, grade) VALUES (?, ?, ?)", ("Svitlana", 19, "A"))

# 5. Оновлення даних (UPDATE)
cursor.execute("UPDATE learners SET grade = ? WHERE name = ?", ("C", "Bohdan"))

# 6. Видалення рядка (DELETE)
cursor.execute("DELETE FROM learners WHERE name = ?", ("Svitlana",))

# Збереження змін
conn.commit()
conn.close()

# Перевірка результатів
conn = sqlite3.connect("mydatabase.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM learners")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()
