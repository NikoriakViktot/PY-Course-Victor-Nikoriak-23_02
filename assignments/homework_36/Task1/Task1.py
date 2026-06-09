# Практика роботи з асинхронним кодом
# Створіть окремий асинхронний код для обчислення чисел Фібоначчі, факторіалу, квадратів
# та кубіків для введеного числа. Заплануйте виконання цього коду за допомогою
# asyncio.gather для списку цілих чисел від 1 до 10. Вам потрібно отримати чотири
# списки результатів від відповідних функцій.
# Перепишіть код, використовуючи прості функції, щоб отримати ті самі результати,
# але з використанням бібліотеки multiprocessing. Заміряйте час виконання обох
# реалізацій, проаналізуйте результати, визначте, яка реалізація є ефективнішою,
# та поясніть, чому ви отримали саме такий результат.
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

from concurrent.futures import ProcessPoolExecutor
# Прості синхронні функції
def sync_fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
def sync_factorial(n):
    if n < 0:
        return 0
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result
def sync_squares(n):
    return n**2
def sync_cubic(n):
    return n**3
def run_mp_version(numbers):
    start_time = time.perf_counter()
    # Використовуємо пул процесів для паралельного мапінгу
    with ProcessPoolExecutor() as executor:
        fib_results = list(executor.map(sync_fibonacci, numbers))
        fact_results = list(executor.map(sync_factorial, numbers))
        sq_results = list(executor.map(sync_squares, numbers))
        cube_results = list(executor.map(sync_cubic, numbers))
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    return (fib_results, fact_results, sq_results, cube_results), execution_time

if __name__ == "__main__":
    input_numbers = list(range(1, 11))
    print(f"[СТАРТ] Обробка чисел від {input_numbers[0]} до {input_numbers[-1]}\n")
    # 1. Тест асинхронності
    async_res, async_time = asyncio.run(run_async_version(input_numbers))
    print(f"⏱️  Час виконання з asyncio: {async_time:.6f} сек.")
    # 2. Тест мультипроцесорності
    mp_res, mp_time = run_mp_version(input_numbers)
    print(f"⏱️  Час виконання з multiprocessing: {mp_time:.6f} сек.")
    # Перевірка правильності (виведемо один з масивів результатів для наочності)
    print("\n📋 Отримані списки результатів (на прикладі asyncio):")
    print(f"  Фібоначчі: {async_res[0]}")
    print(f"  Факторіал: {async_res[1]}")
    print(f"  Квадрати:  {async_res[2]}")
    print(f"  Куби:      {async_res[3]}")