import unittest

def in_range(start, end = None, step=1):

    if end is None:
        end = start
        start = 0

    if step == 0:
        raise ValueError("step == 0")

    if step > 0:
        while start < end:
            yield start
            start += step
    else:
        while start > end:
            yield start
            start += step

class Test(unittest.TestCase):
    def test_range(self):
        self.assertEqual(list(in_range(0, 5, 1)), [0, 1, 2, 3, 4])
        self.assertEqual(list(in_range(0, 5, 2)), [0, 2, 4])
        self.assertEqual(list(in_range(3)), [0, 1, 2])
        self.assertEqual(list(in_range(1, 4)), [1, 2, 3])
        self.assertEqual(list(in_range(10, 5, -1)), [10, 9, 8, 7, 6])
