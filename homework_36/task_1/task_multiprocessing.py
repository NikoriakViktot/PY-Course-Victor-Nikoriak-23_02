from multiprocessing import Pool
import time


def fibonacci(n):
    if n <= 1:
        return n

    a, b = 0, 1

    for _ in range(2, n + 1):
        a, b = b, a + b

    return b


def factorial(n):
    result = 1

    for i in range(1, n + 1):
        result *= i

    return result


def square(n):
    return n ** 2


def cube(n):
    return n ** 3


def main():
    numbers = list(range(30, 40))

    start = time.perf_counter()

    with Pool() as pool:
        fib_results = pool.map(fibonacci, numbers)

        factorial_results = pool.map(factorial, numbers)

        square_results = pool.map(square, numbers)

        cube_results = pool.map(cube, numbers)

    end = time.perf_counter()

    print('Fibonacci:', fib_results)
    print('Factorial:', factorial_results)
    print('Squares', square_results)
    print('Cubes:', cube_results)

    print(f'\nMultiprocessing time: {end - start:.5f} seconds')


if __name__ == "__main__":
    main()