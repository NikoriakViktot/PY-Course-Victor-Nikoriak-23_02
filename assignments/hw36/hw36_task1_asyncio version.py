import asyncio
import time
import math


def fib(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return a


async def async_fib(n):
    return fib(n)


async def async_factorial(n):
    return math.factorial(n)


async def async_square(n):
    return n * n


async def async_cube(n):
    return n ** 3


async def main_async():
    numbers = list(range(1, 11))

    start = time.time()

    fibs, facts, squares, cubes = await asyncio.gather(
        asyncio.gather(*[async_fib(n) for n in numbers]),
        asyncio.gather(*[async_factorial(n) for n in numbers]),
        asyncio.gather(*[async_square(n) for n in numbers]),
        asyncio.gather(*[async_cube(n) for n in numbers]),
    )

    print("ASYNCIO RESULTS")
    print("FIB:", fibs)
    print("FACT:", facts)
    print("SQUARE:", squares)
    print("CUBE:", cubes)
    print("Time:", time.time() - start)


if __name__ == "__main__":
    asyncio.run(main_async())