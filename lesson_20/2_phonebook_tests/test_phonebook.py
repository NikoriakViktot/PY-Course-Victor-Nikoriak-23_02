import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from phonebook import (
    add_record,
    delete_record,
    load_phonebook,
    save_phonebook,
    search_by_city_or_state,
    search_by_first_name,
    search_by_full_name,
    search_by_last_name,
    search_by_telephone_number,
    update_record,
)


class TestPhonebook(unittest.TestCase):
    def setUp(self):
        self.phonebook = [
            {
                "first_name": "John",
                "last_name": "Doe",
                "telephone_number": "12345",
                "city": "New York",
                "state": "NY",
            },
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "telephone_number": "67890",
                "city": "Los Angeles",
                "state": "CA",
            },
        ]

    def test_add_record(self):
        record = add_record(self.phonebook, "Bob", "Brown", "11111", "Chicago", "IL")

        self.assertEqual(record["first_name"], "Bob")
        self.assertEqual(len(self.phonebook), 3)
        self.assertIn(record, self.phonebook)

    def test_search_by_first_name(self):
        result = search_by_first_name(self.phonebook, "john")
        self.assertEqual(result, [self.phonebook[0]])

    def test_search_by_last_name(self):
        result = search_by_last_name(self.phonebook, "smith")
        self.assertEqual(result, [self.phonebook[1]])

    def test_search_by_full_name(self):
        result = search_by_full_name(self.phonebook, "john doe")
        self.assertEqual(result, [self.phonebook[0]])

    def test_search_by_telephone_number(self):
        result = search_by_telephone_number(self.phonebook, "67890")
        self.assertEqual(result, [self.phonebook[1]])

    def test_search_by_city_or_state(self):
        result_by_city = search_by_city_or_state(self.phonebook, "new")
        result_by_state = search_by_city_or_state(self.phonebook, "ca")

        self.assertEqual(result_by_city, [self.phonebook[0]])
        self.assertEqual(result_by_state, [self.phonebook[1]])

    def test_delete_record(self):
        deleted_record = delete_record(self.phonebook, "12345")

        self.assertEqual(deleted_record["telephone_number"], "12345")
        self.assertEqual(len(self.phonebook), 1)
        self.assertNotIn(deleted_record, self.phonebook)

    def test_delete_record_raises_error_if_record_not_found(self):
        with self.assertRaises(ValueError):
            delete_record(self.phonebook, "00000")

    def test_update_record(self):
        updated_record = update_record(
            self.phonebook,
            "12345",
            first_name="Jack",
            city="Boston",
        )

        self.assertEqual(updated_record["first_name"], "Jack")
        self.assertEqual(updated_record["city"], "Boston")
        self.assertEqual(updated_record["last_name"], "Doe")

    def test_update_record_raises_error_if_record_not_found(self):
        with self.assertRaises(ValueError):
            update_record(self.phonebook, "00000", first_name="Unknown")

    def test_save_and_load_phonebook(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "phonebook.json"

            save_phonebook(path, self.phonebook)
            loaded_phonebook = load_phonebook(path)

        self.assertEqual(loaded_phonebook, self.phonebook)

    def test_load_phonebook_raises_error_if_file_not_found(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing.json"

            with self.assertRaises(FileNotFoundError):
                load_phonebook(path)

    def test_load_phonebook_raises_error_if_data_is_not_list(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "phonebook.json"

            with open(path, "w") as file:
                json.dump({"first_name": "John"}, file)

            with self.assertRaises(ValueError):
                load_phonebook(path)


if __name__ == "__main__":
    unittest.main()
