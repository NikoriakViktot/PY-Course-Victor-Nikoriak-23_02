# Запити з використанням багатопотоковості
# Завантажте всі коментарі з обраного вами субреддіту за посиланням:
# https://api.pushshift.io/reddit/comment/search/ .
# У результаті збережіть усі коментарі в хронологічному порядку у форматі JSON та
# запишіть їх у файл. Для виконання цього завдання використовуйте бібліотеку Threads
# для надсилання запитів до API Reddit.
import json
import queue
import sys
import threading
import time
import requests
# Константи за замовчуванням
SUBREDDIT = "python"  # Сабреддіт, з якого збираємо дані
BASE_URL = "https://api.pushshift.io/reddit/comment/search/"
NUM_THREADS = 4  # Кількість паралельних потоків для запитів
MAX_COMMENTS = 500  # Скільки всього коментарів ми хочемо зібрати для тесту
# Спільні ресурси для потоків
# Потокобезпечна черга для збереження часових проміжків (пагінації)
time_chunks_queue = queue.Queue()
# Список для збереження всіх отриманих коментарів
all_comments = []
# Lock для безпечного додавання даних у загальний список з різних потоків
list_lock = threading.Lock()
def worker():
    """Функція, яку виконує кожен окремий потік."""
    while not time_chunks_queue.empty():
        try:
            # Отримуємо часову мітку з черги (без блокування, щоб потік не зависав)
            before_timestamp = time_chunks_queue.get_nowait()
        except queue.Empty:
            break
        # Параметри для API запиту
        params = {
            "subreddit": SUBREDDIT,
            "size": 100,  # Максимальна кількість результатів на один запит
            "before": before_timestamp,
        }
        try:
            print(
                f"[{threading.current_thread().name}] Робить запит для timestamp < {before_timestamp}..."
            )
            response = requests.get(BASE_URL, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json().get("data", [])
                if not data:
                    print(
                        f"[{threading.current_thread().name}] Дані відсутні для цього проміжку."
                    )
                    time_chunks_queue.task_done()
                    continue
                # Безпечно додаємо отримані коментарі до загального списку
                with list_lock:
                    all_comments.extend(data)
                print(
                    f"[{threading.current_thread().name}] Успішно завантажено {len(data)} коментарів."
                )
            elif response.status_code == 429:
                print(
                    f"[{threading.current_thread().name}] Помилка 429: Too Many Requests. Повертаємо мітку в чергу."
                )
                time_chunks_queue.put(before_timestamp)
                time.sleep(2)  # Пауза у випадку ліміту запитів
            else:
                print(
                    f"[{threading.current_thread().name}] Помилка API: Статус {response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            print(
                f"[{threading.current_thread().name}] Помилка мережі: {e}. Повертаємо мітку в чергу."
            )
            time_chunks_queue.put(before_timestamp)
        # Позначаємо завдання в черзі як виконане
        time_chunks_queue.task_done()
        time.sleep(1)  # Ввічливий інтервал між запитами одного потоку
def main():
    # 1. Заповнюємо чергу початковими часовими точками для пагінації назад у часі
    # Починаємо з поточного моменту часу
    current_time = int(time.time())
    # Кожен крок відступає назад приблизно на 1 годину (3600 сек) або використовує динамічний підхід.
    # Для демонстрації згенеруємо мітки пагінації
    for i in range(NUM_THREADS * 2):
        time_chunks_queue.put(current_time - (i * 3600))
    print(
        f"[СТАРТ] Починаємо збір коментарів з r/{SUBREDDIT} у {NUM_THREADS} потоків..."
    )
    # 2. Створюємо та запускаємо потоки
    threads = []
    for i in range(NUM_THREADS):
        t = threading.Thread(target=worker, name=f"Thread-{i+1}")
        threads.append(t)
        t.start()
    # 3. Чекаємо завершення роботи всіх потоків
    for t in threads:
        t.join()
    print(f"\n[ОБРОБКА] Усі потоки завершили роботу. Отримано всього: {len(all_comments)} коментарів.")
    # 4. Сортування в хронологічному порядку (від найстарішого до найновішого)
    # Коментарі в Reddit/Pushshift мають поле 'created_utc'
    print("[СОРТУВАННЯ] Сортуємо коментарі за часом...")
    all_comments.sort(key=lambda x: x.get("created_utc", 0))
    # 5. Запис результату в JSON файл
    output_filename = f"{SUBREDDIT}_comments.json"
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(all_comments, f, ensure_ascii=False, indent=4)
        print(
            f"✅ [УСПІХ] Усі коментарі успішно збережено у файл: '{output_filename}'"
        )
    except IOError as e:
        print(f"Помилка під час запису файлу: {e}")
if __name__ == "__main__":
    main()