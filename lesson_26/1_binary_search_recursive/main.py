def binary_search_recursive(numbers, target, left=0, right=None):
    if right is None:
        right = len(numbers) - 1

    if left > right:
        return -1

    middle = (left + right) // 2

    if numbers[middle] == target:
        return middle

    if target < numbers[middle]:
        return binary_search_recursive(numbers, target, left, middle - 1)

    return binary_search_recursive(numbers, target, middle + 1, right)


numbers = [1, 3, 5, 7, 9, 11, 13]

assert binary_search_recursive(numbers, 1) == 0
assert binary_search_recursive(numbers, 7) == 3
assert binary_search_recursive(numbers, 13) == 6
assert binary_search_recursive(numbers, 8) == -1

print("All assertions passed")
