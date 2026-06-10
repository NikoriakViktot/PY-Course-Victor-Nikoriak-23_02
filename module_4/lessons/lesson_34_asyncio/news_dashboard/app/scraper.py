import asyncio
import time
import re
from datetime import datetime, timezone

import aiohttp
from bs4 import BeautifulSoup

from nlp import analyze

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; EduScraper/1.0; +educational)',
    'Accept-Language': 'uk,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml',
}

PAGES = [
    'https://www.rbc.ua/',
    'https://www.rbc.ua/rus/news/',
    'https://www.rbc.ua/rus/economic/',
    'https://www.rbc.ua/rus/politics/',
    'https://www.rbc.ua/rus/society/',
    'https://www.rbc.ua/ukr/news/',
    'https://www.rbc.ua/ukr/economic/',
]


def _parse_page(html: str, base_url: str) -> list[dict]:
    """Parse news items from an HTML page."""
    soup = BeautifulSoup(html, 'lxml')
    items = []

    selectors = [
        ('div', 'newsline__item'),
        ('li', 'newsline__item'),
        ('div', 'news-feed__item'),
        ('div', 'news-item'),
        ('article', 'news-item'),
        ('article', 'article-item'),
    ]

    # rbc.ua actual structure: div.item inside div.newsline
    # Also try div.topstory for featured articles
    containers = []
    for tag, cls in selectors:
        found = soup.find_all(tag, class_=cls)
        if found:
            containers = found
            break

    if not containers:
        # rbc.ua 2024+: div.item inside div.newsline
        containers = soup.find_all('div', class_='item')

    if not containers:
        containers = (
            soup.find_all('article') or
            soup.find_all('div', class_=re.compile(r'news|article'))
        )

    for item in containers:
        link = item.find('a', href=True)
        if not link:
            continue

        raw_text = link.get_text(strip=True)
        # rbc.ua format: "19:45Заголовок новини..." — time prefix
        time_prefix = ''
        if re.match(r'^\d{2}:\d{2}', raw_text):
            time_prefix = raw_text[:5]
            title = raw_text[5:].strip()
        else:
            title = raw_text

        if len(title) < 10:
            continue

        url = link.get('href', '')
        if url and not url.startswith('http'):
            url = 'https://www.rbc.ua' + url

        # Derive category from URL path: /ukr/news/ → news, /rus/economic/ → economic
        url_parts = [p for p in url.replace('https://www.rbc.ua', '').split('/') if p]
        category_map = {
            'news': 'Новини', 'economic': 'Економіка', 'economics': 'Економіка',
            'politics': 'Політика', 'society': 'Суспільство', 'sport': 'Спорт',
            'world': 'Світ', 'technology': 'Технології',
        }
        raw_cat = url_parts[1] if len(url_parts) > 1 else (url_parts[0] if url_parts else '')
        category = category_map.get(raw_cat, raw_cat.capitalize() or 'Загальні')

        # Span inside link may hold time separately
        span_time = item.find('span', class_='time')
        pub_date = None
        if span_time:
            # Time-only string like "19:45" — no full date available from list page
            pass

        description = ''
        nlp_data = analyze(title, description)
        items.append({
            'title': title,
            'url': url,
            'category': category,
            'description': description,
            'pub_date': pub_date,
            'scraped_at': datetime.now(timezone.utc),
            'source': 'rbc.ua',
            **nlp_data,
        })

    return items


async def fetch_one(
    session: aiohttp.ClientSession, url: str, t0: float
) -> dict:
    """Fetch a single URL and return timing info + parsed news."""
    start = time.perf_counter()
    abs_start = start - t0
    error = None
    items = []
    try:
        async with session.get(
            url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)
        ) as resp:
            html = await resp.text()
        items = _parse_page(html, url)
    except Exception as e:
        error = str(e)
    end = time.perf_counter()
    return {
        'url': url,
        'news': items,
        'start': abs_start,
        'end': end - t0,
        'elapsed': end - start,
        'count': len(items),
        'error': error,
    }


async def scrape_all_async(pages: list[str] | None = None) -> dict:
    """Scrape all pages concurrently using asyncio.gather."""
    urls = pages or PAGES
    t0 = time.perf_counter()

    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(fetch_one(session, url, t0)) for url in urls]
        page_results = await asyncio.gather(*tasks, return_exceptions=False)

    total_time = time.perf_counter() - t0

    all_news = []
    seen_urls: set[str] = set()
    for pr in page_results:
        for item in pr['news']:
            if item['url'] not in seen_urls and item['url']:
                seen_urls.add(item['url'])
                all_news.append(item)

    return {
        'page_results': list(page_results),
        'news': all_news,
        'total_time': total_time,
        'pages_count': len(urls),
        'news_count': len(all_news),
    }


async def scrape_sequential(pages: list[str] | None = None) -> dict:
    """Scrape pages one-by-one (sequential) for educational comparison."""
    urls = pages or PAGES
    t0 = time.perf_counter()
    results = []

    async with aiohttp.ClientSession() as session:
        for url in urls:
            r = await fetch_one(session, url, t0)
            results.append(r)

    total_time = time.perf_counter() - t0

    all_news = []
    seen: set[str] = set()
    for pr in results:
        for item in pr['news']:
            if item['url'] not in seen and item['url']:
                seen.add(item['url'])
                all_news.append(item)

    return {
        'page_results': results,
        'news': all_news,
        'total_time': total_time,
        'pages_count': len(urls),
        'news_count': len(all_news),
    }
