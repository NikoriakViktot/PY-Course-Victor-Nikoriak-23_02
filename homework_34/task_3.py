import requests
import json
from threading import Thread, Lock


url = "https://api.pushshift.io/reddit/comment/search/"

all_comments = []
lock = Lock()


def download_comments(before_time):
    params = {
        'subreddit': 'python',
        'size': 100,
        'before': before_time
    }

    response = requests.get(url, params = params)


    if response.status_code != 200:
        return

    data = response.json().get('data', [])

    with lock:
        all_comments.extend(data)

    print(f'Downloaded {len(data)} comments')


threads = []

times = [
    1700000000,
    1690000000,
    1680000000
]


for time in times:
    thread = Thread(target = download_comments, args = (time,))
    threads.append(thread)
    thread.start()


for thread in threads:
    thread.join()


all_comments.sort(key = lambda x: x['created_utc'])


with open('comments.json', 'w', encoding = 'utf-8') as f:
    json.dump(all_comments, f, ensure_ascii = False, indent = 4)


print('Done')