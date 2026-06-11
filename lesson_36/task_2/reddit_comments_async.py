import asyncio
import json
from pathlib import Path
from time import time

import aiohttp


API_URL = "https://api.pushshift.io/reddit/comment/search/"
OUTPUT_FILE = Path(__file__).parent / "comments.json"


async def fetch_comments(session, subreddit, before, size):
    params = {
        "subreddit": subreddit,
        "size": size,
        "before": before,
        "sort": "desc",
        "sort_type": "created_utc",
    }

    async with session.get(API_URL, params=params) as response:
        response.raise_for_status()
        result = await response.json()
        return result.get("data", [])


async def download_comments(subreddit, comments_limit):
    comments = []
    before = int(time())
    page_size = 100

    timeout = aiohttp.ClientTimeout(total=30)
    headers = {"User-Agent": "python-homework-asyncio-aiohttp"}

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        while len(comments) < comments_limit:
            current_size = min(page_size, comments_limit - len(comments))
            page_comments = await fetch_comments(session, subreddit, before, current_size)

            if not page_comments:
                break

            comments.extend(page_comments)
            before = min(comment["created_utc"] for comment in page_comments) - 1

    comments = comments[:comments_limit]
    comments.sort(key=lambda comment: comment.get("created_utc", 0))
    return comments


def save_comments(comments):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(comments, file, indent=4, ensure_ascii=False)


def main():
    subreddit = input("Enter subreddit name: ").strip()
    comments_limit = int(input("Enter comments limit: ").strip())

    comments = asyncio.run(download_comments(subreddit, comments_limit))
    save_comments(comments)

    print(f"Saved {len(comments)} comments to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
