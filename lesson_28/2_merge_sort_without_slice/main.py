def merge_sort(items):
    result = list(items)
    temp = [None] * len(result)

    def sort(left, right):
        if right - left <= 1:
            return

        middle = (left + right) // 2
        sort(left, middle)
        sort(middle, right)
        merge(left, middle, right)

    def merge(left, middle, right):
        left_index = left
        right_index = middle
        temp_index = left

        while left_index < middle and right_index < right:
            if result[left_index] <= result[right_index]:
                temp[temp_index] = result[left_index]
                left_index += 1
            else:
                temp[temp_index] = result[right_index]
                right_index += 1

            temp_index += 1

        while left_index < middle:
            temp[temp_index] = result[left_index]
            left_index += 1
            temp_index += 1

        while right_index < right:
            temp[temp_index] = result[right_index]
            right_index += 1
            temp_index += 1

        for index in range(left, right):
            result[index] = temp[index]

    sort(0, len(result))
    return result


numbers = [38, 27, 43, 3, 9, 82, 10]

assert merge_sort(numbers) == [3, 9, 10, 27, 38, 43, 82]
assert merge_sort([1, 2, 3]) == [1, 2, 3]
assert merge_sort([]) == []
assert merge_sort([5]) == [5]

print(merge_sort(numbers))
print("All assertions passed")
