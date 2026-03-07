"""Coletor de posts do LinkedIn via Apify actor "apify/linkedin-scraper"."""

from __future__ import annotations

import logging

from apify_client import ApifyClient

from app.config import settings

logger = logging.getLogger(__name__)


def collect(profile_url: str) -> list[dict]:
    """Retorna até 10 posts recentes do perfil LinkedIn.

    Args:
        profile_url: URL completa do perfil (ex.: "https://www.linkedin.com/in/handle").

    Returns:
        Lista de dicts com keys: title, description, url, published_at, platform.
        Retorna lista vazia em caso de erro.
    """
    try:
        client = ApifyClient(settings.APIFY_TOKEN)
        run_input = {"startUrls": [{"url": profile_url}], "count": 10}
        run = client.actor("apify/linkedin-scraper").call(run_input=run_input)

        items: list[dict] = []
        for post in client.dataset(run["defaultDatasetId"]).iterate_items():
            title = post.get("title") or post.get("text") or ""
            description = post.get("text") or post.get("description") or ""
            items.append(
                {
                    "title": title[:100],
                    "description": description,
                    "url": post.get("url", profile_url),
                    "published_at": post.get("publishedAt") or post.get("date", ""),
                    "platform": "linkedin",
                }
            )
        return items

    except Exception as e:
        logger.error(f"linkedin: {e}")
        return []
