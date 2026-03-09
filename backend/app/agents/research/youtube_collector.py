"""Coletor de vídeos do YouTube via Data API v3."""

from __future__ import annotations

import logging

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import settings

logger = logging.getLogger(__name__)


def collect(channel_id: str) -> list[dict]:
    """Retorna até 10 vídeos recentes do canal.

    Args:
        channel_id: ID do canal no YouTube (ex.: "UCxxxxxx").

    Returns:
        Lista de dicts com keys: title, description, url, published_at, platform.
        Retorna lista vazia em caso de erro.
    """
    try:
        youtube = build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)
        response = (
            youtube.search()
            .list(
                part="snippet",
                channelId=channel_id,
                order="date",
                maxResults=10,
                type="video",
            )
            .execute()
        )

        items: list[dict] = []
        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            video_id = item.get("id", {}).get("videoId", "")
            items.append(
                {
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "published_at": snippet.get("publishedAt", ""),
                    "platform": "youtube",
                }
            )
        return items

    except HttpError as e:
        if e.resp.status == 403:
            logger.warning(f"youtube: quota exceeded ao coletar canal {channel_id!r}")
        else:
            logger.error(f"youtube: {e}")
        return []
    except Exception as e:
        logger.error(f"youtube: {e}")
        return []
