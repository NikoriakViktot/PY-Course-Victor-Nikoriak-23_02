import json
import sys

def load_phonebook(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Помилка: файл не знайдено.")
        sys.exit(1)

def save_phonebook(filename, book):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(book, f, ensure_ascii=False, indent=4)

def add_entry(book, filename):
    name = input("Ім'я: ")
    lastname = input("Прізвище: ")
    phone = input("Телефон: ")
    city = input("Місто: ")
    oblast = input("Область: ")
    book.append({"name": name, "lastname": lastname, "phone": phone, "city": city, "oblast": oblast})
    save_phonebook(filename, book)

def search(book, key, value):
    return [entry for entry in book if entry.get(key, "").lower() == value.lower()]

def delete_entry(book, phone):
    book[:] = [entry for entry in book if entry["phone"] != phone]

def update_entry(book, phone):
    for entry in book:
        if entry["phone"] == phone:
            print("Знайдено:", entry)
            entry["name"] = input("Нове ім'я: ") or entry["name"]
            entry["lastname"] = input("Нове прізвище: ") or entry["lastname"]
            entry["city"] = input("Нове місто: ") or entry["city"]
            entry["oblast"] = input("Нова область: ") or entry["oblast"]
            return
    print("Запис не знайдено.")

def menu(book, filename):
    while True:
        print("\nМеню:")
        print("1. Додати новий запис")
        print("2. Пошук за ім'ям")
        print("3. Пошук за прізвищем")
        print("4. Пошук за повним ім'ям")
        print("5. Пошук за номером телефону")
        print("6. Пошук за містом або областю")
        print("7. Видалити запис за номером телефону")
        print("8. Оновити запис за номером телефону")
        print("9. Вихід")
        print("10. Показати всі записи")

        choice = input("Виберіть опцію: ")

        if choice == "1":
            add_entry(book, filename)
        elif choice == "2":
            name = input("Ім'я: ")
            print(search(book, "name", name))
        elif choice == "3":
            lastname = input("Прізвище: ")
            print(search(book, "lastname", lastname))
        elif choice == "4":
            fullname = input("Повне ім'я (Ім'я Прізвище): ")
            name, lastname = fullname.split()
            results = [entry for entry in book if entry["name"].lower() == name.lower() and entry["lastname"].lower() == lastname.lower()]
            print(results)
        elif choice == "5":
            phone = input("Телефон: ")
            print(search(book, "phone", phone))
        elif choice == "6":
            city = input("Місто: ")
            oblast = input("Область: ")
            results = [entry for entry in book if entry["city"].lower() == city.lower() or entry["oblast"].lower() == oblast.lower()]
            print(results)
        elif choice == "7":
            phone = input("Телефон: ")
            delete_entry(book, phone)
        elif choice == "8":
            phone = input("Телефон: ")
            update_entry(book, phone)
        elif choice == "9":
            save_phonebook(filename, book)
            print("Дані збережено. Вихід.")
            break
        elif choice == "10":
            for entry in book:
                print(f"Ім'я: {entry['name']}, Прізвище: {entry['lastname']}, Телефон: {entry['phone']}, Місто: {entry['city']}, Область: {entry['oblast']}")
        else:
            print("Невірний вибір.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Вкажіть назву телефонної книги (JSON).")
        sys.exit(1)

    filename = sys.argv[1]
    phonebook = load_phonebook(filename)
    menu(phonebook, filename)
