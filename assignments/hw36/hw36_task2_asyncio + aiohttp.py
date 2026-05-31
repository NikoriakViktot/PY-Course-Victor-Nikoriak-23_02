import asyncio
import aiohttp
import json

URL = "https://api.pushshift.io/reddit/comment/search/"
SUBREDDIT = "python"
LIMIT = 50
PAGES = 5


async def fetch(session, before=None):
    params = {
        "subreddit": SUBREDDIT,
        "size": LIMIT,
        "sort": "desc",
        "sort_type": "created_utc",
    }

    if before:
        params["before"] = before

    async with session.get(URL, params=params) as resp:
        data = await resp.json()
        return data.get("data", [])


async def main():
    comments = []
    before = None

    async with aiohttp.ClientSession() as session:
        tasks = []

        for _ in range(PAGES):
            tasks.append(fetch(session, before))

        results = await asyncio.gather(*tasks)

        for batch in results:
            comments.extend(batch)

    comments.sort(key=lambda x: x["created_utc"])

    with open("comments_async.json", "w", encoding="utf-8") as f:
        json.dump(comments, f, indent=2)

    print(f"Saved {len(comments)} comments")


if __name__ == "__main__":
    asyncio.run(main())