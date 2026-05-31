import re

class User:
    def __init__(self, email: str):
        self.email = email
        self.validate(email)

    @classmethod
    def validate(cls, email):
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(pattern, email):
            raise ValueError(f"Invalid email: {email}")

# Приклад використання
try:
    u1 = User("test@example.com")  # валідно
    print("Email is valid")
    u2 = User("invalid_email")     # викличе ValueError
except ValueError as e:
    print(e)