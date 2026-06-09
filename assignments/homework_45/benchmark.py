import time
import asyncio
import httpx
base_url = "http://127.0.0"
def run_sync_benchmark():
    """Послідовні синхронні запити (імітація Requests)."""
    print("--- Запуск синхронного тесту ---")
    start_all = time.time()
    latencies = []
    # Використовуємо звичайний HTTP-клієнт
    with httpx.Client() as client:
        for i in range(10):
            start_req = time.time()
            # Додаємо унікальний параметр, щоб уникнути кешування браузером/сервером
            response = client.get(f"{base_url}?scope=personal&iteration={i}")
            end_req = time.time()
            duration = end_req - start_req
            latencies.append(duration)
            print(f"Запит {i + 1}: статус {response.status_code}, час: {duration:.4f} сек")
    end_all = time.time()
    total_time = end_all - start_all
    avg_time = sum(latencies) / len(latencies)
    print(f"Середній час одного синхронного запиту: {avg_time:.4f} сек")
    print(f"Сумарний час на всі синхронні запити: {total_time:.4f} сек\n")
async def run_async_benchmark():
    """Паралельні асинхронні запити за допомогою HTTPX."""
    print("--- Запуск асинхронного тесту ---")
    start_all = time.time()
    async with httpx.AsyncClient() as client:
        # Створюємо список асинхронних завдань
        tasks = []
        for i in range(10):
            tasks.append(client.get(f"{base_url}?scope=personal&iteration={i}"))
        # Виконуємо всі запити одночасно (паралельно)
        start_reqs = time.time()
        responses = await asyncio.gather(*tasks)
        end_reqs = time.time()
    end_all = time.time()
    total_time = end_all - start_all
    print(f"Всі {len(responses)} асинхронних запитів виконано паралельно.")
    print(f"Сумарний час на всі асинхронні запити: {total_time:.4f} сек\n")
if __name__ == "__main__":
    # 1. Запускаємо синхронний тест
    run_sync_benchmark()
    # 2. Запускаємо асинхронний тест
    asyncio.run(run_async_benchmark())
