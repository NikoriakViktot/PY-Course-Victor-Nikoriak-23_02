import json
import threading
import requests

all_comments = []
list_lock = threading.Lock()

def fetch_comments_by_post(post_id):
    url = f"https://jsonplaceholder.typicode.com/comments?postId={post_id}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            with list_lock:
                all_comments.extend(data)
            print(f"[ПОТІК] Завантажено коментарі для поста {post_id}")
    except Exception as e:
        print(f"Помилка у потоці для поста {post_id}: {e}")

def main():
    threads = []
    for i in range(1, 6):
        t = threading.Thread(target=fetch_comments_by_post, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    sorted_comments = sorted(all_comments, key=lambda x: x['id'])

    with open("multithreaded_comments.json", "w", encoding="utf-8") as f:
        json.dump(sorted_comments, f, ensure_ascii=False, indent=4)

    print(f"\n[ГОТОВО] Загалом завантажено {len(sorted_comments)} коментарів та збережено в 'multithreaded_comments.json'.")

if __name__ == "__main__":
    main()