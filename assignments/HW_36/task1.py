import asyncio
import time
import multiprocessing


def get_fibonacci(n):
    if n <= 1: return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return a


def get_factorial(n):
    res = 1
    for i in range(1, n + 1):
        res *= i
    return res


def compute_all_sync(n):
    return get_fibonacci(n), get_factorial(n), n ** 2, n ** 3


async def async_worker(n):
    await asyncio.sleep(0)
    return compute_all_sync(n)


async def run_asyncio(numbers):
    start = time.perf_counter()
    tasks = [async_worker(n) for n in numbers]
    results = await asyncio.gather(*tasks)

    fibs = [r[0] for r in results]
    facts = [r[1] for r in results]
    sqrs = [r[2] for r in results]
    cubs = [r[3] for r in results]

    print(f"[Asyncio] Час виконання: {time.perf_counter() - start:.6f} сек.")
    return fibs, facts, sqrs, cubs


def run_multiprocessing(numbers):
    start = time.perf_counter()
    with multiprocessing.Pool() as pool:
        results = pool.map(compute_all_sync, numbers)

    fibs = [r[0] for r in results]
    facts = [r[1] for r in results]
    sqrs = [r[2] for r in results]
    cubs = [r[3] for r in results]

    print(f"[Multiprocessing] Час виконання: {time.perf_counter() - start:.6f} сек.")
    return fibs, facts, sqrs, cubs


if __name__ == '__main__':
    test_numbers = list(range(1, 11))

    print("--- Порівняння підходів для обчислень ---")
    asyncio.run(run_asyncio(test_numbers))
    run_multiprocessing(test_numbers)