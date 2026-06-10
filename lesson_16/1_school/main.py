class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def introduce(self):
        return f"Hello, my name is {self.name} and I am {self.age} years old"

    def go_to_school(self):
        return f"{self.name} goes to school"


class Student(Person):
    def __init__(self, name, age, grade):
        super().__init__(name, age)
        self.grade = grade
        self.marks = []

    def add_mark(self, mark):
        self.marks.append(mark)

    def get_average_mark(self):
        if not self.marks:
            return 0

        return sum(self.marks) / len(self.marks)

    def study(self, subject):
        return f"{self.name} studies {subject}"


class Teacher(Person):
    def __init__(self, name, age, subject, salary):
        super().__init__(name, age)
        self.subject = subject
        self.salary = salary

    def teach(self):
        return f"{self.name} teaches {self.subject}"

    def get_salary(self):
        return self.salary


student = Student("John", 15, "9A")
student.add_mark(10)
student.add_mark(12)

teacher = Teacher("Anna", 34, "Math", 2500)

print(student.introduce())
print(student.study("English"))
print(student.get_average_mark())
print(teacher.introduce())
print(teacher.teach())
print(teacher.get_salary())
