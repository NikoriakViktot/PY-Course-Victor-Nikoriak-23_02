import os

def count_lines(file_obj):
    """Рахує кількість рядків у відкритому файлі."""
    file_obj.seek(0) # Повертаємо курсор на початок
    return len(file_obj.readlines())

def count_chars(file_obj):
    """Рахує кількість символів у відкритому файлі."""
    file_obj.seek(0) # Повертаємо курсор на початок
    return len(file_obj.read())

def test(name):
    """Відкриває файл один раз і викликає функції підрахунку."""
    if not os.path.exists(name):
        print(f"Помилка: Файл '{name}' не знайдено.")
        return

    with open(name, 'r', encoding='utf-8') as f:
        lines = count_lines(f)
        chars = count_chars(f)
        print(f"Файл: {name}")
        print(f"Рядків: {lines}")
        print(f"Символів: {chars}")

# Дозволяє запустити тест модуля на самому собі через термінал
if __name__ == "__main__":
    test("mymod.py")

# Чи потрібно додавати директорію до PYTHONPATH?
# Якщо ви запускаєте Python-інтерпретатор у тій же папці, де лежить mymod.py, то ні,
# оскільки поточна директорія за замовчуванням додається до шляхів пошуку.
# Якщо ж ви хочете імпортувати цей модуль, перебуваючи в будь-якій іншій папці на комп'ютері —
# так, шлях до папки з модулем має бути в PYTHONPATH або доданий через sys.path.append().