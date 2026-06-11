import asyncio
import multiprocessing as mp
from time import perf_counter


NUMBERS = list(range(1, 11))


def fibonacci(number):
    if number <= 1:
        return number

    previous_number = 0
    current_number = 1

    for _ in range(2, number + 1):
        previous_number, current_number = current_number, previous_number + current_number

    return current_number


def factorial(number):
    result = 1

    for current_number in range(2, number + 1):
        result *= current_number

    return result


def square(number):
    return number ** 2


def cube(number):
    return number ** 3


async def async_fibonacci(number):
    await asyncio.sleep(0)
    return fibonacci(number)


async def async_factorial(number):
    await asyncio.sleep(0)
    return factorial(number)


async def async_square(number):
    await asyncio.sleep(0)
    return square(number)


async def async_cube(number):
    await asyncio.sleep(0)
    return cube(number)


async def run_async_version(numbers):
    fibonacci_results = await asyncio.gather(
        *[async_fibonacci(number) for number in numbers]
    )
    factorial_results = await asyncio.gather(
        *[async_factorial(number) for number in numbers]
    )
    square_results = await asyncio.gather(
        *[async_square(number) for number in numbers]
    )
    cube_results = await asyncio.gather(
        *[async_cube(number) for number in numbers]
    )

    return fibonacci_results, factorial_results, square_results, cube_results


def run_multiprocessing_version(numbers):
    with mp.Pool() as pool:
        fibonacci_results = pool.map(fibonacci, numbers)
        factorial_results = pool.map(factorial, numbers)
        square_results = pool.map(square, numbers)
        cube_results = pool.map(cube, numbers)

    return fibonacci_results, factorial_results, square_results, cube_results


def main():
    async_start_time = perf_counter()
    async_results = asyncio.run(run_async_version(NUMBERS))
    async_end_time = perf_counter()

    multiprocessing_start_time = perf_counter()
    multiprocessing_results = run_multiprocessing_version(NUMBERS)
    multiprocessing_end_time = perf_counter()

    assert async_results == multiprocessing_results

    print("Fibonacci:", async_results[0])
    print("Factorials:", async_results[1])
    print("Squares:", async_results[2])
    print("Cubes:", async_results[3])
    print()
    print(f"Asyncio time: {async_end_time - async_start_time:.6f} seconds")
    print(
        "Multiprocessing time: "
        f"{multiprocessing_end_time - multiprocessing_start_time:.6f} seconds"
    )
    print()
    print(
        "For small numbers from 1 to 10 asyncio is usually faster because "
        "multiprocessing spends extra time creating processes. For heavy CPU tasks "
        "multiprocessing can be more effective because it can use several CPU cores."
    )
    print("All assertions passed")


if __name__ == "__main__":
    main()
