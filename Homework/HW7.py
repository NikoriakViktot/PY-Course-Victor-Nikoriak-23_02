# Task 1
sentence = input('Додай щось у словник: ')
words = sentence.split()
words_dict = {}
i = 1
for word in words:
    if word not in words_dict:
        words_dict[word] = 1
    else:
        words_dict[word] += 1
print(words_dict)

# Task 2
stock = {
    "banana": 6,
    "apple": 0,
    "orange": 32,
    "pear": 15
}
prices = {
    "banana": 4,
    "apple": 2,
    "orange": 1.5,
    "pear": 3
}

total_price = {fruit: stock[fruit] * prices[fruit] for fruit in stock}
print(total_price)

# Task 3
list1 = [(i, i**2) for i in range(1, 11)]
print(list1)

# Task 4
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
week = {i: day for i, day in enumerate(days, start=1)}
print(week)

week_v2 = {day: i for i, day in enumerate(days, start=1)}
print(week_v2)