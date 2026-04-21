"""
Модуль 1: Сбор данных
Источники: NewsAPI, GNews API, RSS-ленты
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
import feedparser
import httpx
from pydantic import BaseModel
from config import NEWSAPI_KEY, GNEWS_KEY, RSS_FEEDS


class Article(BaseModel):
    title: str
    text: str
    source: str
    url: str
    published: Optional[str] = None


async def _fetch_newsapi(query: str, lang: str = "ru") -> list[Article]:
    if not NEWSAPI_KEY:
        return []
    from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    params = {
        "q": query,
        "language": lang,
        "from": from_date,
        "sortBy": "relevancy",
        "pageSize": 20,
        "apiKey": NEWSAPI_KEY,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get("https://newsapi.org/v2/everything", params=params)
            r.raise_for_status()
            articles = []
            for item in r.json().get("articles", []):
                articles.append(Article(
                    title=item.get("title", ""),
                    text=(item.get("description") or item.get("content") or ""),
                    source=item.get("source", {}).get("name", "NewsAPI"),
                    url=item.get("url", ""),
                    published=item.get("publishedAt", ""),
                ))
            return articles
    except Exception as e:
        print(f"[NewsAPI] Ошибка: {e}")
        return []


async def _fetch_gnews(query: str, lang: str = "ru") -> list[Article]:
    if not GNEWS_KEY:
        return []
    params = {
        "q": query,
        "lang": lang,
        "max": 20,
        "apikey": GNEWS_KEY,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get("https://gnews.io/api/v4/search", params=params)
            r.raise_for_status()
            articles = []
            for item in r.json().get("articles", []):
                articles.append(Article(
                    title=item.get("title", ""),
                    text=item.get("description", ""),
                    source=item.get("source", {}).get("name", "GNews"),
                    url=item.get("url", ""),
                    published=item.get("publishedAt", ""),
                ))
            return articles
    except Exception as e:
        print(f"[GNews] Ошибка: {e}")
        return []


async def _fetch_rss(query: str, source_name: str, url: str) -> list[Article]:
    try:
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, url)
        query_words = query.lower().split()
        articles = []
        for entry in feed.entries[:50]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            combined = (title + " " + summary).lower()
            if any(word in combined for word in query_words):
                articles.append(Article(
                    title=title,
                    text=summary,
                    source=source_name,
                    url=entry.get("link", ""),
                    published=entry.get("published", ""),
                ))
        return articles
    except Exception as e:
        print(f"[RSS:{source_name}] Ошибка: {e}")
        return []


async def collect(query: str, lang: str = "ru") -> list[Article]:
    """Собирает статьи из всех доступных источников параллельно."""
    tasks = [
        _fetch_newsapi(query, lang),
        _fetch_gnews(query, lang),
        *[_fetch_rss(query, name, url) for name, url in RSS_FEEDS.items()],
    ]
    results = await asyncio.gather(*tasks)
    articles = [a for batch in results for a in batch]

    # Дедупликация по URL
    seen_urls = set()
    unique = []
    for a in articles:
        if a.url and a.url not in seen_urls:
            seen_urls.add(a.url)
            unique.append(a)

    return unique
