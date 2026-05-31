class Person:
    def __init__(self, name, age):
        self.name = name          # спільний атрибут
        self.age = age

    def introduce(self):
        return f"Мене звати {self.name}, мені {self.age} років."

    def celebrate_birthday(self):
        self.age += 1
        return f"{self.name} святкує день народження! Виповнилося {self.age}."


class Student(Person):
    def __init__(self, name, age, grade):
        super().__init__(name, age)
        self.grade = grade        # унікальний атрибут студента
        self.subjects = []        # список предметів

    def study(self, subject):
        self.subjects.append(subject)
        return f"{self.name} вивчає {subject}."

    def show_grade(self):
        return f"{self.name} навчається у {self.grade} класі."


class Teacher(Person):
    def __init__(self, name, age, subject, salary):
        super().__init__(name, age)
        self.subject = subject    # предмет, який викладає
        self.salary = salary      # зарплата (атрибут лише для вчителя)

    def teach(self, student):
        return f"{self.name} викладає {self.subject} для {student.name}."

    def show_salary(self):
        return f"Зарплата вчителя {self.name} становить {self.salary} грн."
if __name__ == "__main__":
    student = Student("Олена", 15, 9)
    teacher = Teacher("Іван Петрович", 40, "Математика", 15000)

    print(student.introduce())
    print(student.study("біологію"))
    print(student.show_grade())

    print(teacher.introduce())
    print(teacher.teach(student))
    print(teacher.show_salary())
    print(student.celebrate_birthday())