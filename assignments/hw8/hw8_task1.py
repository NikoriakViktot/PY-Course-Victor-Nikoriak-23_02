# task1.py

# Створюємо файл і записуємо в нього текст
with open("myfile.txt", "w") as f:
    f.write("Hello file world!\n")  # додаємо \n для нового рядка

# Відкриваємо файл для читання і друкуємо його вміст
with open("myfile.txt", "r") as f:
    content = f.read()
    print("Вміст файлу:")
    print(content)