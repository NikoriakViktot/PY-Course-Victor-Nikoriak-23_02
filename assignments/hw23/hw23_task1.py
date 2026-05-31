from typing import List, Tuple

# We assume that all lists passed to functions are the same length N

# Answers:
# question1 -> O(n^2)  -> 2
# question2 -> O(1)    -> 5
# question3 -> O(n^2)  -> 4
# question4 -> O(n)    -> 3
# question5 -> O(n^2)  -> 2
# question6 -> O(log n)-> 1


def question1(first_list: List[int], second_list: List[int]) -> List[int]:
    res: List[int] = []
    for el_first_list in first_list:
        if el_first_list in second_list:  # O(n) inside loop => O(n^2)
            res.append(el_first_list)
    return res


def question2(n: int) -> int:
    for _ in range(10):  # constant loop
        n **= 3
    return n


def question3(first_list: List[int], second_list: List[int]) -> List[int]:
    temp: List[int] = first_list[:]
    for el_second_list in second_list:
        flag = False
        for check in temp:
            if el_second_list == check:
                flag = True
                break
        if not flag:
            temp.append(second_list)  # still inside nested loop => O(n^2)
    return temp


def question4(input_list: List[int]) -> int:
    res: int = 0
    for el in input_list:  # single pass => O(n)
        if el > res:
            res = el
    return res


def question5(n: int) -> List[Tuple[int, int]]:
    res: List[Tuple[int, int]] = []
    for i in range(n):
        for j in range(n):  # nested loops => O(n^2)
            res.append((i, j))
    return res


def question6(n: int) -> int:
    while n > 1:  # halving each time => O(log n)
        n /= 2
    return n