class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def introduce(self):
        return f"My name is {self.name}, I am {self.age} years old"


class Student(Person):
    def __init__(self, name, age, grade):
        super().__init__(name, age)
        self.grade = grade

    def study(self):
        return f"{self.name} is studying"

    def introduce(self):
        return f"I am {self.name}, a student in grade {self.grade}"


class Teacher(Person):
    def __init__(self, name, age, subject, salary):
        super().__init__(name, age)
        self.subject = subject
        self.salary = salary

    def teach(self):
        return f"{self.name} teaches {self.subject}"

    def introduce(self):
        return f"I am {self.name}, a teacher of {self.subject}"


# Example
s = Student("Ivan", 16, 10)
t = Teacher("Olena", 40, "Math", 2000)

print(s.introduce())
print(t.introduce())