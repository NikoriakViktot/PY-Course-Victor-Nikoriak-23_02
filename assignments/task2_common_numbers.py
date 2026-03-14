import random

list1 = []
list2 = []

i = 0
while i < 10:
    list1.append(random.randint(1, 10))
    list2.append(random.randint(1, 10))
    i += 1

print("List 1:", list1)
print("List 2:", list2)

common = []
i = 0

while i < len(list1):
    j = 0
    while j < len(list2):
        if list1[i] == list2[j] and list1[i] not in common:
            common.append(list1[i])
        j += 1
    i += 1

print("Common numbers:", common)