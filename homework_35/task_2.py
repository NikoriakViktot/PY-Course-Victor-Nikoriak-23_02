import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


URL = "https://api.pushshift.io/reddit/comment/search/"


times = [
    1700000000,
    1690000000,
    1680000000,
]


def download_comments(before_time):

    params = {
        "subreddit": "python",
        "size": 100,
        "before": before_time
    }

    response = requests.get(URL, params=params)

    if responce.status_code != 200:
        return []

    data = responce.json().get("data", [])

    print(f'Downloaded {len(data)} comments')

    return data


if __name__ == "__main__":

    start = time.time()

    with ThreadPoolExecutor() as executor:
        thread_results = list(executor.map(download_comments, times))

    all_thread_comments = []

    for result in thread_results:
        all_thread_comments.extend(result)

    all_thread_comments.sort(key=lambda x: x["created_utc"])

    with open('thread_comments.json', 'w', encoding='utf-8') as f:
        json.dump(all_thread_comments, f, ensure_ascii=False, indent=4)

    end = time.time()

    print('\nThreads time:', end - start)


    start = time.time()
    with ProcessPoolExecutor() as executor:
        process_results = list(executor.map(download_comments, times))

    all_process_comments = []

    for result in process_results:
        all_process_comments.extend(result)

    all_process_comments.sort(key=lambda x: x["created_utc"])

    with open('process_comments.json', 'w', encoding='utf-8') as f:
        json.dump(all_process_comments, f, ensure_ascii=False, indent=4)

    end = time.time()

    print('\nProcess time:', end - start)

