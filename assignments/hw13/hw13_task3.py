# Homework 13
# Task 3
# Function with callbacks

def choose_func(nums: list, func1, func2):
    """
    If all numbers in the list are positive,
    execute func1.
    Otherwise execute func2.
    """

    # Check if all numbers are positive
    if all(num > 0 for num in nums):
        return func1(nums)
    else:
        return func2(nums)


# Example functions

def square_nums(nums):
    """Return list of squared numbers"""
    return [num ** 2 for num in nums]


def remove_negatives(nums):
    """Return list without negative numbers"""
    return [num for num in nums if num > 0]


# Test data
nums1 = [1, 2, 3, 4, 5]
nums2 = [1, -2, 3, -4, 5]

# Assertions (tests)
assert choose_func(nums1, square_nums, remove_negatives) == [1, 4, 9, 16, 25]
assert choose_func(nums2, square_nums, remove_negatives) == [1, 3, 5]

print("All tests passed successfully ✅")