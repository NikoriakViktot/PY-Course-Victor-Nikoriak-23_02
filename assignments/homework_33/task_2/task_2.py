import json
import time
import requests

# Налаштування параметрів
SUBREDDIT = "python"  # Сабреддіт, з якого збираємо дані
LIMIT = 100  # Скільки коментарів завантажити за раз (макс. 100)

# Використовуємо робоче дзеркало api.pullpush.io (ідентичне pushshift за структурою)
URL = "https://api.pullpush.io/reddit/search/comment/"

# Параметри HTTP-запиту
params = {
    "subreddit": SUBREDDIT,
    "size": LIMIT,
    "sort": "asc",  # Сортування: спочатку старі, потім нові (хронологічно)
}

print(f"Надсилання HTTP-запиту до API для сабреддіту r/{SUBREDDIT}...")

try:
    # Робимо GET-запит
    response = requests.get(URL, params=params, timeout=10)

    # Перевіряємо статус відповіді (200 OK)
    if response.status_code == 200:
        json_data = response.json()

        # Витягуємо безпосередньо список коментарів із ключа 'data'
        comments = json_data.get("data", [])

        if not comments:
            print("Коментарів не знайдено або API повернув порожній список.")
        else:
            print(f"Успішно отримано {len(comments)} коментарів.")

            # Додатково гарантуємо хронологічний порядок за Unix-часом ('created_utc')
            comments_sorted = sorted(comments, key=lambda x: x.get("created_utc", 0))

            # Назва вихідного файлу
            filename = f"{SUBREDDIT}_comments.json"

            # Записуємо дані у файл у форматі JSON з відступами
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(comments_sorted, f, indent=4, ensure_ascii=False)

            print(f"Дані успішно збережено у файл: {filename}")
    else:
        print(
            f"Помилка сервера. Статус-код: {response.status_code}. "
            f"Відповідь: {response.text}"
        )

except requests.exceptions.RequestException as e:
    print(f"Помилка при виконанні HTTP-запиту: {e}")
