import math
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


def is_prime(n):
    if n < 2:
        return False

    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False

    return True


if __name__ == "__main__":


    start = time.time()

    with ThreadPoolExecutor() as executor:
        thread_results = list(executor.map(is_prime, NUMBERS))

    end = time.time()

    print("Threads:")
    print(thread_results)
    print("Time:", end - start)


    start = time.time()

    with ProcessPoolExecutor() as executor:
        process_results = list(executor.map(is_prime, NUMBERS))

    end = time.time()

    print("\nProcesses:")
    print(process_results)
    print("Time:", end - start)