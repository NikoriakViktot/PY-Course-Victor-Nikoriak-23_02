import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

NUMBERS = [
    2,  # prime
    1099726899285419,
    1570341764013157,  # prime
    1637027521802551,  # prime
    1880450821379411,  # prime
    1893530391196711,  # prime
    2447109360961063,  # prime
    3,  # prime
    2772290760589219,  # prime
    3033700317376073,  # prime
    4350190374376723,
    4350190491008389,  # prime
    4350190491008390,
    4350222956688319,
    2447120421950803,
    5,  # prime
]


def is_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def run_executor(executor_class, name):
    start_time = time.perf_counter()
    with executor_class() as executor:
        results = list(executor.map(is_prime, NUMBERS))

    end_time = time.perf_counter()
    prime_numbers = [num for num, prime in zip(NUMBERS, results) if prime]
    print(f"[{name}] Знайдено простих чисел: {len(prime_numbers)}")
    print(f"[{name}] Час виконання: {end_time - start_time:.4f} секунд\n")


if __name__ == '__main__':
    print("--- Порівняння продуктивності пулів ---\n")
    run_executor(ThreadPoolExecutor, "ThreadPoolExecutor (Потоки)")
    run_executor(ProcessPoolExecutor, "ProcessPoolExecutor (Процеси)")