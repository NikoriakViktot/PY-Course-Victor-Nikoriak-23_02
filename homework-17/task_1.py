class Animal:
    def talk(self):
        pass


class Dog(Animal):
    def talk(self):
        print('Woof woof!')


class Cat(Animal):
    def talk(self):
        print('Meow!')

animals = [Dog(), Cat()]

def animal_talk(animals_list):
    for a in animals_list:
        a.talk()

animal_talk(animals)