import json
from pathlib import Path


FIELDS = ["first_name", "last_name", "telephone_number", "city", "state"]


def load_phonebook(phonebook_path):
    path = Path(phonebook_path)

    if not path.exists():
        raise FileNotFoundError(f"Phonebook file was not found: {path}")

    with open(path, "r") as file:
        phonebook = json.load(file)

    if not isinstance(phonebook, list):
        raise ValueError("Phonebook data must be a list")

    return phonebook


def save_phonebook(phonebook_path, phonebook):
    with open(phonebook_path, "w") as file:
        json.dump(phonebook, file, indent=4)


def add_record(phonebook, first_name, last_name, telephone_number, city, state):
    record = {
        "first_name": first_name,
        "last_name": last_name,
        "telephone_number": telephone_number,
        "city": city,
        "state": state,
    }

    phonebook.append(record)
    return record


def search_by_field(phonebook, field, value):
    value = value.lower()
    return [record for record in phonebook if value in record.get(field, "").lower()]


def search_by_first_name(phonebook, first_name):
    return search_by_field(phonebook, "first_name", first_name)


def search_by_last_name(phonebook, last_name):
    return search_by_field(phonebook, "last_name", last_name)


def search_by_telephone_number(phonebook, telephone_number):
    return search_by_field(phonebook, "telephone_number", telephone_number)


def search_by_full_name(phonebook, full_name):
    full_name = full_name.lower()
    results = []

    for record in phonebook:
        record_full_name = f"{record.get('first_name', '')} {record.get('last_name', '')}".lower()

        if full_name in record_full_name:
            results.append(record)

    return results


def search_by_city_or_state(phonebook, value):
    value = value.lower()
    results = []

    for record in phonebook:
        city = record.get("city", "").lower()
        state = record.get("state", "").lower()

        if value in city or value in state:
            results.append(record)

    return results


def delete_record(phonebook, telephone_number):
    for record in phonebook:
        if record.get("telephone_number") == telephone_number:
            phonebook.remove(record)
            return record

    raise ValueError("No record found")


def update_record(phonebook, telephone_number, **new_values):
    for record in phonebook:
        if record.get("telephone_number") == telephone_number:
            for field, value in new_values.items():
                if field in FIELDS and value is not None:
                    record[field] = value

            return record

    raise ValueError("No record found")
