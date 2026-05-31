import unittest

# === Solution ===
def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True


# === Tests ===
class TestIsPrime(unittest.TestCase):

    def test_prime_numbers(self):
        self.assertTrue(is_prime(2))
        self.assertTrue(is_prime(3))
        self.assertTrue(is_prime(7))

    def test_non_prime_numbers(self):
        self.assertFalse(is_prime(1))
        self.assertFalse(is_prime(4))
        self.assertFalse(is_prime(9))

    def test_negative_numbers(self):
        self.assertFalse(is_prime(-5))

    def test_zero(self):
        self.assertFalse(is_prime(0))


if __name__ == "__main__":
    unittest.main()