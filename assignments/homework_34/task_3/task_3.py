from concurrent.futures import ThreadPoolExecutor
import json
import requests

URL = "https://api.pullpush.io/reddit/search/comment/"
NUM_THREADS = 4

# Кожен потік завантажить останні коментарі зі свого популярного сабреддіту.
# Це працює миттєво і не викликає перевантаження сервера.
SUBREDDITS = ["python", "learnprogramming", "coding", "technology"]


def fetch_latest_comments(subreddit_name):
    """Функція для одного потоку. Завантажує останні 25 коментарів з конкретного сабреддіту."""
    params = {
        "subreddit": subreddit_name,
        "size": 25,  # Невеликий розмір пакета, щоб сервер віддав його моментально
        "sort": "asc",  # Сортуємо хронологічно
    }

    try:
        # Робимо звичайний HTTP-запит
        response = requests.get(URL, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json().get("data", [])
            print(
                f"[Потік] Успішно завантажено {len(data)} коментарів з r/{subreddit_name}"
            )
            return data
        else:
            print(
                f"[Помилка API] r/{subreddit_name} повернув статус {response.status_code}"
            )
            return []
    except requests.exceptions.RequestException as e:
        print(f"[Помилка мережі для r/{subreddit_name}]: {e}")
        return []


def main():
    all_comments = []

    print(f"Запуск {NUM_THREADS} потоків для збору коментарів через PullPush API...\n")

    # Створюємо пул потоків
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        # Розподіляємо сабреддіти по потоках
        futures = [
            executor.submit(fetch_latest_comments, sub) for sub in SUBREDDITS
        ]

        # Збираємо результати виконання всіх потоків
        for future in futures:
            result = future.result()
            all_comments.extend(result)

    print(f"\nВсього зібрано коментарів з усіх потоків: {len(all_comments)}")

    if all_comments:
        # Обов'язкова умова завдання: сортуємо ВСІ коментарі в хронологічному порядку за Unix-часом
        all_comments_sorted = sorted(
            all_comments, key=lambda x: x.get("created_utc", 0)
        )

        # Записуємо результат у JSON-файл
        filename = "reddit_pullpush_multithreaded.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(all_comments_sorted, f, indent=4, ensure_ascii=False)

        print(f"Дані успішно відсортовано та збережено у файл: {filename}")
    else:
        print("Не вдалося зібрати дані з Reddit.")


if __name__ == "__main__":
    main()
