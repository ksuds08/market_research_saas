"""
agent.py
Core market‑research logic (search, scrape, summarize, compile report).
"""
import asyncio
import datetime as dt
import os
import re
from typing import List, Dict

import aiohttp
import bs4
import openai
import requests

from .settings import get_settings

settings = get_settings()
openai.api_key = settings.openai_key
SERP_ENDPOINT = "https://serpapi.com/search.json"


def _clean_text(html: str) -> str:
    soup = bs4.BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ")
    return re.sub(r"\s+", " ", text).strip()


def _serp_search(query: str, num_results: int = 10) -> List[str]:
    params = {
        "q": query,
        "api_key": settings.serpapi_key,
        "engine": "google",
        "num": num_results,
    }
    res = requests.get(SERP_ENDPOINT, params=params, timeout=30)
    res.raise_for_status()
    return [r["link"] for r in res.json().get("organic_results", [])]


async def _fetch(session: aiohttp.ClientSession, url: str) -> str:
    try:
        async with session.get(url, timeout=15) as resp:
            return await resp.text() if resp.status == 200 else ""
    except Exception:
        return ""


async def _summarize(text: str) -> str:
    response = await openai.ChatCompletion.acreate(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior market‑research analyst. Provide a concise "
                    "summary with key insights, competitor mentions, and trends."
                ),
            },
            {"role": "user", "content": text[:20000]},  # safety cut
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


async def _analyze_urls(urls: List[str]) -> List[Dict]:
    results = []
    async with aiohttp.ClientSession() as session:
        for url in urls:
            html = await _fetch(session, url)
            if not html:
                continue
            summary = await _summarize(_clean_text(html))
            results.append({"url": url, "summary": summary})
    return results


async def generate_report(topic: str, extra_keywords: List[str] = None, n: int = 10):
    """
    High‑level helper: search → scrape → summarize → return Markdown report.
    """
    extra_keywords = extra_keywords or []
    queries = [topic] + [f"{topic} {k}" for k in extra_keywords]
    urls = []
    for q in queries:
        urls.extend(_serp_search(q, n))

    analyses = await _analyze_urls(urls)

    ts = dt.datetime.utcnow().strftime("%Y‑%m‑%d %H:%M UTC")
    md = [f"# Market Research Report\n**Topic:** {topic}\n**Generated:** {ts}\n"]
    for item in analyses:
        md.append(f"## {item['url']}\n{item['summary']}\n")
    return "\n---\n".join(md)
