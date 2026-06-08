# Task 2
# Завантаження даних
# Завантажте всі коментарі з обраного вами субреддіту за посиланням:
# https://api.pushshift.io/reddit/comment/search/ .
# У результаті збережіть усі коментарі в хронологічному порядку у форматі JSON та
# запишіть їх у файл.
import json
import time
import requests
# Конфігурація запиту
SUBREDDIT = "learnpython"  # Оберіть будь-який сабреддіт
BASE_URL = "https://api.pushshift.io/reddit/comment/search/"
# Альтернативне робоче дзеркало, якщо офіційний Pushshift блокує запит:
# BASE_URL = "https://pullpush.io"
OUTPUT_FILE = "task2.json"
MAX_COMMENTS = 300  # Ліміт для демонстрації (можна збільшити)
all_comments = []
# Поточна часова мітка (завантажуємо коментарі від теперішнього моменту назад у минуле)
before_timestamp = int(time.time())
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Python/requests_script"
}
print(
    f"[START] Початок завантаження коментарів із r/{SUBREDDIT} за допомогою Pushshift API..."
)
while len(all_comments) < MAX_COMMENTS:
    # Параметри для API
    params = {
        "subreddit": SUBREDDIT,
        "size": 100,  # Максимально можливий розмір однієї порції
        "before": before_timestamp,
    }
    try:
        response = requests.get(BASE_URL, params=params, headers=headers, timeout=15)
        if response.status_code != 200:
            print(
                f"[УВАГА] Сервер повернув статус {response.status_code}. Перериваємо або перемикаємося."
            )
            break
        data = response.json()
        comments_batch = data.get("data", [])
        # Якщо нових коментарів немає — ми викачали все доступне
        if not comments_batch:
            print("[INFO] Нових даних більше немає.")
            break
        # Додаємо порцію до загального списку
        all_comments.extend(comments_batch)
        print(f"[PROGRESS] Завантажено коментарів: {len(all_comments)}")
        # Оновлюємо мітку часу на основі НАЙСТАРІШОГО коментаря в цій порції,
        # щоб наступний запит шукав дані, створені ще раніше.
        before_timestamp = comments_batch[-1]["created_utc"]
        # Пауза, щоб не навантажувати API (Rate Limiting)
        time.sleep(1.5)
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Помилка мережі: {e}")
        break
    except json.JSONDecodeError:
        print("[ERROR] Не вдалося розпарсити відповідь як JSON.")
        break
# Обрізаємо список до бажаного ліміту, якщо завантажилося трохи більше
all_comments = all_comments[:MAX_COMMENTS]
# Завдання вимагає хронологічного порядку (від найстаріших до найновіших).
# Pushshift за замовчуванням віддає дані у зворотному порядку (від нових до старих).
# Сортуємо список за ключем 'created_utc' (час створення у форматі Unix)
all_comments.sort(key=lambda x: x.get("created_utc", 0))
# Записуємо фінальний результат у файл json
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    # ensure_ascii=False зберігає емодзі та текст у нормальному вигляді (не як \uXXXX)
    json.dump(all_comments, f, indent=4, ensure_ascii=False)
print(
    f"[SUCCESS] Усі коментарі ({len(all_comments)} шт.) успішно відсортовано та збережено у файл '{OUTPUT_FILE}'!"
)