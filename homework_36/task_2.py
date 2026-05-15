import asyncio
import aiohttp
import json


URL = "https://api.pushshift.io/reddit/comment/search/"


async def fetch(session, params):
    async with session.get(URL, params=params) as response:
        if response.status != 200:
            return []

        data = await response.json()
        return data.get('data', [])


async def get_comments(subreddit, limit=500):
    all_comments = []
    before = None

    async with aiohttp.ClientSession() as session:
        while len(all_comments) < limit:
            params = {
                'subreddit': subreddit,
                'size': 100,
            }

            if before:
                params['before'] = before

            comments = await fetch(session, params)

            if not comments:
                break

            all_comments.extend(comments)

            before = comments[-1]['created_utc'] - 1

            print(f'Downloaded {len(all_comments)} comments')

            await asyncio.sleep(0.2)

    return all_comments


def sort_comments(comments):
    return sorted(comments, key=lambda c: c['created_utc'])


def save_to_json(data, filename='comments.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


async def main():
    subreddit = 'python'

    comments = await get_comments(subreddit, limit=300)
    sorted_comments = sort_comments(comments)

    save_to_json(sorted_comments)

    print(f'Saved {len(sorted_comments)} comments to file')

if __name__ == "__main__":
    asyncio.run(main())