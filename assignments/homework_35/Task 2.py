# Task 2
# Запити з використанням бібліотек concurrent та multiprocessing
# Завантажте всі коментарі з обраного вами субреддіту за посиланням:
# https://api.pushshift.io/reddit/comment/search/ .
# У результаті збережіть усі коментарі в хронологічному порядку у форматі JSON та
# запишіть їх у файл. Для виконання цього завдання використовуйте бібліотеки concurrent
# та multiprocessing для надсилання запитів до API Reddit.
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import time
import requests
# Константи для конфігурації
SUBREDDIT = "python"
BASE_URL = "https://api.pushshift.io/reddit/comment/search/"
MAX_WORKERS = 4  # Кількість паралельних процесів
def fetch_comments_chunk(before_timestamp: int) -> list:
    """Функція виконується в окремому процесі.
    Робить один запит до API для вказаного часового проміжку.
    """
    params = {
        "subreddit": SUBREDDIT,
        "size": 100,  # Максимальний ліміт для Pushshift API
        "before": before_timestamp,
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json().get("data", [])
            return data
        elif response.status_code == 429:
            print(f"[Процес] Помилка 429 (Too Many Requests) для {before_timestamp}. Потрібна пауза.")
            return []
        else:
            print(f"[Процес] Помилка API: Статус {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"[Процес] Помилка мережі: {e}")
        return []
def main():
    # 1. Формуємо список завдань (часових міток для пагінації назад у часі)
    current_time = int(time.time())
    # Генеруємо мітки з кроком в 1 годину (3600 секунд) для паралельних процесів
    timestamps = [current_time - (i * 3600) for i in range(MAX_WORKERS * 2)]
    all_comments = []
    print(
        f"[СТАРТ] Запуск ProcessPoolExecutor з {MAX_WORKERS} процесами для r/{SUBREDDIT}..."
    )
    start_time = time.perf_counter()
    # 2. Використовуємо ProcessPoolExecutor для паралельного виконання запитів
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Запускаємо завдання та створюємо словник для відстеження майбутніх результатів (Futures)
        future_to_timestamp = {
            executor.submit(fetch_comments_chunk, ts): ts for ts in timestamps
        }
        # Отримуємо результати в міру їхнього завершення (as_completed)
        for future in as_completed(future_to_timestamp):
            ts = future_to_timestamp[future]
            try:
                data = future.result()
                if data:
                    all_comments.extend(data)
                    print(
                        f"[УСПІХ] Завантажено {len(data)} коментарів для зміщення {ts}."
                    )
            except Exception as exc:
                print(f"[ПОМИЛКА] Запит для мітки {ts} викликав виняток: {exc}")
    end_time = time.perf_counter()
    print(
        f"\n[ОБРОБКА] Запити завершено за {end_time - start_time:.2f} сек. Отримано всього: {len(all_comments)}."
    )
    # 3. Сортування в хронологічному порядку за полем 'created_utc'
    print("[СОРТУВАННЯ] Сортуємо коментарі за часом створення...")
    all_comments.sort(key=lambda x: x.get("created_utc", 0))
    # 4. Запис у JSON файл
    output_filename = f"{SUBREDDIT}_multiprocessing_comments.json"
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(all_comments, f, ensure_ascii=False, indent=4)
        print(f"✅ [ЗБЕРЕЖЕНО] Результат записано у файл: '{output_filename}'")
    except IOError as e:
        print(f"Помилка запису файлу: {e}")
if __name__ == "__main__":
    main()