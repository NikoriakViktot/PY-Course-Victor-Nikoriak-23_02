import json
import time
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_URL = "https://api.pushshift.io/reddit/comment/search/"
OUTPUT_FILE = Path(__file__).parent / "comments.json"


def request_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "python-homework-client"})

    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_comments(params: dict) -> list:
    query = urlencode(params)
    url = f"{API_URL}?{query}"

    try:
        response = request_json(url)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        print(f"Request failed: {error}")
        return []

    return response.get("data", [])


def create_time_ranges(days: int, workers: int) -> list:
    now = int(time.time())
    start_time = now - days * 24 * 60 * 60
    step = (now - start_time) // workers

    ranges = []

    for index in range(workers):
        after = start_time + step * index
        before = start_time + step * (index + 1)

        if index == workers - 1:
            before = now

        ranges.append((after, before))

    return ranges


def build_params(subreddit: str, limit: int, after: int, before: int) -> dict:
    return {
        "subreddit": subreddit,
        "size": limit,
        "after": after,
        "before": before,
        "sort": "asc",
        "sort_type": "created_utc",
    }


def download_with_threads(subreddit: str, total_limit: int, workers: int, days: int) -> list:
    limit_per_worker = max(1, total_limit // workers)
    time_ranges = create_time_ranges(days, workers)
    params_list = [
        build_params(subreddit, limit_per_worker, after, before)
        for after, before in time_ranges
    ]

    comments = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = executor.map(fetch_comments, params_list)

    for result in results:
        comments.extend(result)

    return comments


def download_with_processes(subreddit: str, total_limit: int, workers: int, days: int) -> list:
    limit_per_worker = max(1, total_limit // workers)
    time_ranges = create_time_ranges(days, workers)
    params_list = [
        build_params(subreddit, limit_per_worker, after, before)
        for after, before in time_ranges
    ]

    comments = []

    with Pool(processes=workers) as pool:
        results = pool.map(fetch_comments, params_list)

    for result in results:
        comments.extend(result)

    return comments


def remove_duplicates(comments: list) -> list:
    unique_comments = {}

    for comment in comments:
        comment_id = comment.get("id")

        if comment_id:
            unique_comments[comment_id] = comment

    return list(unique_comments.values())


def save_comments(comments: list) -> None:
    comments.sort(key=lambda comment: comment.get("created_utc", 0))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(comments, file, indent=4, ensure_ascii=False)


def main():
    subreddit = input("Enter subreddit name: ").strip() or "python"
    total_limit = int(input("Enter comments limit: ").strip() or 40)
    workers = int(input("Enter workers count: ").strip() or 4)
    days = int(input("Enter how many last days to search: ").strip() or 30)

    print("Downloading comments with ThreadPoolExecutor...")
    thread_comments = download_with_threads(subreddit, total_limit, workers, days)

    print("Downloading comments with multiprocessing.Pool...")
    process_comments = download_with_processes(subreddit, total_limit, workers, days)

    comments = remove_duplicates(thread_comments + process_comments)
    save_comments(comments)

    print(f"Saved {len(comments)} comments to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
