import requests
import json

SUBREDDIT = "python"
URL = "https://api.pushshift.io/reddit/comment/search/"

params = {
    "subreddit": SUBREDDIT,
    "size": 100,   # max per request
    "sort": "asc",
    "sort_type": "created_utc"
}

response = requests.get(URL, params=params)
data = response.json()

comments = data.get("data", [])

# sort just in case
comments = sorted(comments, key=lambda x: x["created_utc"])

output_file = f"{SUBREDDIT}_comments.json"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(comments, f, indent=4)

print(f"Saved {len(comments)} comments to {output_file}")