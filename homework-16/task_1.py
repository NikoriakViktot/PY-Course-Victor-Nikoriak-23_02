class Person:
    next_id = 1

    def __init__(self, full_name,  age, phone_number):
        self.name = full_name
        self.age = age
        self.phone_number = phone_number

        self.id = Person.next_id
        Person.next_id += 1

    def information(self):
        print(f'Information about a person:\n'
              f'ID: {self.id}\n'
              f'Name: {self.name}\n'
              f'Age: {self.age}\n'
              f'Phone number: {self.phone_number}')


class Student(Person):
    def __init__(self, full_name, age, phone_number, school_class):
        super().__init__(full_name, age, phone_number)
        self.school_class = school_class

    def information(self):
        super().information()
        print(f'Status: Student\n'
              f'Class: {self.school_class}')


class Teacher(Person):
    def __init__(self, full_name, age, phone_number, subject, experience, salary):
        super().__init__(full_name, age, phone_number)
        self.experience = experience
        self.subject = subject
        self.salary = salary

    def information(self):
        super().information()
        print(f'Status: Teacher\n'
              f'Subject: {self.subject}\n'
              f'Experience: {self.experience} year\n'
              f'Salary in month: {self.salary}$\n'
              f'Salary in year: {self.salary * 12}$')


mary_brown = Student('Mary Brown', 11, '12121212', 6)
thomas_white = Teacher('Thomas White', 26, '375453657', 'Geography', 3, 2000 )
mary_brown.information()
thomas_white.information()
