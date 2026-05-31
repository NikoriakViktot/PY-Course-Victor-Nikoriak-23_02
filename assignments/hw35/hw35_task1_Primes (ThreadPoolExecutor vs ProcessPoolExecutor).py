import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

NUMBERS = [
    2,
    1099726899285419,
    1570341764013157,
    1637027521802551,
    1880450821379411,
    1893530391196711,
    2447109360961063,
    3,
    2772290760589219,
    3033700317376073,
    4350190374376723,
    4350190491008389,
    4350190491008390,
    4350222956688319,
    2447120421950803,
    5,
]


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def run_executor(executor_class, name):
    start = time.time()

    with executor_class() as executor:
        results = list(executor.map(is_prime, NUMBERS))

    duration = time.time() - start

    primes = [n for n, r in zip(NUMBERS, results) if r]

    print(f"\n{name}")
    print("Primes:", primes)
    print("Time:", duration)


if __name__ == "__main__":
    run_executor(ThreadPoolExecutor, "ThreadPoolExecutor")
    run_executor(ProcessPoolExecutor, "ProcessPoolExecutor")