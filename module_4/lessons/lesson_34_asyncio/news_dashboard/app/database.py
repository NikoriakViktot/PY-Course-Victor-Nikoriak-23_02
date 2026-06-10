from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB  = os.environ.get("MONGODB_DB", "news_db")

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGODB_URL)
    return _client


def get_db():
    return get_client()[MONGODB_DB]


async def init_db():
    db = get_db()
    await db.news.create_index("url", unique=True)
    await db.scrape_jobs.create_index("job_id")
