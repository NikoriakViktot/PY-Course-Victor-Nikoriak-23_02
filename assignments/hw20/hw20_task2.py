import unittest

# === Phonebook Implementation ===
class Phonebook:
    def __init__(self):
        self.contacts = {}

    def add_contact(self, name, number):
        self.contacts[name] = number

    def get_number(self, name):
        return self.contacts.get(name)

    def delete_contact(self, name):
        if name in self.contacts:
            del self.contacts[name]

    def update_contact(self, name, number):
        if name in self.contacts:
            self.contacts[name] = number


# === Tests ===
class TestPhonebook(unittest.TestCase):

    def setUp(self):
        self.phonebook = Phonebook()
        self.phonebook.add_contact("Alice", "123")
        self.phonebook.add_contact("Bob", "456")

    def test_add_contact(self):
        self.phonebook.add_contact("Charlie", "789")
        self.assertEqual(self.phonebook.get_number("Charlie"), "789")

    def test_get_number(self):
        self.assertEqual(self.phonebook.get_number("Alice"), "123")

    def test_delete_contact(self):
        self.phonebook.delete_contact("Alice")
        self.assertIsNone(self.phonebook.get_number("Alice"))

    def test_update_contact(self):
        self.phonebook.update_contact("Bob", "999")
        self.assertEqual(self.phonebook.get_number("Bob"), "999")

    def test_non_existing_contact(self):
        self.assertIsNone(self.phonebook.get_number("Unknown"))


if __name__ == "__main__":
    unittest.main()