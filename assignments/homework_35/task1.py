# Task 1
# Прості числа
# NUMBERS = [
#    2,  # просте число
#    1099726899285419,
#    1570341764013157,  # просте число
#    1637027521802551,  # просте число
#    1880450821379411,  # просте число
#    1893530391196711,  # просте число
#    2447109360961063,  # просте число
#    3,  # просте число
#    2772290760589219,  # просте число
#    3033700317376073,  # просте число
#    4350190374376723,
#    4350190491008389,  # просте число
#    4350190491008390,
#    4350222956688319,
#    2447120421950803,
#    5,  # просте число
# ]
# Ми маємо наступний вхідний список чисел, деякі з яких є простими. Вам потрібно створити
# допоміжну функцію, яка приймає в якості вхідних даних число і повертає логічне значення,
# чи є воно простим чи ні.
# Використовуйте ThreadPoolExecutor та ProcessPoolExecutor для створення різних
# паралельних реалізацій фільтрації чисел.
# Порівняйте результати та продуктивність кожної з них.
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import time
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
def is_prime(n: int) -> bool:
    """Утилітарна функція для перевірки, чи є число простим."""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    # Перевірка дільників методом 6k +/- 1 до квадратного кореня з n
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True
def run_with_threads():
    """Реалізація за допомогою ThreadPoolExecutor."""
    start_time = time.perf_counter()
    with ThreadPoolExecutor() as executor:
        # Отримуємо ітератор результатів
        results = list(executor.map(is_prime, NUMBERS))
    end_time = time.perf_counter()
    return results, end_time - start_time
def run_with_processes():
    """Реалізація за допомогою ProcessPoolExecutor."""
    start_time = time.perf_counter()
    with ProcessPoolExecutor() as executor:
        # Отримуємо ітератор результатів
        results = list(executor.map(is_prime, NUMBERS))
    end_time = time.perf_counter()
    return results, end_time - start_time
if __name__ == "__main__":
    print("[ТЕСТ] Починаємо обчислення простих чисел...\n")
    # 1. Запуск потоків
    thread_res, thread_time = run_with_threads()
    print(f"🧵 ThreadPoolExecutor виконувався: {thread_time:.4f} секунд.")
    # 2. Запуск процесів
    process_res, process_time = run_with_processes()
    print(f"⚙️ ProcessPoolExecutor виконувався: {process_time:.4f} секунд.")
    # Перевірка відповідності результатів
    assert (
        thread_res == process_res
    ), "Помилка: результати виконання пулів відрізняються!"
    # Вивід результатів фільтрації
    primes = [num for num, prime in zip(NUMBERS, thread_res) if prime]
    print(f"\n✅ Результати ідентичні. Знайдено {len(primes)} простих чисел.")