class Dog:
    age_factor = 7
    def __init__(self, age):
        self.age = age
    def human_age(self):
        return self.age * Dog.age_factor

dog1 = Dog(8)
print(dog1.human_age())
