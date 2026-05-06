import requests
import json
import time


url = 'https://api.pushshift.io/reddit/comment/search/'

params = {
    'subreddit': 'python',
    'size': 100,
}

all_comments = []

while True:
    response = requests.get(url, params=params)

    if response.status_code != 200:
        break

    data = response.json().get('data', [])

    if not data:
        break

    all_comments.extend(data)

    last_time = data[-1]['created_utc']

    params['before'] = last_time

    print(f'Завантажено: {len(all_comments)}')

    time.sleep(1)


all_comments.sort(key=lambda x: x['created_utc'])

with open('comments.json', 'w', encoding='utf-8') as f:
    json.dump(all_comments, f, ensure_ascii=False, indent=4)

print('Виконано')

with open('comments.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(len(data))