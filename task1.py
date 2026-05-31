import random

number = random.randint(1, 10)

guess = int(input("Guess the number from 1 to 10: "))

if guess == number:
    print("You guessed correctly!")
else:
    print("Wrong! The number was", number)
