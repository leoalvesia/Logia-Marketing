"""Coletor de tweets via Twitter API v2 (tweepy 4.x, leitura com Bearer Token)."""

from __future__ import annotations

import logging

import tweepy

from app.config import settings

logger = logging.getLogger(__name__)


def collect(username: str) -> list[dict]:
    """Retorna até 10 tweets recentes do usuário.

    Args:
        username: Nome de usuário do Twitter, com ou sem "@".

    Returns:
        Lista de dicts com keys: title, description, url, published_at, platform.
        Retorna lista vazia em caso de erro.
    """
    try:
        client = tweepy.Client(bearer_token=settings.TWITTER_BEARER_TOKEN)
        clean_username = username.lstrip("@")

        user_response = client.get_user(username=clean_username)
        if not user_response.data:
            logger.error(f"twitter: usuário não encontrado: {username!r}")
            return []

        user_id = user_response.data.id
        tweets_response = client.get_users_tweets(
            user_id,
            max_results=10,
            tweet_fields=["created_at"],
        )

        if not tweets_response.data:
            return []

        items: list[dict] = []
        for tweet in tweets_response.data:
            published = (
                tweet.created_at.isoformat() if tweet.created_at else ""
            )
            items.append(
                {
                    "title": tweet.text[:100],
                    "description": tweet.text,
                    "url": (
                        f"https://twitter.com/{clean_username}/status/{tweet.id}"
                    ),
                    "published_at": published,
                    "platform": "twitter",
                }
            )
        return items

    except Exception as e:
        logger.error(f"twitter: {e}")
        return []
