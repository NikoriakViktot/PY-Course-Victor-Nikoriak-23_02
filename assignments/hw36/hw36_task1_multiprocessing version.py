import time
import math
from multiprocessing import Pool


def fib(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return a


def square(n):
    return n * n


def cube(n):
    return n ** 3


def factorial(n):
    return math.factorial(n)


def run_mp(func, numbers):
    with Pool() as pool:
        return pool.map(func, numbers)


if __name__ == "__main__":
    numbers = list(range(1, 11))
    start = time.time()

    fibs = run_mp(fib, numbers)
    facts = run_mp(factorial, numbers)
    squares = run_mp(square, numbers)
    cubes = run_mp(cube, numbers)

    print("MULTIPROCESSING RESULTS")
    print("FIB:", fibs)
    print("FACT:", facts)
    print("SQUARE:", squares)
    print("CUBE:", cubes)
    print("Time:", time.time() - start)