# Відкриваємо файл для запису ('w'). Якщо файлу немає, Python його створить.
with open("myfile.txt", "w", encoding="utf-8") as f:
    f.write("Hello file world!\n")
print("Файл myfile.txt успішно створено та записано.")