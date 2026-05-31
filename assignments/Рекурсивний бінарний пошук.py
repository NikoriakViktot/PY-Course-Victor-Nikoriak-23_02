from typing import List

def binary_search_recursive(arr: List[int], target: int, left: int, right: int) -> int:
    if left > right:
        return -1

    mid = (left + right) // 2

    if arr[mid] == target:
        return mid
    elif arr[mid] > target:
        return binary_search_recursive(arr, target, left, mid - 1)
    else:
        return binary_search_recursive(arr, target, mid + 1, right)


# Example
if __name__ == "__main__":
    data = [1, 3, 5, 7, 9, 11, 13]
    print(binary_search_recursive(data, 7, 0, len(data) - 1))