import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

URL = "https://api.pushshift.io/reddit/comment/search/"
SUBREDDIT = "python"
LIMIT = 50


def fetch_comments(before=None):
    params = {
        "subreddit": SUBREDDIT,
        "size": LIMIT,
        "sort": "desc",
        "sort_type": "created_utc",
    }
    if before:
        params["before"] = before

    response = requests.get(URL, params=params)
    data = response.json().get("data", [])
    return data


def collect_comments(worker):
    comments = []
    before = None

    with worker(max_workers=5) as executor:
        futures = []

        for _ in range(5):  # pages
            futures.append(executor.submit(fetch_comments, before))

        for future in as_completed(futures):
            batch = future.result()
            comments.extend(batch)

            if batch:
                before = min(c["created_utc"] for c in batch)

    comments.sort(key=lambda x: x["created_utc"])
    return comments


def run(worker, name):
    start = time.time()
    comments = collect_comments(worker)

    with open(f"{name}_comments.json", "w", encoding="utf-8") as f:
        json.dump(comments, f, indent=2)

    print(f"{name}: saved {len(comments)} comments in {time.time() - start:.2f}s")


if __name__ == "__main__":
    run(ThreadPoolExecutor, "threading")
    run(ProcessPoolExecutor, "multiprocessing")