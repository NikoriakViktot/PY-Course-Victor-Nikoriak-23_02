def cocktail_sort(items):
    items = list(items)

    start = 0
    end = len(items) - 1
    swapped = True

    while swapped:
        swapped = False

        for index in range(start, end):
            if items[index] > items[index + 1]:
                items[index], items[index + 1] = items[index + 1], items[index]
                swapped = True

        if not swapped:
            break

        end -= 1
        swapped = False

        for index in range(end - 1, start - 1, -1):
            if items[index] > items[index + 1]:
                items[index], items[index + 1] = items[index + 1], items[index]
                swapped = True

        start += 1

    return items


numbers = [5, 1, 4, 2, 8, 0, 2]

assert cocktail_sort(numbers) == [0, 1, 2, 2, 4, 5, 8]
assert cocktail_sort([1, 2, 3, 4]) == [1, 2, 3, 4]
assert cocktail_sort([]) == []
assert cocktail_sort([3]) == [3]

print(cocktail_sort(numbers))
print("All assertions passed")
