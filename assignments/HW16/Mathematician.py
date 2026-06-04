class Mathematician:
    # метод для піднесення чисел у квадрат
    def square_nums(self, nums):
        return [n ** 2 for n in nums]

    # метод для видалення додатних чисел
    def remove_positives(self, nums):
        return [n for n in nums if n <= 0]

    # метод для фільтрації високосних років
    def filter_leaps(self, years):
        return [y for y in years if (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)]


# Приклад використання
m = Mathematician()

assert m.square_nums([7, 11, 5, 4]) == [49, 121, 25, 16]
assert m.remove_positives([26, -11, -8, 13, -90]) == [-11, -8, -90]
assert m.filter_leaps([2001, 1884, 1995, 2003, 2020]) == [1884, 2020]

print("Усі тести пройдено успішно ✅")
