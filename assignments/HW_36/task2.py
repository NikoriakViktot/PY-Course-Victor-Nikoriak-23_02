import asyncio
import json
import aiohttp

BASE_URL = "https://jsonplaceholder.typicode.com/comments"


async def fetch_comments(session, post_id):
    url = f"{BASE_URL}?postId={post_id}"
    try:
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                return await response.json()
    except Exception as e:
        print(f"Помилка завантаження поста {post_id}: {e}")
    return []


async def main():
    post_ids = list(range(1, 11))  # перші 10 постів

    print("[СТАРТ] Починаємо асинхронне завантаження через aiohttp...")

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_comments(session, pid) for pid in post_ids]
        results = await asyncio.gather(*tasks)

    all_comments = []
    for comments_list in results:
        all_comments.extend(comments_list)

    sorted_comments = sorted(all_comments, key=lambda x: x['id'])

    with open("async_comments.json", "w", encoding="utf-8") as f:
        json.dump(sorted_comments, f, ensure_ascii=False, indent=4)

    print(f"[УСПІХ] Завантажено та збережено {len(sorted_comments)} коментарів у файл 'async_comments.json'.")


if __name__ == '__main__':
    asyncio.run(main())