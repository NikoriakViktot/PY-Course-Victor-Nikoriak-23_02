import json
import time
import urllib.parse
import urllib.request
from threading import Lock, Thread


API_URL = "https://api.pushshift.io/reddit/comment/search/"


def build_url(subreddit, size, before):
    query_params = {
        "subreddit": subreddit,
        "size": size,
        "before": before,
        "sort": "desc",
        "sort_type": "created_utc",
    }
    return f"{API_URL}?{urllib.parse.urlencode(query_params)}"


def fetch_comments(subreddit, size, before, comments, lock):
    url = build_url(subreddit, size, before)

    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            response_data = response.read().decode("utf-8")
            data = json.loads(response_data)
    except Exception as error:
        print(f"Request failed: {error}")
        return

    downloaded_comments = data.get("data", [])

    with lock:
        comments.extend(downloaded_comments)


def save_comments(comments, filename):
    unique_comments = {}

    for comment in comments:
        comment_id = comment.get("id")

        if comment_id:
            unique_comments[comment_id] = comment

    sorted_comments = sorted(
        unique_comments.values(),
        key=lambda comment: comment.get("created_utc", 0),
    )

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(sorted_comments, file, indent=4, ensure_ascii=False)

    return len(sorted_comments)


def main():
    subreddit = input("Enter subreddit name: ").strip()
    total_comments = int(input("Enter comments limit: ").strip())
    threads_count = int(input("Enter number of threads: ").strip())

    if total_comments <= 0:
        raise ValueError("Comments limit must be greater than zero")

    if threads_count <= 0:
        raise ValueError("Number of threads must be greater than zero")

    comments = []
    lock = Lock()
    threads = []

    comments_per_thread = max(1, total_comments // threads_count)
    current_time = int(time.time())

    for index in range(threads_count):
        before = current_time - index * 86400

        thread = Thread(
            target=fetch_comments,
            args=(subreddit, comments_per_thread, before, comments, lock),
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    saved_count = save_comments(comments, "comments.json")
    print(f"Saved {saved_count} comments to comments.json")


if __name__ == "__main__":
    main()
