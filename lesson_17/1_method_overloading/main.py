class Animal:
    def talk(self):
        raise NotImplementedError("Subclasses must implement this method")


class Dog(Animal):
    def talk(self):
        print("woof woof")


class Cat(Animal):
    def talk(self):
        print("meow")


def animal_talk(animal):
    animal.talk()


dog = Dog()
cat = Cat()

animal_talk(dog)
animal_talk(cat)
