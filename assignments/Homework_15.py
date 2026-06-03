# Task 1
# Клас «Person»
# Створіть клас із назвою «Person». Зробіть так, щоб метод __init__() приймав як параметри ім’я,
# прізвище та вік і додавав їх як атрибути. Створіть ще один метод із назвою talk(), який виводить
# привітання від цієї особи, наприклад: «Привіт, мене звати Карл Джонсон, і мені 26 років».
class Person:
    def __init__(self, firstname, lastname, age):
        self.firstname = firstname
        self.lastname = lastname
        self.age = age

    def talk(self):
        print(f"Hello, my name is {self.firstname} {self.lastname} and I’m {self.age} years old.")

# Task 2
# Вік собаки#
# Створіть клас Dog з атрибутом класу “age_factor”, що дорівнює 7. Створіть метод __init__(),
# який приймає значення віку собаки. Потім створіть метод `human_age`, який повертає вік собаки
# у перерахунку на людський вік.

class Dog:
    age_factor = 7

    def __init__(self, dog_age):
        self.dog_age = dog_age

    def human_age(self):
        return self.dog_age * Dog.age_factor

# Task 3
# Пульт дистанційного керування телевізором#
# Створіть простий прототип пульта дистанційного керування телевізором на Python.
# Він використовуватиме такі команди:#
# first_channel() — вмикає перший канал зі списку.
# last_channel() — вмикає останній канал зі списку.
# turn_channel(N) — вмикає N-й канал. Зверніть увагу, що нумерація каналів починається з 1, а не з 0.
# next_channel() — вмикає наступний канал. Якщо поточний канал є останнім, вмикає перший канал.
# previous_channel() — вмикає попередній канал. Якщо поточний канал є першим, вмикає останній канал.
# current_channel() — повертає назву поточного каналу.
# exists(N/“name”) — приймає 1 аргумент — число N або рядок “name” і повертає «Yes», якщо канал N
# або “name” існує у списку, або «No» — в іншому випадку.
# Канал за замовчуванням, увімкнений до виконання всіх команд, — №1.
# Ваше завдання — створити клас TVController та описані вище методи.
# CHANNELS = [«BBC», “Discovery”, «TV1000»]
#  class TVController:
# pass
#  controller = TVController(CHANNELS)
# controller.first_channel() == «BBC»
# controller.last_channel() == «TV1000»
# controller.turn_channel(1) == «BBC»
# controller.next_channel() == «Discovery»
# controller.previous_channel() == «BBC»
# controller.current_channel() == «BBC»
# controller.exists(4) == «No»
# controller.exists(«BBC») == «Yes»

CHANNELS = ["BBC", "Discovery", "TV1000"]

class TVController:
    def __init__(self, channels):
        self.channels = channels
        self.current_index = 0

    def first_channel(self):
        self.current_index = 0
        return self.channels[self.current_index]

    def last_channel(self):
        self.current_index = len(self.channels) - 1
        return self.channels[self.current_index]

    def turn_channel(self, n):
        if 1 <= n <= len(self.channels):
            self.current_index = n - 1
        return self.channels[self.current_index]

    def next_channel(self):
        self.current_index = (self.current_index + 1) % len(self.channels)
        return self.channels[self.current_index]

    def previous_channel(self):
        self.current_index = (self.current_index - 1) % len(self.channels)
        return self.channels[self.current_index]

    def current_channel(self):
        return self.channels[self.current_index]

    def exists(self, param):
        if isinstance(param, int):
            if 1 <= param <= len(self.channels):
                return "Yes"
        elif isinstance(param, str):
            if param in self.channels:
                return "Yes"
        return "No"


# Перевірка роботи коду:
controller = TVController(CHANNELS)

print(controller.first_channel() == "BBC")         # True
print(controller.last_channel() == "TV1000")       # True
print(controller.turn_channel(1) == "BBC")         # True
print(controller.next_channel() == "Discovery")    # True
print(controller.previous_channel() == "BBC")      # True
print(controller.current_channel() == "BBC")       # True
print(controller.exists(4) == "No")                # True
print(controller.exists("BBC") == "Yes")           # True