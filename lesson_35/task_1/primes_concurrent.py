from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from time import perf_counter


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


# Deterministic Miller-Rabin test for numbers smaller than 2 ** 64.
def is_prime(number: int) -> bool:
    if number < 2:
        return False

    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    if number in small_primes:
        return True

    for prime in small_primes:
        if number % prime == 0:
            return False

    d = number - 1
    s = 0

    while d % 2 == 0:
        s += 1
        d //= 2

    witnesses = (2, 3, 5, 7, 11, 13, 17)

    for witness in witnesses:
        if witness >= number:
            continue

        x = pow(witness, d, number)

        if x == 1 or x == number - 1:
            continue

        for _ in range(s - 1):
            x = pow(x, 2, number)

            if x == number - 1:
                break
        else:
            return False

    return True


def filter_primes_sequential(numbers):
    return [number for number in numbers if is_prime(number)]


def filter_primes_thread_pool(numbers):
    with ThreadPoolExecutor() as executor:
        results = executor.map(is_prime, numbers)

    return [number for number, prime in zip(numbers, results) if prime]


def filter_primes_process_pool(numbers):
    with ProcessPoolExecutor() as executor:
        results = executor.map(is_prime, numbers)

    return [number for number, prime in zip(numbers, results) if prime]


def measure_time(func, numbers):
    start = perf_counter()
    result = func(numbers)
    end = perf_counter()

    return result, end - start


def main():
    sequential_result, sequential_time = measure_time(filter_primes_sequential, NUMBERS)
    threads_result, threads_time = measure_time(filter_primes_thread_pool, NUMBERS)
    processes_result, processes_time = measure_time(filter_primes_process_pool, NUMBERS)

    assert sequential_result == threads_result == processes_result

    print("Prime numbers:")
    print(sequential_result)
    print()
    print(f"Sequential time: {sequential_time:.6f} seconds")
    print(f"ThreadPoolExecutor time: {threads_time:.6f} seconds")
    print(f"ProcessPoolExecutor time: {processes_time:.6f} seconds")
    print()
    print("For CPU-bound tasks ProcessPoolExecutor is usually better than ThreadPoolExecutor.")
    print("ThreadPoolExecutor can be slower for CPU-bound work because of the GIL.")


if __name__ == "__main__":
    main()
