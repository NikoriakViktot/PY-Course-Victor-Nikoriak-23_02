import json

def add_new():
    user_new = {}
    user_new['first_name'] = input("Введіть своє ім'я: ").title()
    user_new['last_name'] = input("Введіть своє прізвище: ").title()
    user_new['phone_number'] = input("Введіть свій номер телефону: ")
    user_new['city'] = input("Введіть своє місто: ").title()
    with open("phonebook.json", "r") as f:
        data_our = json.load(f)
        data_our.append(user_new)
    with open("phonebook.json", "w") as f:
        json.dump(data_our, f)
    print("Дані збережено.")
    return 0

def search_first_name():
    our_first_name = input("Введіть своє ім'я: ")
    with open("phonebook.json", "r") as f:
        s = json.load(f)
        a = 0
        for user in s:
            if user['first_name'] == our_first_name.title():
                print(user)
                a = a+1
        if a == 0:
            print("Вас не знайдено!")
    return 0

def search_last_name():
    our_last_name = input("Введіть своє прізвище: ")
    with open("phonebook.json", "r") as f:
        s = json.load(f)
        a = 0
        for user in s:
            if user['last_name'] == our_last_name.title():
                print(user)
                a = a+1
        if a == 0:
            print("Вас не знайдено!")
    return 0

def search_phone_number():
    our_phone_number = input("Введіть свій номер телефону: ")
    with open("phonebook.json", "r") as f:
        s = json.load(f)
        a = 0
        for user in s:
            if our_phone_number in user['phone_number']:
                print(user)
                a = a + 1
        if a == 0:
            print("Вас не знайдено!")
    return 0

def search_full_name():
    our_first_name = input("Введіть своє ім'я: ").title()
    our_last_name = input("Введіть своє прізвище: ").title()
    with open("phonebook.json", "r") as f:
        s = json.load(f)
        a = 0
        for user in s:
            if user['first_name'] == our_first_name and user['last_name'] == our_last_name:
                print(user)
                a = a+1
        if a == 0:
            print("Вас не знайдено!")
    return 0

def search_city():
    our_city = input("Введіть своє місто: ").title()
    with open("phonebook.json", "r") as f:
        s = json.load(f)
        a = 0
        for user in s:
            if user['city'] == our_city:
                print(user)
                a = a+1
        if a == 0:
            print("Вас не знайдено!")
    return 0

def del_user():
    our_number = input("Введіть номер телефону для видалення користувача: ")
    with open("phonebook.json", "r") as f:
        s = json.load(f)
        new_data = [p for p in s if p['phone_number'] != our_number]
    with open("phonebook.json", "w") as f:
        json.dump(new_data, f)
    print("Данні видалено успішно!")
    return 0

def rewiev_user():
    our_number = input("Введіть номер телефону для оновлення данних: ")
    with open("phonebook.json", "r") as f:
        s = json.load(f)
        new_data = [p for p in s if p['phone_number'] != our_number]
        user_rew = {}
        user_rew['first_name'] = input("Введіть своє ім'я: ").title()
        user_rew['last_name'] = input("Введіть своє прізвище: ").title()
        user_rew['phone_number'] = input("Введіть свій номер телефону: ")
        user_rew['city'] = input("Введіть своє місто: ").title()
        new_data.append(user_rew)
    with open("phonebook.json", "w") as f:
        json.dump(new_data, f)
    print("Данні оновлено успішно!")
    return 0

