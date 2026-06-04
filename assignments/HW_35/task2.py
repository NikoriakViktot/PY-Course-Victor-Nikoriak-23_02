import json
import time
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import requests

BASE_URL = "https://jsonplaceholder.typicode.com/comments"


def fetch_post_comments(post_id):
    url = f"{BASE_URL}?postId={post_id}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Помилка завантаження для поста {post_id}: {e}")
    return []


def run_with_threads(post_ids):
    print("[СТАРТ] Завантаження через ThreadPoolExecutor...")
    start_time = time.perf_counter()

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(fetch_post_comments, post_ids))

    all_comments = []
    for comments_list in results:
        all_comments.extend(comments_list)

    print(f"[ПОТОКИ] Час виконання: {time.perf_counter() - start_time:.4f} сек.")
    return all_comments


def run_with_multiprocessing(post_ids):
    print("[СТАРТ] Завантаження через multiprocessing.Pool...")
    start_time = time.perf_counter()

    with multiprocessing.Pool(processes=4) as pool:
        results = pool.map(fetch_post_comments, post_ids)

    all_comments = []
    for comments_list in results:
        all_comments.extend(comments_list)

    print(f"[ПРОЦЕСИ] Час виконання: {time.perf_counter() - start_time:.4f} сек.")
    return all_comments


if __name__ == '__main__':
    post_ids = list(range(1, 16))
    comments = run_with_threads(post_ids)
    sorted_comments = sorted(comments, key=lambda x: x['id'])
    output_filename = "reddit_comments.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(sorted_comments, f, ensure_ascii=False, indent=4)

    print(f"\n[УСПІХ] Всього збережено {len(sorted_comments)} коментарів у файл '{output_filename}'.")