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