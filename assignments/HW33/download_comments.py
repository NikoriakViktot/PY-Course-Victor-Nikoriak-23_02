import requests
import json

subreddit = "python"
url = f"https://api.pushshift.io/reddit/comment/search/?subreddit={subreddit}&size=100&sort=asc"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()["data"]

    # сортуємо коментарі за часом
    data_sorted = sorted(data, key=lambda x: x["created_utc"])

    # зберігаємо у файл
    with open(f"{subreddit}_comments.json", "w", encoding="utf-8") as f:
        json.dump(data_sorted, f, ensure_ascii=False, indent=2)

    print(f"✅ Збережено {len(data_sorted)} коментарів у {subreddit}_comments.json")
else:
    print(f"⚠️ Помилка: {response.status_code}")
