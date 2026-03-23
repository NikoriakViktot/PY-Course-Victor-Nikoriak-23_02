import os
import mode_phonebook

def phonebook():
    if os.path.exists('phonebook.json') == False:
        print('Файлу телефонної книги "phonebook.json" НЕ ІСНУЄ в поточній директорії!')
        return 0

    while True:
        name_phonebook = "ТЕЛЕФОННА КНИГА"
        print(name_phonebook,
              "1 - Додати нового користувача",
              "2 - Пошук за ім'ям",
              "3 - Пошук за прізвищем",
              "4 - Пошук за номером телефону",
              "5 - Пошук за повним ім'ям",
              "6 - Пошук за містом",
              "7 - Видалити запис за вказаним номером телефону",
              "8 - Оновити запис за вказаним номером телефону",
              "9 - Вихід",
              sep='\n')
        our_change = int(input("Введіть номер потрібної дії: "))

        if our_change == 1:
            mode_phonebook.add_new()
        elif our_change == 2:
            mode_phonebook.search_first_name()
        elif our_change == 3:
            mode_phonebook.search_last_name()
        elif our_change == 4:
            mode_phonebook.search_phone_number()
        elif our_change == 5:
            mode_phonebook.search_full_name()
        elif our_change == 6:
            mode_phonebook.search_city()
        elif our_change == 7:
            mode_phonebook.del_user()
        elif our_change == 8:
            mode_phonebook.rewiev_user()
        elif our_change == 9:
            break
        else:
            print("Невірно введений номер!")
    return 0

phonebook()
