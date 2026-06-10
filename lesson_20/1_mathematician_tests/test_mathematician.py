import unittest
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from mathematician import Mathematician


class TestMathematician(unittest.TestCase):
    def setUp(self):
        self.mathematician = Mathematician()

    def test_square_nums(self):
        result = self.mathematician.square_nums([7, 11, 5, 4])
        self.assertEqual(result, [49, 121, 25, 16])

    def test_square_nums_with_negative_numbers(self):
        result = self.mathematician.square_nums([-3, -2, 0, 2])
        self.assertEqual(result, [9, 4, 0, 4])

    def test_square_nums_with_empty_list(self):
        result = self.mathematician.square_nums([])
        self.assertEqual(result, [])

    def test_remove_positives(self):
        result = self.mathematician.remove_positives([26, -11, -8, 13, -90])
        self.assertEqual(result, [-11, -8, -90])

    def test_remove_positives_keeps_zero(self):
        result = self.mathematician.remove_positives([5, 0, -1, 7])
        self.assertEqual(result, [0, -1])

    def test_filter_leaps(self):
        result = self.mathematician.filter_leaps([2001, 1884, 1995, 2003, 2020])
        self.assertEqual(result, [1884, 2020])

    def test_filter_leaps_with_century_years(self):
        result = self.mathematician.filter_leaps([1900, 2000, 2100, 2400])
        self.assertEqual(result, [2000, 2400])


if __name__ == "__main__":
    unittest.main()
