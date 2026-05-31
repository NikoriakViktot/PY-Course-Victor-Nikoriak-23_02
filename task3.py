import random

word = input("Enter a word: ")

for i in range(5):
    random_word = ''.join(random.choice(word) for _ in word)
    print(random_word)