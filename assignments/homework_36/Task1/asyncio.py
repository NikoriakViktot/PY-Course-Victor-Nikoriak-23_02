import asyncio
import time
# Обчислювальні функції (корутини)
async def async_fibonacci(n):
    await asyncio.sleep(0)
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
async def async_factorial(n):
    await asyncio.sleep(0)
    if n < 0:
        return 0
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result
async def async_squares(n):
    await asyncio.sleep(0)
    return n**2
async def async_cubic(n):
    await asyncio.sleep(0)
    return n**3
async def run_async_version(numbers):
    start_time = time.perf_counter()
    # Створюємо завдання для кожного числа зі списку
    fib_tasks = [async_fibonacci(n) for n in numbers]
    fact_tasks = [async_factorial(n) for n in numbers]
    sq_tasks = [async_squares(n) for n in numbers]
    cube_tasks = [async_cubic(n) for n in numbers]
    # Збираємо чотири окремі списки результатів через asyncio.gather
    fib_results = await asyncio.gather(*fib_tasks)
    fact_results = await asyncio.gather(*fact_tasks)
    sq_results = await asyncio.gather(*sq_tasks)
    cube_results = await asyncio.gather(*cube_tasks)
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    return (fib_results, fact_results, sq_results, cube_results), execution_time