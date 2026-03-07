"""Coletor de posts do Instagram.

Primário  : Apify actor "apify/instagram-scraper".
Fallback  : RapidAPI Instagram Data API.
"""

from __future__ import annotations

import logging

import requests
from apify_client import ApifyClient

from app.config import settings

logger = logging.getLogger(__name__)

_RAPIDAPI_HOST = "instagram-data1.p.rapidapi.com"
_RAPIDAPI_URL = f"https://{_RAPIDAPI_HOST}/user/feed"


def collect(handle: str) -> list[dict]:
    """Retorna até 10 posts recentes do perfil.

    Args:
        handle: Nome de usuário, com ou sem "@".

    Returns:
        Lista de dicts com keys: title, description, url, published_at, platform.
        Retorna lista vazia em caso de erro.
    """
    result = _collect_via_apify(handle)
    if result:
        return result
    return _collect_via_rapidapi(handle)


# ── Primário: Apify ───────────────────────────────────────────────────────────


def _collect_via_apify(handle: str) -> list[dict]:
    try:
        client = ApifyClient(settings.APIFY_TOKEN)
        run_input = {"usernames": [handle.lstrip("@")], "resultsLimit": 10}
        run = client.actor("apify/instagram-scraper").call(run_input=run_input)

        items: list[dict] = []
        for post in client.dataset(run["defaultDatasetId"]).iterate_items():
            caption = post.get("caption") or ""
            items.append(
                {
                    "title": caption[:100],
                    "description": caption,
                    "url": post.get("url", ""),
                    "published_at": post.get("timestamp", ""),
                    "platform": "instagram",
                }
            )
        return items
    except Exception as e:
        logger.error(f"instagram (apify): {e}")
        return []


# ── Fallback: RapidAPI ────────────────────────────────────────────────────────


def _collect_via_rapidapi(handle: str) -> list[dict]:
    try:
        response = requests.get(
            _RAPIDAPI_URL,
            headers={
                "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
                "X-RapidAPI-Host": _RAPIDAPI_HOST,
            },
            params={"username": handle.lstrip("@")},
            timeout=10,
        )
        response.raise_for_status()

        items: list[dict] = []
        for post in response.json().get("collector", [])[:10]:
            desc = post.get("description") or ""
            items.append(
                {
                    "title": desc[:100],
                    "description": desc,
                    "url": post.get("url", ""),
                    "published_at": str(post.get("taken_at_timestamp", "")),
                    "platform": "instagram",
                }
            )
        return items
    except Exception as e:
        logger.error(f"instagram (rapidapi): {e}")
        return []
