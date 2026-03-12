import json
import os

# Назва файлу телефонної книги
phonebook_file = "phonebook.json"

# Завантажуємо JSON дані або створюємо порожню книгу, якщо файлу немає
if os.path.exists(phonebook_file):
    with open(phonebook_file, "r") as f:
        phonebook = json.load(f)
else:
    phonebook = {}
    with open(phonebook_file, "w") as f:
        json.dump(phonebook, f, indent=4)

def save_data():
    with open(phonebook_file, "w") as f:
        json.dump(phonebook, f, indent=4)

def add_entry():
    first = input("First name: ")
    last = input("Last name: ")
    phone = input("Phone number: ")
    city = input("City: ")
    state = input("State: ")
    phonebook[phone] = {"first": first, "last": last, "city": city, "state": state}
    print("Entry added.")

def search_by_first():
    name = input("Enter first name: ")
    for phone, info in phonebook.items():
        if info['first'].lower() == name.lower():
            print(phone, info)

def search_by_last():
    name = input("Enter last name: ")
    for phone, info in phonebook.items():
        if info['last'].lower() == name.lower():
            print(phone, info)

def search_by_full():
    first = input("First name: ")
    last = input("Last name: ")
    for phone, info in phonebook.items():
        if info['first'].lower() == first.lower() and info['last'].lower() == last.lower():
            print(phone, info)

def search_by_phone():
    phone = input("Phone number: ")
    if phone in phonebook:
        print(phone, phonebook[phone])
    else:
        print("No record found.")

def search_by_city_state():
    city = input("City (leave blank to ignore): ").lower()
    state = input("State (leave blank to ignore): ").lower()
    for phone, info in phonebook.items():
        if (not city or info['city'].lower() == city) and (not state or info['state'].lower() == state):
            print(phone, info)

def delete_record():
    phone = input("Phone number to delete: ")
    if phone in phonebook:
        del phonebook[phone]
        print("Record deleted.")
    else:
        print("No record found.")

def update_record():
    phone = input("Phone number to update: ")
    if phone in phonebook:
        first = input("New first name: ")
        last = input("New last name: ")
        city = input("New city: ")
        state = input("New state: ")
        phonebook[phone] = {"first": first, "last": last, "city": city, "state": state}
        print("Record updated.")
    else:
        print("No record found.")

def menu():
    print("""
Phonebook Options:
1. Add new entry
2. Search by first name
3. Search by last name
4. Search by full name
5. Search by phone number
6. Search by city/state
7. Delete a record
8. Update a record
9. Exit
""")

# Головний цикл
while True:
    menu()
    choice = input("Enter choice: ")
    if choice == "1":
        add_entry()
    elif choice == "2":
        search_by_first()
    elif choice == "3":
        search_by_last()
    elif choice == "4":
        search_by_full()
    elif choice == "5":
        search_by_phone()
    elif choice == "6":
        search_by_city_state()
    elif choice == "7":
        delete_record()
    elif choice == "8":
        update_record()
    elif choice == "9":
        save_data()
        print("Phonebook saved. Exiting...")
        break
    else:
        print("Invalid choice, try again.")