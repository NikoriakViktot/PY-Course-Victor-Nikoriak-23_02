from math import gcd


class Fraction:
    def __init__(self, numerator, denominator):
        if not isinstance(numerator, int) or not isinstance(denominator, int):
            raise TypeError("Numerator and denominator must be integers")

        if denominator == 0:
            raise ZeroDivisionError("Denominator cannot be zero")

        if denominator < 0:
            numerator *= -1
            denominator *= -1

        common_divisor = gcd(numerator, denominator)
        self.numerator = numerator // common_divisor
        self.denominator = denominator // common_divisor

    def __add__(self, other):
        self._validate_fraction(other)
        numerator = self.numerator * other.denominator + other.numerator * self.denominator
        denominator = self.denominator * other.denominator
        return Fraction(numerator, denominator)

    def __sub__(self, other):
        self._validate_fraction(other)
        numerator = self.numerator * other.denominator - other.numerator * self.denominator
        denominator = self.denominator * other.denominator
        return Fraction(numerator, denominator)

    def __mul__(self, other):
        self._validate_fraction(other)
        numerator = self.numerator * other.numerator
        denominator = self.denominator * other.denominator
        return Fraction(numerator, denominator)

    def __truediv__(self, other):
        self._validate_fraction(other)

        if other.numerator == 0:
            raise ZeroDivisionError("Cannot divide by zero fraction")

        numerator = self.numerator * other.denominator
        denominator = self.denominator * other.numerator
        return Fraction(numerator, denominator)

    def __eq__(self, other):
        if not isinstance(other, Fraction):
            return False

        return self.numerator == other.numerator and self.denominator == other.denominator

    def __lt__(self, other):
        self._validate_fraction(other)
        return self.numerator * other.denominator < other.numerator * self.denominator

    def __le__(self, other):
        return self == other or self < other

    def __gt__(self, other):
        self._validate_fraction(other)
        return self.numerator * other.denominator > other.numerator * self.denominator

    def __ge__(self, other):
        return self == other or self > other

    def __str__(self):
        return f"{self.numerator}/{self.denominator}"

    def __repr__(self):
        return f"Fraction({self.numerator}, {self.denominator})"

    @staticmethod
    def _validate_fraction(value):
        if not isinstance(value, Fraction):
            raise TypeError("Value must be an instance of Fraction class")


if __name__ == "__main__":
    x = Fraction(1, 2)
    y = Fraction(1, 4)

    assert x + y == Fraction(3, 4)
    assert x - y == Fraction(1, 4)
    assert x * y == Fraction(1, 8)
    assert x / y == Fraction(2, 1)
    assert x > y
    assert y < x
    assert x >= Fraction(1, 2)
    assert y <= Fraction(1, 4)

    print("All assertions passed")
