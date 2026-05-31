import json
import sys
import os


def load_phonebook(filename):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"{filename} not found!")

    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)


def save_phonebook(filename, data):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def add_entry(phonebook):
    entry = {
        "first_name": input("First name: "),
        "last_name": input("Last name: "),
        "phone": input("Phone: "),
        "city": input("City: "),
        "state": input("State: ")
    }
    phonebook.append(entry)
    print("Entry added!")


def search(phonebook):
    query = input("Enter search value: ").lower()
    results = []

    for entry in phonebook:
        if (
            query in entry["first_name"].lower()
            or query in entry["last_name"].lower()
            or query in (entry["first_name"] + " " + entry["last_name"]).lower()
            or query in entry["phone"]
            or query in entry["city"].lower()
            or query in entry["state"].lower()
        ):
            results.append(entry)

    if results:
        for r in results:
            print(r)
    else:
        print("No results found.")


def delete_entry(phonebook):
    phone = input("Enter phone to delete: ")
    for entry in phonebook:
        if entry["phone"] == phone:
            phonebook.remove(entry)
            print("Deleted.")
            return
    print("Not found.")


def update_entry(phonebook):
    phone = input("Enter phone to update: ")
    for entry in phonebook:
        if entry["phone"] == phone:
            entry["first_name"] = input("New first name: ")
            entry["last_name"] = input("New last name: ")
            entry["city"] = input("New city: ")
            entry["state"] = input("New state: ")
            print("Updated.")
            return
    print("Not found.")


def menu():
    print("\nPhonebook Menu:")
    print("1. Add entry")
    print("2. Search")
    print("3. Delete")
    print("4. Update")
    print("5. Exit")


def main():
    if len(sys.argv) < 2:
        print("Usage: python phonebook.py <filename.json>")
        return

    filename = sys.argv[1]

    try:
        phonebook = load_phonebook(filename)
    except FileNotFoundError as e:
        print(e)
        return

    while True:
        menu()
        choice = input("Choose an option: ")

        if choice == "1":
            add_entry(phonebook)
        elif choice == "2":
            search(phonebook)
        elif choice == "3":
            delete_entry(phonebook)
        elif choice == "4":
            update_entry(phonebook)
        elif choice == "5":
            save_phonebook(filename, phonebook)
            print("Saved. Bye!")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()