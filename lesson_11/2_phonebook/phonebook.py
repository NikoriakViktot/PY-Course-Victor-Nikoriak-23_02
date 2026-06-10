import json
import sys
from pathlib import Path


FIELDS = ["first_name", "last_name", "telephone_number", "city", "state"]


def get_phonebook_path():
    if len(sys.argv) < 2:
        raise ValueError("Phonebook name must be provided as the first argument")

    return Path(__file__).parent / sys.argv[1]


def load_phonebook(phonebook_path):
    if not phonebook_path.exists():
        raise FileNotFoundError(f"Phonebook file was not found: {phonebook_path}")

    with open(phonebook_path, "r") as file:
        phonebook = json.load(file)

    if not isinstance(phonebook, list):
        raise ValueError("Phonebook data must be a list")

    return phonebook


def save_phonebook(phonebook_path, phonebook):
    with open(phonebook_path, "w") as file:
        json.dump(phonebook, file, indent=4)


def print_record(record):
    print(f"First name: {record.get('first_name', '')}")
    print(f"Last name: {record.get('last_name', '')}")
    print(f"Telephone number: {record.get('telephone_number', '')}")
    print(f"City: {record.get('city', '')}")
    print(f"State: {record.get('state', '')}")
    print("-" * 30)


def print_records(records):
    if not records:
        print("No records found")
        return

    for record in records:
        print_record(record)


def add_record(phonebook):
    record = {}

    for field in FIELDS:
        record[field] = input(f"Enter {field.replace('_', ' ')}: ").strip()

    phonebook.append(record)
    print("Record was added")


def search_by_field(phonebook, field):
    value = input(f"Enter {field.replace('_', ' ')}: ").strip().lower()
    results = []

    for record in phonebook:
        if value in record.get(field, "").lower():
            results.append(record)

    print_records(results)


def search_by_full_name(phonebook):
    full_name = input("Enter full name: ").strip().lower()
    results = []

    for record in phonebook:
        record_full_name = f"{record.get('first_name', '')} {record.get('last_name', '')}".lower()
        if full_name in record_full_name:
            results.append(record)

    print_records(results)


def search_by_city_or_state(phonebook):
    value = input("Enter city or state: ").strip().lower()
    results = []

    for record in phonebook:
        city = record.get("city", "").lower()
        state = record.get("state", "").lower()

        if value in city or value in state:
            results.append(record)

    print_records(results)


def delete_record(phonebook):
    telephone_number = input("Enter telephone number: ").strip()

    for record in phonebook:
        if record.get("telephone_number") == telephone_number:
            phonebook.remove(record)
            print("Record was deleted")
            return

    print("No record found")


def update_record(phonebook):
    telephone_number = input("Enter telephone number: ").strip()

    for record in phonebook:
        if record.get("telephone_number") == telephone_number:
            for field in FIELDS:
                current_value = record.get(field, "")
                new_value = input(f"Enter new {field.replace('_', ' ')} or press Enter to keep '{current_value}': ").strip()

                if new_value:
                    record[field] = new_value

            print("Record was updated")
            return

    print("No record found")


def print_menu():
    print("\nPhonebook menu")
    print("1. Add new entry")
    print("2. Search by first name")
    print("3. Search by last name")
    print("4. Search by full name")
    print("5. Search by telephone number")
    print("6. Search by city or state")
    print("7. Delete a record by telephone number")
    print("8. Update a record by telephone number")
    print("9. Exit")


def main():
    phonebook_path = get_phonebook_path()
    phonebook = load_phonebook(phonebook_path)

    while True:
        print_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_record(phonebook)
        elif choice == "2":
            search_by_field(phonebook, "first_name")
        elif choice == "3":
            search_by_field(phonebook, "last_name")
        elif choice == "4":
            search_by_full_name(phonebook)
        elif choice == "5":
            search_by_field(phonebook, "telephone_number")
        elif choice == "6":
            search_by_city_or_state(phonebook)
        elif choice == "7":
            delete_record(phonebook)
        elif choice == "8":
            update_record(phonebook)
        elif choice == "9":
            save_phonebook(phonebook_path, phonebook)
            print("Phonebook was saved")
            break
        else:
            print("Wrong option")


main()
