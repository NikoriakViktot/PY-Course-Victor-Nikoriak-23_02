# Task 1

import random
number = random.randint(1, 10)
guess = int(input("Guess a number between 1 and 10: "))
if guess == number:
    print("Correct! You guessed the number.")
else:
    print("Wrong. The number was", number)

# Task 2

name = input("Enter your name: ")
age = int(input("Enter your age: "))
next_age = age + 1
print("Hello", name + ", on your next birthday you'll be", next_age, "years")

# Task 3

import random
word = input("Enter a word: ")
for i in range(5):
    random_word = ""
    for j in range(len(word)):
        random_char = random.choice(word)
        random_word += random_char
    print(random_word)

