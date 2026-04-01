class Person:
    def __init__(self, name, surname):
        self.name = name
        self.surname = surname

    def say_hello(self):
        return f"Hello, I`m {self.name} {self.surname}"

class Teacher(Person):
    def __init__(self, name, surname, subject):
        super().__init__(name, surname)
        self.subject = subject

class Student(Person):
    def __init__(self, name, surname, grade):
        super().__init__(name, surname)
        self.grade = grade


profi = Teacher("Max", "Hope", "Python")
junior = Student("Jo", "Low", "10-A")

print(f"{profi.say_hello()}. I teach {profi.subject}.")
print(f"Hi! My name is {junior.name} {junior.surname}. I'm in grade {junior.grade}.")