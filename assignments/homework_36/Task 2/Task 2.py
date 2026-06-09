# Запити з використанням asyncio та aiohttp
# Завантажте всі коментарі з обраного вами субреддіту за посиланням:
# https://api.pushshift.io/reddit/comment/search/ .
# У результаті збережіть усі коментарі в хронологічному порядку у форматі JSON та
# запишіть їх у файл. Для виконання цього завдання використовуйте бібліотеки asyncio
# та aiohttp для надсилання запитів до API Reddit.

import asyncio
import json
import time
import aiohttp
# константи конфігурації (всі в нижньому регістрі)
subreddit_name = "python"
base_url = "https://api.pushshift.io/reddit/comment/search/"
max_requests = 4  # кількість паралельних запитів
async def fetch_comments_chunk(session, before_timestamp):
    """Корутина для виконання одного асинхронного запиту до API."""
    params = {
        "subreddit": subreddit_name,
        "size": 100,  # ліміт результатів для pushshift api
        "before": before_timestamp,
    }
    try:
        # робимо асинхронний get-запит
        async with session.get(base_url, params=params, timeout=10) as response:
            if response.status == 200:
                # асинхронно зчитуємо та парсимо json
                json_data = await response.json()
                data_chunk = json_data.get("data", [])
                return data_chunk
            elif response.status == 429:
                print(
                    f"[асинхронно] помилка 429 (too many requests) для {before_timestamp}."
                )
                return []
            else:
                print(f"[асинхронно] помилка api, статус: {response.status}")
                return []
    except Exception as error:
        print(f"[асинхронно] помилка мережі: {error}")
        return []
async def main():
    current_time = int(time.time())
    # генеруємо часові мітки для пагінації назад у часі з кроком в 1 годину (3600 сек)
    timestamps = [current_time - (i * 3600) for i in range(max_requests * 2)]
    all_comments = []
    print(
        f"[старт] запуск asyncio + aiohttp для збору коментарів з r/{subreddit_name}..."
    )
    start_time = time.perf_counter()
    # створюємо одну клієнтську сесію для повторного використання TCP-з'єднань
    async with aiohttp.ClientSession() as session:
        # створюємо список асинхронних завдань (tasks)
        tasks = [fetch_comments_chunk(session, ts) for ts in timestamps]
        # запускаємо всі завдання паралельно за допомогою asyncio.gather
        results = await asyncio.gather(*tasks)
        # об'єднуємо результати з усіх успішних запитів
        for data_chunk in results:
            if data_chunk:
                all_comments.extend(data_chunk)
    end_time = time.perf_counter()
    print(
        f"\n[обробка] запити завершено за {end_time - start_time:.2f} сек."
    )
    print(f"отримано всього коментарів: {len(all_comments)}")
    # сортування коментарів у хронологічному порядку за полем 'created_utc'
    print("[сортування] впорядкування коментарів за часом створення...")
    all_comments.sort(key=lambda x: x.get("created_utc", 0))
    # запис результату в json файл
    output_filename = f"{subreddit_name}_asyncio_comments.json"
    try:
        with open(output_filename, "w", encoding="utf-8") as file_object:
            json.dump(all_comments, file_object, ensure_ascii=False, indent=4)
        print(
            f"✅ [успіх] усі коментарі успішно збережено у файл: '{output_filename}'"
        )
    except IOError as io_error:
        print(f"помилка під час запису файлу: {io_error}")
if __name__ == "__main__":
    # запуск головного циклу подій (event loop)
    asyncio.run(main())