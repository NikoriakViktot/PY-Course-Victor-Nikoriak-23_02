# Task 1

# Скрипт для запису файлу write_file.py

filename = "myfile.txt"

with open(filename, "w") as file:
    file.write("Hello file world!\n")

print(f"File '{filename}' created and written successfully.")

# Скрипт для читання файлу read_file.py

filename = "myfile.txt"

with open(filename, "r") as file:
    content = file.read()

print("File content:")
print(content)

# Task 2

# phonebook.py

import json
import sys
import os

def load_phonebook(filename):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Phonebook '{filename}' not found!")
    with open(filename, "r") as f:
        return json.load(f)

def save_phonebook(phonebook, filename):
    with open(filename, "w") as f:
        json.dump(phonebook, f, indent=4)

def add_entry(phonebook):
    entry = {}
    entry["first_name"] = input("First name: ")
    entry["last_name"] = input("Last name: ")
    entry["phone"] = input("Phone number: ")
    entry["city"] = input("City: ")
    phonebook.append(entry)
    print("Entry added!")

def search(phonebook, key, value):
    results = [p for p in phonebook if p.get(key, "").lower() == value.lower()]
    if results:
        for r in results:
            print(r)
    else:
        print("No matching records found.")

def delete_entry(phonebook, phone):
    initial_len = len(phonebook)
    phonebook[:] = [p for p in phonebook if p["phone"] != phone]
    if len(phonebook) < initial_len:
        print("Entry deleted!")
    else:
        print("Phone number not found.")

def update_entry(phonebook, phone):
    for p in phonebook:
        if p["phone"] == phone:
            print("Leave field empty to keep current value.")
            for key in ["first_name", "last_name", "city"]:
                new_val = input(f"{key} [{p[key]}]: ")
                if new_val.strip():
                    p[key] = new_val
            print("Entry updated!")
            return
    print("Phone number not found.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python phonebook.py <phonebook.json>")
        return

    filename = sys.argv[1]

    phonebook = load_phonebook(filename)

    while True:
        print("\nOptions:")
        print("1. Add entry")
        print("2. Search by first name")
        print("3. Search by last name")
        print("4. Search by full name")
        print("5. Search by phone")
        print("6. Search by city")
        print("7. Delete entry")
        print("8. Update entry")
        print("9. Exit")
        choice = input("Choose option: ")

        if choice == "1":
            add_entry(phonebook)
        elif choice == "2":
            value = input("Enter first name: ")
            search(phonebook, "first_name", value)
        elif choice == "3":
            value = input("Enter last name: ")
            search(phonebook, "last_name", value)
        elif choice == "4":
            first = input("Enter first name: ")
            last = input("Enter last name: ")
            results = [p for p in phonebook if p["first_name"].lower() == first.lower() and p["last_name"].lower() == last.lower()]
            if results:
                for r in results:
                    print(r)
            else:
                print("No matching records found.")
        elif choice == "5":
            value = input("Enter phone number: ")
            search(phonebook, "phone", value)
        elif choice == "6":
            value = input("Enter city: ")
            search(phonebook, "city", value)
        elif choice == "7":
            phone = input("Enter phone number to delete: ")
            delete_entry(phonebook, phone)
        elif choice == "8":
            phone = input("Enter phone number to update: ")
            update_entry(phonebook, phone)
        elif choice == "9":
            save_phonebook(phonebook, filename)
            print("Phonebook saved. Exiting...")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()