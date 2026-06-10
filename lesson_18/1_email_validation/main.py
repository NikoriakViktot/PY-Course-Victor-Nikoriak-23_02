import re


class User:
    def __init__(self, email):
        self.email = self.validate(email)

    @classmethod
    def validate(cls, email):
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

        if not isinstance(email, str):
            raise ValueError("Email must be a string")

        if not re.match(pattern, email):
            raise ValueError("Invalid email address")

        return email


user = User("john.doe@gmail.com")
print(user.email)

try:
    User("wrong-email")
except ValueError as error:
    print(error)
