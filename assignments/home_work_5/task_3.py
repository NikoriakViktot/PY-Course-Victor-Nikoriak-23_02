#Task_3

import random

your_str = input("Введіть заданий рядок: ")
a = 0

while a < 5:
    rand_str = random.sample(your_str, len(your_str))
    our_str = ""

    for i in rand_str:
        our_str = our_str + i
    print(our_str)
    a += 1

