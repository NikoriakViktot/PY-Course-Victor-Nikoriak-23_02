import json
import sys
import os


def load_data(filename):
    """Завантажує дані з JSON файлу або створює новий список, якщо файлу немає."""
    if not os.path.exists(filename):
        # Якщо файлу немає, повертаємо порожній список (або можна raise FileNotFoundError)
        return []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_data(filename, data):
    """Зберігає всі дані у JSON файл."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def add_entry(data):
    entry = {
        "first_name": input("Ім'я: "),
        "last_name": input("Прізвище: "),
        "full_name": "",
        "phone": input("Телефон: "),
        "city": input("Місто/Область: ")
    }
    entry["full_name"] = f"{entry['first_name']} {entry['last_name']}"
    data.append(entry)
    print("✅ Запис додано.")


def search(data, key):
    query = input(f"Введіть значення для пошуку ({key}): ").lower()
    results = [item for item in data if query in str(item.get(key, "")).lower()]
    for res in results:
        print(res)
    if not results:
        print("Нічого не знайдено.")


def delete_entry(data):
    phone = input("Введіть номер телефону для видалення: ")
    for i, item in enumerate(data):
        if item['phone'] == phone:
            del data[i]
            print("🗑️ Запис видалено.")
            return
    print("❌ Номер не знайдено.")


def update_entry(data):
    phone = input("Введіть номер телефону для оновлення: ")
    for item in data:
        if item['phone'] == phone:
            item['first_name'] = input(f"Нове ім'я ({item['first_name']}): ") or item['first_name']
            item['last_name'] = input(f"Нове прізвище ({item['last_name']}): ") or item['last_name']
            item['city'] = input(f"Нове місто ({item['city']}): ") or item['city']
            item['full_name'] = f"{item['first_name']} {item['last_name']}"
            print("🔄 Запис оновлено.")
            return
    print("❌ Номер не знайдено.")


def main():
    if len(sys.argv) < 2:
        print("Помилка: вкажіть назву файлу телефонної книги. Приклад: python phonebook.py mybook.json")
        return

    filename = sys.argv[1]
    phonebook = load_data(filename)

    while True:
        print("\n--- МЕНЮ ---")
        print("1. Додати запис | 2. Пошук за іменем | 3. Пошук за прізвищем | 4. Повна назва")
        print("5. За телефоном | 6. За містом | 7. Видалити | 8. Оновити | 9. Вихід")

        choice = input("Оберіть дію: ")

        if choice == '1':
            add_entry(phonebook)
        elif choice == '2':
            search(phonebook, 'first_name')
        elif choice == '3':
            search(phonebook, 'last_name')
        elif choice == '4':
            search(phonebook, 'full_name')
        elif choice == '5':
            search(phonebook, 'phone')
        elif choice == '6':
            search(phonebook, 'city')
        elif choice == '7':
            delete_entry(phonebook)
        elif choice == '8':
            update_entry(phonebook)
        elif choice == '9':
            save_data(filename, phonebook)
            print("💾 Дані збережено. До зустрічі!")
            break
        else:
            print("Невірний вибір.")


if __name__ == "__main__":
    main()