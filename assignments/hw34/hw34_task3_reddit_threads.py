import requests
import threading
import json

URL = "https://api.pushshift.io/reddit/comment/search/"
SUBREDDIT = "python"

NUM_THREADS = 5
SIZE = 50

all_comments = []
lock = threading.Lock()


def fetch_comments(thread_id):
    params = {
        "subreddit": SUBREDDIT,
        "size": SIZE,
        "sort": "asc",
        "sort_type": "created_utc",
        "before": None if thread_id == 0 else 1700000000 - thread_id * 10000
    }

    response = requests.get(URL, params=params)
    data = response.json()

    comments = data.get("data", [])

    with lock:
        all_comments.extend(comments)

    print(f"Thread {thread_id} finished: {len(comments)} comments")


threads = []

for i in range(NUM_THREADS):
    t = threading.Thread(target=fetch_comments, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

# sort results
all_comments.sort(key=lambda x: x.get("created_utc", 0))

with open("reddit_comments_threads.json", "w", encoding="utf-8") as f:
    json.dump(all_comments, f, indent=4)

print("Saved comments:", len(all_comments))