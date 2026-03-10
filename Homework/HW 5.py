# Task 1
import random
number = random.randint(1,10)
response = input('Guess which number from 1 to 10 I thought of. ')
if number == int(response):
    print(f"You guessed right. It's {number}.")
else:
    print(f"You're wrong. The number was {number}. Try again.")

# Task 2
name = input('What\'s your name? ')
age = input('How old are you? ')
print(f'Hello {name.capitalize()}, on your next birthday you’ll be {int(age) + 1} years')

# Task 3
import random
user_word = input('Enter a word: ')
word_list = random.sample(list(user_word),5)
print(''.join(word_list))
