sentence = input("Enter a sentence: ")

words = sentence.split()

result = {}

for word in words:
    if word in result:
        result[word] += 1
    else:
        result[word] = 1

print(result)