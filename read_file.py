# Відкриваємо файл для читання ('r')
try:
    with open("myfile.txt", "r", encoding="utf-8") as f:
        content = f.read()
        print("Вміст файлу:")
        print(content)
except FileNotFoundError:
    print("Помилка: Файл myfile.txt не знайдено.")