# task 1
word = 'helloworld'
if len(word) < 2:
    print('')
else:
    print(word[:2] + word[-2:])

    #або
def some_name(word):
    if len(word) < 2:
        return ''
    else:
        return word[:2] + word[-2:]
print(some_name('helloworld'))

# task 2
def valid_number(numbers):
    if numbers.isdigit() and len(numbers) == 10:
        return 'Your number is valid'
    else:
        return 'Your number is invalid'
print(valid_number('0958731937'))

# Task 3
decision = input('How much 37+79?')
if int(decision) == 116:
    print('Correct')
else:
    print('Incorrect')

# Task 4
name = 'kateryna'
user_name = input('What`s your name?')
if user_name.lower() == name:
    print(True)
else:
    print(False)