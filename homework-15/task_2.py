class Dog:
    age_factor = 7

    def __init__(self, age):
        self.age = age

    def human_age(self):
        return self.age * Dog.age_factor

buddy = Dog(4)
print(buddy.human_age())