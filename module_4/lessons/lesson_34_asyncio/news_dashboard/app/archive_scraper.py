"""
RBC.UA Archive Scraper
======================
Scrapes daily archive pages:  rbc.ua/rus/archive/YYYY/MM/DD
Each page lists all articles published that day (~40-160 per day).

Designed for multi-year collection with:
  - asyncio.Semaphore  — max N concurrent requests (polite crawling)
  - asyncio.sleep delay — pause between batches
  - MongoDB upsert      — safe to re-run (idempotent)
  - Progress callback   — tracked in DB scrape_jobs collection
"""
from __future__ import annotations

import asyncio
import re
import uuid
from datetime import date, timedelta
from datetime import datetime, timezone

import aiohttp
from bs4 import BeautifulSoup

from nlp import analyze

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EduScraper/1.0; +educational)",
    "Accept-Language": "uk,en;q=0.9",
}

ARCHIVE_URL = "https://www.rbc.ua/rus/archive/{year}/{month:02d}/{day:02d}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def date_range(start: date, end: date) -> list[date]:
    """Return list of dates from start to end inclusive."""
    days = (end - start).days + 1
    return [start + timedelta(days=i) for i in range(days)]


def _parse_archive_page(html: str, page_date: date) -> list[dict]:
    """Extract article stubs from one archive page."""
    soup = BeautifulSoup(html, "lxml")
    items: list[dict] = []
    seen: set[str] = set()

    for link in soup.find_all("a", href=re.compile(r"rbc\.ua.*/news/.*\d{10,}")):
        href = link.get("href", "")
        if not href.startswith("http"):
            href = "https://www.rbc.ua" + href
        if href in seen:
            continue
        seen.add(href)

        raw = link.get_text(strip=True)
        # Strip leading time prefix like "00:12"
        if re.match(r"^\d{2}:\d{2}", raw):
            time_str = raw[:5]
            title = raw[5:].strip()
            # Build pub_date from archive date + time
            try:
                h, m = int(time_str[:2]), int(time_str[3:])
                pub_date = datetime(
                    page_date.year, page_date.month, page_date.day, h, m,
                    tzinfo=timezone.utc
                )
            except Exception:
                pub_date = datetime(
                    page_date.year, page_date.month, page_date.day,
                    tzinfo=timezone.utc
                )
        else:
            title = raw
            pub_date = datetime(
                page_date.year, page_date.month, page_date.day,
                tzinfo=timezone.utc
            )

        if len(title) < 10:
            continue

        nlp = analyze(title, "")
        items.append({
            "title": title,
            "url": href,
            "category": "Архів",
            "description": "",
            "pub_date": pub_date,
            "scraped_at": datetime.now(timezone.utc),
            "source": "rbc.ua/archive",
            **nlp,
        })
    return items


async def _fetch_archive_day(
    session: aiohttp.ClientSession,
    d: date,
    semaphore: asyncio.Semaphore,
) -> dict:
    url = ARCHIVE_URL.format(year=d.year, month=d.month, day=d.day)
    async with semaphore:
        try:
            async with session.get(
                url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=20)
            ) as resp:
                html = await resp.text()
            items = _parse_archive_page(html, d)
            return {"date": d.isoformat(), "url": url, "count": len(items), "items": items, "error": None}
        except Exception as e:
            return {"date": d.isoformat(), "url": url, "count": 0, "items": [], "error": str(e)[:120]}


# ---------------------------------------------------------------------------
# Main entry point  (called from FastAPI background task)
# ---------------------------------------------------------------------------

async def run_archive_scrape(
    db,
    job_id: str,
    start: date,
    end: date,
    max_concurrent: int = 15,
    batch_size: int = 30,
    batch_delay: float = 1.0,
) -> None:
    """
    Scrape all daily archive pages between start and end (inclusive).
    Saves articles to db.news (upsert on url).
    Tracks progress in db.scrape_jobs.
    """
    all_dates = date_range(start, end)
    total_days = len(all_dates)

    # Initialise job record
    await db.scrape_jobs.update_one(
        {"job_id": job_id},
        {"$set": {
            "job_id": job_id,
            "status": "running",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "total_days": total_days,
            "days_done": 0,
            "articles_saved": 0,
            "articles_skipped": 0,
            "errors": 0,
            "started_at": datetime.now(timezone.utc),
            "finished_at": None,
        }},
        upsert=True,
    )

    semaphore = asyncio.Semaphore(max_concurrent)
    days_done = 0
    articles_saved = 0
    articles_skipped = 0
    errors = 0

    async with aiohttp.ClientSession() as session:
        # Process in batches to add polite delay between bursts
        for batch_start in range(0, total_days, batch_size):
            batch = all_dates[batch_start: batch_start + batch_size]

            tasks = [
                asyncio.create_task(_fetch_archive_day(session, d, semaphore))
                for d in batch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=False)

            # Upsert articles into MongoDB
            for day_result in results:
                days_done += 1
                if day_result["error"]:
                    errors += 1
                    continue
                for item in day_result["items"]:
                    url = item.get("url", "")
                    if not url:
                        continue
                    res = await db.news.update_one(
                        {"url": url},
                        {"$setOnInsert": item},
                        upsert=True,
                    )
                    if res.upserted_id:
                        articles_saved += 1
                    else:
                        articles_skipped += 1

            # Update progress
            await db.scrape_jobs.update_one(
                {"job_id": job_id},
                {"$set": {
                    "days_done": days_done,
                    "articles_saved": articles_saved,
                    "articles_skipped": articles_skipped,
                    "errors": errors,
                    "progress_pct": round(days_done / total_days * 100, 1),
                }},
            )

            # Polite delay between batches
            if batch_start + batch_size < total_days:
                await asyncio.sleep(batch_delay)

    # Mark job done
    await db.scrape_jobs.update_one(
        {"job_id": job_id},
        {"$set": {
            "status": "done",
            "finished_at": datetime.now(timezone.utc),
            "days_done": days_done,
            "articles_saved": articles_saved,
            "articles_skipped": articles_skipped,
            "errors": errors,
            "progress_pct": 100.0,
        }},
    )
