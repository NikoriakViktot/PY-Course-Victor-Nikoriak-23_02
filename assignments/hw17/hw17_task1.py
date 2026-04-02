class Animal:
    def talk(self):
        raise NotImplementedError("Subclass must implement this method")


class Dog(Animal):
    def talk(self):
        return "woof woof"


class Cat(Animal):
    def talk(self):
        return "meow"


def animal_talk(animal):
    print(animal.talk())


# Example
dog = Dog()
cat = Cat()

animal_talk(dog)
animal_talk(cat)