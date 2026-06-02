from __future__ import annotations

import uuid
from collections import Counter
from datetime import date, datetime
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from archive_scraper import run_archive_scrape
from database import get_db, init_db
from scraper import scrape_all_async, scrape_sequential

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="News Dashboard API",
    description="Async news scraper + FastAPI + MongoDB. Lesson 34 — asyncio.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    await init_db()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class NewsItem(BaseModel):
    id: str
    title: str
    url: str
    category: str
    description: str
    pub_date: Optional[datetime]
    scraped_at: datetime
    source: str
    sentiment_score: float
    keywords: list[str]
    word_count: int
    entities: list[dict] = []
    lang: str = "unknown"


class ScrapeRequest(BaseModel):
    mode: str = Field(default="async", pattern="^(async|sequential)$")
    pages: Optional[list[str]] = None


class ScrapeResult(BaseModel):
    mode: str
    total_time: float
    pages_count: int
    news_saved: int
    news_total: int
    gantt_data: list[dict]  # [{url, start, end, count, error}]


class ArchiveScrapeRequest(BaseModel):
    start_date: date
    end_date: date
    max_concurrent: int = Field(default=15, ge=1, le=50)
    batch_size: int = Field(default=30, ge=1, le=100)
    batch_delay: float = Field(default=1.0, ge=0.0, le=10.0)


class ArchiveJobStatus(BaseModel):
    job_id: str
    status: str
    start_date: str
    end_date: str
    total_days: int
    days_done: int
    articles_saved: int
    articles_skipped: int
    errors: int
    progress_pct: float
    started_at: Optional[datetime]
    finished_at: Optional[datetime]


# ---------------------------------------------------------------------------
# Helper: serialize MongoDB document to NewsItem dict
# ---------------------------------------------------------------------------


def _doc_to_item(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "title": doc.get("title", ""),
        "url": doc.get("url", ""),
        "category": doc.get("category", ""),
        "description": doc.get("description", ""),
        "pub_date": doc.get("pub_date"),
        "scraped_at": doc.get("scraped_at"),
        "source": doc.get("source", ""),
        "sentiment_score": doc.get("sentiment_score", 0.0),
        "keywords": doc.get("keywords", []),
        "word_count": doc.get("word_count", 0),
        "entities": doc.get("entities", []),
        "lang": doc.get("lang", "unknown"),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/scrape", response_model=ScrapeResult)
async def scrape(request: ScrapeRequest):
    """
    Scrape rbc.ua pages and save results to MongoDB.
    mode='async'  — concurrent (asyncio.gather)
    mode='sequential' — one by one (for comparison demo)
    """
    if request.mode == "sequential":
        result = await scrape_sequential(request.pages)
    else:
        result = await scrape_all_async(request.pages)

    db = get_db()
    saved = 0
    for item in result["news"]:
        doc = {k: v for k, v in item.items() if k != "_id"}
        url = doc.get("url", "")
        if not url:
            continue
        res = await db.news.update_one(
            {"url": url},
            {"$setOnInsert": doc},
            upsert=True,
        )
        if res.upserted_id is not None:
            saved += 1

    gantt_data = [
        {
            "url": pr["url"],
            "start": round(pr["start"], 3),
            "end": round(pr["end"], 3),
            "count": pr["count"],
            "error": pr["error"],
        }
        for pr in result["page_results"]
    ]

    return ScrapeResult(
        mode=request.mode,
        total_time=round(result["total_time"], 3),
        pages_count=result["pages_count"],
        news_saved=saved,
        news_total=result["news_count"],
        gantt_data=gantt_data,
    )


@app.get("/api/news", response_model=list[NewsItem])
async def list_news(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=1000),
    category: str = Query(default=""),
    source: str = Query(default=""),
    lang: str = Query(default="", description="uk | ru | unknown"),
):
    """Return paginated news list with optional filters."""
    db = get_db()
    query: dict = {}
    if category:
        query["category"] = category
    if source:
        query["source"] = source
    if lang:
        query["lang"] = lang

    cursor = db.news.find(query).sort("scraped_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [_doc_to_item(d) for d in docs]


@app.get("/api/news/count")
async def news_count():
    """Total number of news documents in the database."""
    db = get_db()
    total = await db.news.count_documents({})
    return {"count": total}


@app.get("/api/news/stats")
async def news_stats():
    """
    Aggregated statistics:
    - categories with article counts
    - sentiment distribution (positive / neutral / negative)
    - average sentiment
    """
    db = get_db()

    # Category counts
    cat_pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20},
    ]
    cat_docs = await db.news.aggregate(cat_pipeline).to_list(length=20)
    categories = [{"category": d["_id"] or "Загальні", "count": d["count"]} for d in cat_docs]

    # Sentiment distribution
    sent_pipeline = [
        {
            "$group": {
                "_id": None,
                "positive": {"$sum": {"$cond": [{"$gt": ["$sentiment_score", 0]}, 1, 0]}},
                "neutral": {"$sum": {"$cond": [{"$eq": ["$sentiment_score", 0]}, 1, 0]}},
                "negative": {"$sum": {"$cond": [{"$lt": ["$sentiment_score", 0]}, 1, 0]}},
                "avg_sentiment": {"$avg": "$sentiment_score"},
                "total": {"$sum": 1},
            }
        }
    ]
    sent_docs = await db.news.aggregate(sent_pipeline).to_list(length=1)
    sentiment = sent_docs[0] if sent_docs else {
        "positive": 0, "neutral": 0, "negative": 0, "avg_sentiment": 0.0, "total": 0
    }
    sentiment.pop("_id", None)

    return {"categories": categories, "sentiment": sentiment}


@app.get("/api/news/keywords")
async def news_keywords():
    """Top 30 keywords aggregated across all articles."""
    db = get_db()
    pipeline = [
        {"$unwind": "$keywords"},
        {"$group": {"_id": "$keywords", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 30},
    ]
    docs = await db.news.aggregate(pipeline).to_list(length=30)
    return [{"keyword": d["_id"], "count": d["count"]} for d in docs]


@app.get("/api/news/timeline")
async def news_timeline(group_by: str = Query(default="day", pattern="^(day|month|year)$")):
    """News article count + avg sentiment grouped by pub_date or scraped_at."""
    db = get_db()
    fmt = {"day": "%Y-%m-%d", "month": "%Y-%m", "year": "%Y"}[group_by]
    pipeline = [
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": fmt,
                        # Use pub_date if it's a real Date, else scraped_at
                        "date": {
                            "$cond": {
                                "if": {"$and": [
                                    {"$ne": ["$pub_date", None]},
                                    {"$eq": [{"$type": "$pub_date"}, "date"]},
                                ]},
                                "then": "$pub_date",
                                "else": "$scraped_at",
                            }
                        },
                    }
                },
                "count": {"$sum": 1},
                "avg_sentiment": {"$avg": "$sentiment_score"},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    docs = await db.news.aggregate(pipeline).to_list(length=2000)
    return [
        {
            "date": d["_id"],
            "count": d["count"],
            "avg_sentiment": round(d.get("avg_sentiment") or 0.0, 3),
        }
        for d in docs
        if d["_id"]
    ]


# ---------------------------------------------------------------------------
# Entity endpoints
# ---------------------------------------------------------------------------


@app.get("/api/news/entities")
async def top_entities(
    entity_type: str = Query(default="", description="PER | ORG | LOC | GPE | MISC | (empty=all)"),
    limit: int = Query(default=30, ge=1, le=100),
):
    """
    Top entities aggregated across all articles.
    GET /api/news/entities?entity_type=PER&limit=20
    Returns: [{"text": "Зеленський", "label": "PER", "count": 42}, ...]
    """
    db = get_db()
    match: dict = {"entities": {"$exists": True, "$ne": []}}
    if entity_type:
        match["entities.label"] = entity_type.upper()

    pipeline = [
        {"$match": match},
        {"$unwind": "$entities"},
    ]
    if entity_type:
        pipeline.append({"$match": {"entities.label": entity_type.upper()}})
    pipeline += [
        {"$group": {
            "_id": {"text": "$entities.text", "label": "$entities.label"},
            "count": {"$sum": 1},
        }},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    docs = await db.news.aggregate(pipeline).to_list(length=limit)
    return [
        {"text": d["_id"]["text"], "label": d["_id"]["label"], "count": d["count"]}
        for d in docs
    ]


@app.get("/api/news/entity-trend")
async def entity_trend(
    entity: str = Query(min_length=2, max_length=80),
    group_by: str = Query(default="month", pattern="^(day|month|year)$"),
):
    """
    How often a specific entity appears per time period.
    GET /api/news/entity-trend?entity=Зеленський&group_by=month
    """
    db = get_db()
    fmt = {"day": "%Y-%m-%d", "month": "%Y-%m", "year": "%Y"}[group_by]
    pipeline = [
        {"$match": {"entities.text": {"$regex": entity, "$options": "i"}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": fmt,
                        "date": {
                            "$cond": {
                                "if": {"$and": [
                                    {"$ne": ["$pub_date", None]},
                                    {"$eq": [{"$type": "$pub_date"}, "date"]},
                                ]},
                                "then": "$pub_date",
                                "else": "$scraped_at",
                            }
                        },
                    }
                },
                "count": {"$sum": 1},
                "avg_sentiment": {"$avg": "$sentiment_score"},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    docs = await db.news.aggregate(pipeline).to_list(length=2000)
    return [
        {
            "date": d["_id"],
            "count": d["count"],
            "avg_sentiment": round(d.get("avg_sentiment") or 0.0, 3),
        }
        for d in docs
        if d["_id"]
    ]


# ---------------------------------------------------------------------------
# Archive scraping endpoints
# ---------------------------------------------------------------------------


@app.post("/api/scrape/archive")
async def start_archive_scrape(
    request: ArchiveScrapeRequest,
    background_tasks: BackgroundTasks,
):
    """
    Start a background archive scrape for a date range.
    Returns immediately with a job_id to track progress.

    POST /api/scrape/archive
    {
      "start_date": "2021-01-01",
      "end_date":   "2026-05-15",
      "max_concurrent": 15,
      "batch_size": 30,
      "batch_delay": 1.0
    }
    """
    if request.end_date < request.start_date:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")

    job_id = str(uuid.uuid4())
    db = get_db()

    background_tasks.add_task(
        run_archive_scrape,
        db=db,
        job_id=job_id,
        start=request.start_date,
        end=request.end_date,
        max_concurrent=request.max_concurrent,
        batch_size=request.batch_size,
        batch_delay=request.batch_delay,
    )

    return {"job_id": job_id, "status": "started"}


@app.get("/api/scrape/archive/{job_id}", response_model=ArchiveJobStatus)
async def get_archive_job(job_id: str):
    """Poll progress of an archive scrape job."""
    db = get_db()
    doc = await db.scrape_jobs.find_one({"job_id": job_id})
    if not doc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    return ArchiveJobStatus(
        job_id=doc["job_id"],
        status=doc.get("status", "unknown"),
        start_date=doc.get("start_date", ""),
        end_date=doc.get("end_date", ""),
        total_days=doc.get("total_days", 0),
        days_done=doc.get("days_done", 0),
        articles_saved=doc.get("articles_saved", 0),
        articles_skipped=doc.get("articles_skipped", 0),
        errors=doc.get("errors", 0),
        progress_pct=doc.get("progress_pct", 0.0),
        started_at=doc.get("started_at"),
        finished_at=doc.get("finished_at"),
    )


@app.get("/api/scrape/jobs")
async def list_scrape_jobs():
    """List all archive scrape jobs, newest first."""
    db = get_db()
    cursor = db.scrape_jobs.find({}).sort("started_at", -1).limit(20)
    docs = await cursor.to_list(length=20)
    return [
        {
            "job_id": d["job_id"],
            "status": d.get("status", "unknown"),
            "start_date": d.get("start_date", ""),
            "end_date": d.get("end_date", ""),
            "total_days": d.get("total_days", 0),
            "days_done": d.get("days_done", 0),
            "articles_saved": d.get("articles_saved", 0),
            "progress_pct": d.get("progress_pct", 0.0),
            "started_at": d.get("started_at"),
            "finished_at": d.get("finished_at"),
        }
        for d in docs
    ]


@app.get("/api/news/trends")
async def keyword_trends(
    keyword: str = Query(min_length=2, max_length=60),
    group_by: str = Query(default="month", pattern="^(day|month|year)$"),
):
    """
    Count articles containing *keyword* (case-insensitive, in title) grouped by date.
    Also returns avg sentiment for those articles.

    GET /api/news/trends?keyword=трамп&group_by=month
    """
    db = get_db()
    fmt = {"day": "%Y-%m-%d", "month": "%Y-%m", "year": "%Y"}[group_by]
    pipeline = [
        {"$match": {"title": {"$regex": keyword, "$options": "i"}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": fmt,
                        "date": {
                            "$cond": {
                                "if": {"$and": [
                                    {"$ne": ["$pub_date", None]},
                                    {"$eq": [{"$type": "$pub_date"}, "date"]},
                                ]},
                                "then": "$pub_date",
                                "else": "$scraped_at",
                            }
                        },
                    }
                },
                "count": {"$sum": 1},
                "avg_sentiment": {"$avg": "$sentiment_score"},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    docs = await db.news.aggregate(pipeline).to_list(length=2000)
    return [
        {
            "date": d["_id"],
            "count": d["count"],
            "avg_sentiment": round(d.get("avg_sentiment") or 0.0, 3),
        }
        for d in docs
        if d["_id"]
    ]


@app.post("/api/news/purge-russian")
async def purge_russian(background_tasks: BackgroundTasks):
    """
    Re-classify every article whose lang is 'unknown', 'ru', or missing,
    using the two-stage detector (heuristic → langdetect).
    Deletes all articles identified as Russian.
    Runs as a background task — returns immediately.
    """
    db = get_db()
    target_filter = {"$or": [
        {"lang": "ru"},
        {"lang": "unknown"},
        {"lang": None},
        {"lang": {"$exists": False}},
    ]}
    total = await db.news.count_documents(target_filter)

    async def _run():
        # Use ONLY the character heuristic for deletion — safe, zero false positives.
        # langdetect is too aggressive on short Ukrainian titles (high false-positive rate).
        # Only delete if title contains Russian-exclusive chars: ы э ъ
        import re
        ru_pattern = re.compile(r"[ыэъ]")
        cursor = db.news.find(target_filter, {"_id": 1, "title": 1})
        async for doc in cursor:
            title = doc.get("title", "")
            if ru_pattern.search(title.lower()):
                await db.news.delete_one({"_id": doc["_id"]})
            else:
                from nlp import detect_language as _detect
                lang = _detect(title)
                await db.news.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"lang": lang}},
                )

    background_tasks.add_task(_run)
    return {"status": "started", "articles_to_check": total}


@app.post("/api/news/reanalyze")
async def reanalyze_news(background_tasks: BackgroundTasks):
    """
    Backfill NLP fields (entities, keywords, sentiment_score) on all existing articles
    that were scraped before spaCy was enabled.
    Runs as a background task — returns immediately with a count estimate.
    """
    db = get_db()
    missing_filter = {"$or": [
        {"entities": {"$exists": False}},
        {"lang": {"$exists": False}},
    ]}
    total = await db.news.count_documents(missing_filter)

    async def _run():
        from nlp import analyze as _analyze
        cursor = db.news.find(missing_filter, {"_id": 1, "title": 1, "description": 1})
        async for doc in cursor:
            nlp_result = _analyze(
                doc.get("title", ""),
                doc.get("description", ""),
            )
            await db.news.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "entities": nlp_result["entities"],
                    "keywords": nlp_result["keywords"],
                    "sentiment_score": nlp_result["sentiment_score"],
                    "lang": nlp_result["lang"],
                }},
            )

    background_tasks.add_task(_run)
    return {"status": "started", "articles_to_process": total}


@app.delete("/api/news")
async def delete_all_news():
    """Delete all news documents from the database."""
    db = get_db()
    result = await db.news.delete_many({})
    return {"deleted": result.deleted_count}
