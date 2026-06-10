# Task 1

# Створюємо змінну з реченням
text = input("Введіть речення: ")

# Створюємо список слів, переводимо в строковий регістр та розбиваємо речення на слова 
words = text.lower().split()  

# Створюємо породжій словник
word_count = {}               

# Створюємо цикл який перебирає слова в списку words 
for word in words:
    if word in word_count:
        word_count[word] += 1 # Якщо слово є в словнику додаємо значення +1
    else:
        word_count[word] = 1 # Якщо слова немає в словнику присвоюємо значеня 1
# Виводимо словник та значення
print(word_count)


# Task 2

# Створюємо словник фруктів та їх кількість
stock = {
    "banana": 6,
    "apple": 0,
    "orange": 32, 
    "pear": 15
    } 
# Створюємо словник вартості фруктів 
price = {
    "banana": 4,
    "apple": 2,
    "orange": 1.5, 
    "pear": 3
    } 

# Створюємо пустий словник для запису результатів розрахунків 
total_costs = {}

# Створюємо цикл який перебирає словники наявності та вартості та перемножує
for fruit in stock:
      total_costs[fruit] = stock[fruit] * price[fruit]

print(total_costs)


# Task 3 

# Створюємо генератор для списків
squares = [(i, i**2) for i in range(1, 11)]

print(squares)

# Task 4 

# Створюємо список з днями тижня
days_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Використовуємо range(len(days_list)), щоб отримати індекси 0, 1, 2...
# Додаємо +1, щоб нумерація днів була від 1 до 7
direct_days = {i + 1: days_list[i] for i in range(len(days_list))}

# Для зворотнього списку міняємо місцями ключ та значення з першого словника
reverse_days = {days_list[i]: i + 1 for i in range(len(days_list))}

print(direct_days)
print(reverse_days)