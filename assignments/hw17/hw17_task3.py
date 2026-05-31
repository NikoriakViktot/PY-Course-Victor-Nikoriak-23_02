from math import gcd


class Fraction:
    def __init__(self, numerator, denominator):
        if denominator == 0:
            raise ValueError("Denominator cannot be zero")

        common = gcd(numerator, denominator)
        self.numerator = numerator // common
        self.denominator = denominator // common

    def __add__(self, other):
        return Fraction(
            self.numerator * other.denominator + other.numerator * self.denominator,
            self.denominator * other.denominator
        )

    def __sub__(self, other):
        return Fraction(
            self.numerator * other.denominator - other.numerator * self.denominator,
            self.denominator * other.denominator
        )

    def __mul__(self, other):
        return Fraction(
            self.numerator * other.numerator,
            self.denominator * other.denominator
        )

    def __truediv__(self, other):
        if other.numerator == 0:
            raise ValueError("Cannot divide by zero fraction")

        return Fraction(
            self.numerator * other.denominator,
            self.denominator * other.numerator
        )

    def __eq__(self, other):
        return (self.numerator == other.numerator and
                self.denominator == other.denominator)

    def __lt__(self, other):
        return self.numerator * other.denominator < other.numerator * self.denominator

    def __le__(self, other):
        return self.numerator * other.denominator <= other.numerator * self.denominator

    def __str__(self):
        return f"{self.numerator}/{self.denominator}"

    def __repr__(self):
        return f"Fraction({self.numerator}, {self.denominator})"


# Example
if __name__ == "__main__":
    x = Fraction(1, 2)
    y = Fraction(1, 4)

    print(x + y)  # 3/4
    print(x - y)  # 1/4
    print(x * y)  # 1/8
    print(x / y)  # 2/1

    assert x + y == Fraction(3, 4)