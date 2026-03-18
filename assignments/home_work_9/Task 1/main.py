from utils import greet_user

user_name = input("Як вас звати? ")
# Викликаємо імпортовану функцію
message = greet_user(user_name)

print(message)