# Task 1
# Практика використання анотацій типів
# Зверніться до своєї реалізації програми «Phonebook» з модуля 1 або до
# будь-якого іншого повноцінного коду, який ви написали під час курсу, і
# додайте до цього коду анотації типів, використовуючи знання, отримані в
# цьому уроці.
from typing import List, Dict, Optional
# Визначаємо тип для окремого контакту: словник, де ключ і значення — рядки
Contact = Dict[str, str]
class Phonebook:
    def __init__(self) -> None:
        """Ініціалізація порожнього списку контактів.
        Анотація -> None вказує, що конструктор нічого не повертає.
        """
        self.contacts: List[Contact] = []
    def add_contact(self, name: str, phone: str, email: Optional[str] = None) -> str:
        """Додає новий контакт до телефонної книги.
        :param name: Ім'я контакту (рядок)
        :param phone: Номер телефону (рядок)
        :param email: Опціональний email (рядок або None)
        :return: Статус-повідомлення про успішне додавання
        """
        new_contact: Contact = {
            "name": name,
            "phone": phone
        }
        if email:
            new_contact["email"] = email
        self.contacts.append(new_contact)
        return f"Контакт '{name}' успішно додано!"
    def find_contact_by_name(self, name: str) -> Optional[Contact]:
        """Шукає контакт за ім'ям.
        :return: Словник з даними контакту або None, якщо не знайдено
        """
        for contact in self.contacts:
            if contact["name"].lower() == name.lower():
                return contact
        return None
    def get_all_contacts(self) -> List[Contact]:
        """Повертає повний список усіх контактів."""
        return self.contacts
    def delete_contact(self, name: str) -> bool:
        """Видаляє контакт за ім'ям.
        :return: True, якщо видалено успішно, і False, якщо контакт не знайдено
        """
        contact: Optional[Contact] = self.find_contact_by_name(name)
        if contact:
            self.contacts.remove(contact)
            return True
        return False
if __name__ == "__main__":
    # Створюємо екземпляр класу із явно вказаним типом
    my_book: Phonebook = Phonebook()
    # Додавання контактів (аргументи перевіряються на відповідність типам str)
    print(my_book.add_contact("Олексій", "+380501234567", "alex@email.com"))
    print(my_book.add_contact("Марія", "+380679876543"))  # email залишається None
    # Отримання всіх контактів
    all_users: List[Contact] = my_book.get_all_contacts()
    print(f"\nВсього контактів у базі: {len(all_users)}")
    # Пошук контакту
    search_name: str = "Марія"
    found: Optional[Contact] = my_book.find_contact_by_name(search_name)
    if found:
        print(f"Знайдено контакт: {found['name']} -> {found['phone']}")
    else:
        print(f"Контакт {search_name} не знайдено.")