def square_nums(nums):
    return list(map(lambda x: x**2, nums))

def remove_negatives(nums):
    return list(filter(lambda x: x > 0, nums))

def choose_func(nums: list, func1, func2):
    if all(n > 0 for n in nums):
        return func1(nums)
    else:
        return func2(nums)

#Перевірка
nums1 = [1, 2, 3, 4, 5]
nums2 = [1, -2, 3, -4, 5]

assert choose_func(nums1, square_nums, remove_negatives) == [1, 4, 9, 16, 25]
assert choose_func(nums2, square_nums, remove_negatives) == [1, 3, 5]

print("Результат 1:", choose_func(nums1, square_nums, remove_negatives))
print("Результат 2:", choose_func(nums2, square_nums, remove_negatives))