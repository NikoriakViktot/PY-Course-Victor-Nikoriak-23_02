class Fraction:
    def __init__(self, numerator, denominator):
        if denominator == 0:
            raise ValueError('Змінник не може бути нулем')
        self.numerator = numerator
        self.denominator = denominator

    def __add__(self, other):
        if not isinstance(other, Fraction):
            raise TypeError('Можна додати тільки дроби')

        new_numerator = self.numerator * other.denominator + self.denominator * other.numerator
        new_denominator = self.denominator * other.denominator
        return Fraction(new_numerator, new_denominator)

    def __sub__(self, other):
        if not isinstance(other, Fraction):
            raise TypeError('Можна відняти тільки дроби')
        if other.numerator == 0:
            raise ZeroDivisionError('Ділення на нуль неможливе')

        new_numerator = self.numerator * other.denominator - self.denominator * other.numerator
        new_denominator = self.denominator * other.denominator
        return Fraction(new_numerator, new_denominator)

    def __mul__(self, other):
        if not isinstance(other, Fraction):
            raise TypeError('Можна множити тільки дроби')

        new_numerator = self.numerator * other.numerator
        new_denominator = self.denominator * other.denominator
        return Fraction(new_numerator, new_denominator)

    def __truediv__(self, other):
        if not isinstance(other, Fraction):
            raise TypeError('Можна ділити тільки дроби')

        new_numerator = self.numerator * other.denominator
        new_denominator = self.denominator * other.numerator
        return Fraction(new_numerator, new_denominator)

    def __str__(self):
        return f'{self.numerator}/{self.denominator}'

    def __repr__(self):
        return f'Fraction({self.numerator}, {self.denominator})'


if __name__ == "__main__":
    x = Fraction(1, 2)
    y = Fraction(1, 4)
    x + y == Fraction(3, 4)