import asyncio
import time


async def fibonacci(n):
    await asyncio.sleep(0)

    if n <= 1:
        return n

    a, b = 0, 1

    for _ in range(2, n + 1):
        a, b = b, a + b

    return b


async def factorial(n):
    await asyncio.sleep(0)
    result = 1

    for i in range(1, n + 1):
        result *= i

    return result


async def square(n):
    await asyncio.sleep(0)
    return n ** 2


async def cube(n):
    await asyncio.sleep(0)
    return n ** 3


async def main():
    numbers = list(range(30, 40))

    start = time.perf_counter()

    fib_results = await asyncio.gather(
        *(fibonacci(n) for n in numbers)
    )

    factorial_results = await asyncio.gather(
        *(factorial(n) for n in numbers)
    )

    square_results = await asyncio.gather(
        *(square(n) for n in numbers)
    )

    cube_results = await asyncio.gather(
        *(cube(n) for n in numbers)
    )

    end = time.perf_counter()

    print('Fibonacci:', fib_results)
    print('Factorial:', factorial_results)
    print('Squares:', square_results)
    print('Cubes:', cube_results)

    print(f'\nAsyncio time: {end - start:.5f} seconds')


asyncio.run(main())