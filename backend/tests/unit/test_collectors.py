"""Testes unitários dos coletores de pesquisa (todos os externos mockados)."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from types import ModuleType
from unittest.mock import MagicMock, patch


# ─────────────────────────────────────────────────────────────────────────────
# Helpers para construir mocks de módulos não instalados
# ─────────────────────────────────────────────────────────────────────────────


def _stub_module(name: str) -> ModuleType:
    """Cria e registra um ModuleType vazio em sys.modules."""
    mod = ModuleType(name)
    sys.modules.setdefault(name, mod)
    return sys.modules[name]


# ══════════════════════════════════════════════════════════════════════════════
# YouTube
# ══════════════════════════════════════════════════════════════════════════════


class TestYoutubeCollector:
    """Testes para youtube_collector.collect()."""

    def _make_search_item(
        self, video_id: str, title: str, description: str, published_at: str
    ) -> dict:
        return {
            "id": {"videoId": video_id},
            "snippet": {
                "title": title,
                "description": description,
                "publishedAt": published_at,
            },
        }

    def test_returns_list_of_dicts(self):
        fake_item = self._make_search_item(
            "abc123", "Título do vídeo", "Descrição", "2026-01-01T00:00:00Z"
        )
        fake_response = {"items": [fake_item]}

        mock_search = MagicMock()
        mock_search.return_value.list.return_value.execute.return_value = fake_response
        mock_youtube = MagicMock()
        mock_youtube.search = mock_search

        with patch(
            "app.agents.research.youtube_collector.build",
            return_value=mock_youtube,
        ):
            from app.agents.research import youtube_collector

            result = youtube_collector.collect("UCfake")

        assert isinstance(result, list)
        assert len(result) == 1
        item = result[0]
        assert item["title"] == "Título do vídeo"
        assert item["url"] == "https://www.youtube.com/watch?v=abc123"
        assert item["platform"] == "youtube"
        assert item["published_at"] == "2026-01-01T00:00:00Z"

    def test_returns_multiple_items(self):
        items = [
            self._make_search_item(f"vid{i}", f"Título {i}", "Desc", "2026-01-01T00:00:00Z")
            for i in range(5)
        ]
        fake_response = {"items": items}

        mock_search = MagicMock()
        mock_search.return_value.list.return_value.execute.return_value = fake_response
        mock_youtube = MagicMock()
        mock_youtube.search = mock_search

        with patch(
            "app.agents.research.youtube_collector.build",
            return_value=mock_youtube,
        ):
            from app.agents.research import youtube_collector

            result = youtube_collector.collect("UCfake")

        assert len(result) == 5
        assert all(r["platform"] == "youtube" for r in result)

    def test_quota_exceeded_returns_empty(self):
        from googleapiclient.errors import HttpError

        fake_resp = MagicMock()
        fake_resp.status = 403
        http_error = HttpError(resp=fake_resp, content=b"quotaExceeded")

        mock_search = MagicMock()
        mock_search.return_value.list.return_value.execute.side_effect = http_error
        mock_youtube = MagicMock()
        mock_youtube.search = mock_search

        with patch(
            "app.agents.research.youtube_collector.build",
            return_value=mock_youtube,
        ):
            from app.agents.research import youtube_collector

            result = youtube_collector.collect("UCfake")

        assert result == []

    def test_other_http_error_returns_empty(self):
        from googleapiclient.errors import HttpError

        fake_resp = MagicMock()
        fake_resp.status = 500
        http_error = HttpError(resp=fake_resp, content=b"internalError")

        mock_search = MagicMock()
        mock_search.return_value.list.return_value.execute.side_effect = http_error
        mock_youtube = MagicMock()
        mock_youtube.search = mock_search

        with patch(
            "app.agents.research.youtube_collector.build",
            return_value=mock_youtube,
        ):
            from app.agents.research import youtube_collector

            result = youtube_collector.collect("UCfake")

        assert result == []

    def test_generic_exception_returns_empty(self):
        with patch(
            "app.agents.research.youtube_collector.build",
            side_effect=RuntimeError("network error"),
        ):
            from app.agents.research import youtube_collector

            result = youtube_collector.collect("UCfake")

        assert result == []

    def test_empty_response_returns_empty_list(self):
        mock_search = MagicMock()
        mock_search.return_value.list.return_value.execute.return_value = {"items": []}
        mock_youtube = MagicMock()
        mock_youtube.search = mock_search

        with patch(
            "app.agents.research.youtube_collector.build",
            return_value=mock_youtube,
        ):
            from app.agents.research import youtube_collector

            result = youtube_collector.collect("UCfake")

        assert result == []


# ══════════════════════════════════════════════════════════════════════════════
# Instagram
# ══════════════════════════════════════════════════════════════════════════════


def _make_apify_instagram_post(n: int = 0) -> dict:
    return {
        "caption": f"Post {n} de teste #marketing",
        "url": f"https://www.instagram.com/p/post{n}/",
        "timestamp": "2026-01-01T00:00:00Z",
    }


class TestInstagramCollector:
    """Testes para instagram_collector.collect()."""

    # ── Primário: Apify ───────────────────────────────────────────────────────

    def _make_apify_mock(self, posts: list[dict]) -> MagicMock:
        mock_dataset = MagicMock()
        mock_dataset.iterate_items.return_value = iter(posts)

        mock_run_result = {"defaultDatasetId": "ds-123"}
        mock_actor = MagicMock()
        mock_actor.call.return_value = mock_run_result

        mock_client = MagicMock()
        mock_client.actor.return_value = mock_actor
        mock_client.dataset.return_value = mock_dataset
        return mock_client

    def test_apify_primary_returns_posts(self):
        posts = [_make_apify_instagram_post(i) for i in range(3)]
        mock_client = self._make_apify_mock(posts)

        with patch(
            "app.agents.research.instagram_collector.ApifyClient",
            return_value=mock_client,
        ):
            from app.agents.research import instagram_collector

            result = instagram_collector.collect("@testhandle")

        assert len(result) == 3
        assert result[0]["platform"] == "instagram"
        assert result[0]["description"] == "Post 0 de teste #marketing"
        assert result[0]["url"] == "https://www.instagram.com/p/post0/"

    def test_handle_without_at_sign(self):
        posts = [_make_apify_instagram_post()]
        mock_client = self._make_apify_mock(posts)

        with patch(
            "app.agents.research.instagram_collector.ApifyClient",
            return_value=mock_client,
        ):
            from app.agents.research import instagram_collector

            instagram_collector.collect("testhandle")  # sem @

        mock_client.actor.assert_called_once_with("apify/instagram-scraper")
        call_kwargs = mock_client.actor.return_value.call.call_args[1]["run_input"]
        assert "testhandle" in call_kwargs["usernames"]

    def test_apify_failure_falls_back_to_rapidapi(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "collector": [
                {
                    "description": "Post via RapidAPI",
                    "url": "https://www.instagram.com/p/rapid/",
                    "taken_at_timestamp": 1234567890,
                }
            ]
        }
        mock_resp.raise_for_status = MagicMock()

        with (
            patch(
                "app.agents.research.instagram_collector.ApifyClient",
                side_effect=Exception("apify offline"),
            ),
            patch(
                "app.agents.research.instagram_collector.requests.get",
                return_value=mock_resp,
            ),
        ):
            from app.agents.research import instagram_collector

            result = instagram_collector.collect("@testhandle")

        assert len(result) == 1
        assert result[0]["platform"] == "instagram"
        assert result[0]["description"] == "Post via RapidAPI"

    def test_both_sources_fail_returns_empty(self):
        with (
            patch(
                "app.agents.research.instagram_collector.ApifyClient",
                side_effect=Exception("apify offline"),
            ),
            patch(
                "app.agents.research.instagram_collector.requests.get",
                side_effect=Exception("rapidapi offline"),
            ),
        ):
            from app.agents.research import instagram_collector

            result = instagram_collector.collect("@testhandle")

        assert result == []

    def test_title_truncated_to_100_chars(self):
        long_caption = "A" * 200
        posts = [{"caption": long_caption, "url": "https://x.com/p/1", "timestamp": "2026-01-01"}]
        mock_client = self._make_apify_mock(posts)

        with patch(
            "app.agents.research.instagram_collector.ApifyClient",
            return_value=mock_client,
        ):
            from app.agents.research import instagram_collector

            result = instagram_collector.collect("@h")

        assert len(result[0]["title"]) <= 100
        assert result[0]["description"] == long_caption  # description preservada

    def test_apify_empty_result_falls_back_to_rapidapi(self):
        """Quando Apify retorna lista vazia, coletor deve tentar RapidAPI."""
        mock_client = self._make_apify_mock([])  # Apify retorna vazio

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "collector": [{"description": "Rapid post", "url": "https://x.com", "taken_at_timestamp": 0}]
        }
        mock_resp.raise_for_status = MagicMock()

        with (
            patch(
                "app.agents.research.instagram_collector.ApifyClient",
                return_value=mock_client,
            ),
            patch(
                "app.agents.research.instagram_collector.requests.get",
                return_value=mock_resp,
            ),
        ):
            from app.agents.research import instagram_collector

            result = instagram_collector.collect("@h")

        assert len(result) == 1
        assert result[0]["description"] == "Rapid post"


# ══════════════════════════════════════════════════════════════════════════════
# Twitter
# ══════════════════════════════════════════════════════════════════════════════


def _make_tweet(tweet_id: int, text: str) -> MagicMock:
    tweet = MagicMock()
    tweet.id = tweet_id
    tweet.text = text
    tweet.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return tweet


def _make_user(user_id: int = 42) -> MagicMock:
    user_data = MagicMock()
    user_data.id = user_id
    user_resp = MagicMock()
    user_resp.data = user_data
    return user_resp


class TestTwitterCollector:
    """Testes para twitter_collector.collect()."""

    def _make_client_mock(
        self,
        user_resp: MagicMock,
        tweets: list[MagicMock] | None,
    ) -> MagicMock:
        tweets_resp = MagicMock()
        tweets_resp.data = tweets

        mock_client = MagicMock()
        mock_client.get_user.return_value = user_resp
        mock_client.get_users_tweets.return_value = tweets_resp
        return mock_client

    def test_returns_tweets(self):
        tweets = [_make_tweet(1, "Olá mundo!"), _make_tweet(2, "Segundo tweet")]
        mock_client = self._make_client_mock(_make_user(), tweets)

        with patch(
            "app.agents.research.twitter_collector.tweepy.Client",
            return_value=mock_client,
        ):
            from app.agents.research import twitter_collector

            result = twitter_collector.collect("@usuario")

        assert len(result) == 2
        assert result[0]["platform"] == "twitter"
        assert result[0]["description"] == "Olá mundo!"
        assert "twitter.com/usuario/status/1" in result[0]["url"]

    def test_handle_without_at(self):
        tweets = [_make_tweet(1, "tweet")]
        mock_client = self._make_client_mock(_make_user(), tweets)

        with patch(
            "app.agents.research.twitter_collector.tweepy.Client",
            return_value=mock_client,
        ):
            from app.agents.research import twitter_collector

            twitter_collector.collect("usuario")

        mock_client.get_user.assert_called_once_with(username="usuario")

    def test_user_not_found_returns_empty(self):
        user_resp = MagicMock()
        user_resp.data = None
        mock_client = self._make_client_mock(user_resp, None)

        with patch(
            "app.agents.research.twitter_collector.tweepy.Client",
            return_value=mock_client,
        ):
            from app.agents.research import twitter_collector

            result = twitter_collector.collect("@fantasma")

        assert result == []

    def test_no_tweets_returns_empty(self):
        mock_client = self._make_client_mock(_make_user(), None)

        with patch(
            "app.agents.research.twitter_collector.tweepy.Client",
            return_value=mock_client,
        ):
            from app.agents.research import twitter_collector

            result = twitter_collector.collect("@usuario")

        assert result == []

    def test_api_exception_returns_empty(self):
        with patch(
            "app.agents.research.twitter_collector.tweepy.Client",
            side_effect=Exception("API offline"),
        ):
            from app.agents.research import twitter_collector

            result = twitter_collector.collect("@usuario")

        assert result == []

    def test_published_at_is_iso_string(self):
        tweets = [_make_tweet(99, "Teste de data")]
        mock_client = self._make_client_mock(_make_user(), tweets)

        with patch(
            "app.agents.research.twitter_collector.tweepy.Client",
            return_value=mock_client,
        ):
            from app.agents.research import twitter_collector

            result = twitter_collector.collect("@u")

        assert "2026-01-01" in result[0]["published_at"]

    def test_title_truncated_to_100_chars(self):
        long_text = "X" * 300
        tweets = [_make_tweet(1, long_text)]
        mock_client = self._make_client_mock(_make_user(), tweets)

        with patch(
            "app.agents.research.twitter_collector.tweepy.Client",
            return_value=mock_client,
        ):
            from app.agents.research import twitter_collector

            result = twitter_collector.collect("@u")

        assert len(result[0]["title"]) <= 100
        assert result[0]["description"] == long_text


# ══════════════════════════════════════════════════════════════════════════════
# LinkedIn
# ══════════════════════════════════════════════════════════════════════════════


def _make_linkedin_post(n: int = 0) -> dict:
    return {
        "title": f"Post LinkedIn {n}",
        "text": f"Conteúdo completo do post {n}",
        "url": f"https://www.linkedin.com/posts/post{n}",
        "publishedAt": "2026-01-01T00:00:00Z",
    }


class TestLinkedinCollector:
    """Testes para linkedin_collector.collect()."""

    def _make_apify_mock(self, posts: list[dict]) -> MagicMock:
        mock_dataset = MagicMock()
        mock_dataset.iterate_items.return_value = iter(posts)

        mock_run_result = {"defaultDatasetId": "ds-456"}
        mock_actor = MagicMock()
        mock_actor.call.return_value = mock_run_result

        mock_client = MagicMock()
        mock_client.actor.return_value = mock_actor
        mock_client.dataset.return_value = mock_dataset
        return mock_client

    def test_returns_posts(self):
        posts = [_make_linkedin_post(i) for i in range(4)]
        mock_client = self._make_apify_mock(posts)

        with patch(
            "app.agents.research.linkedin_collector.ApifyClient",
            return_value=mock_client,
        ):
            from app.agents.research import linkedin_collector

            result = linkedin_collector.collect("https://www.linkedin.com/in/usuario")

        assert len(result) == 4
        assert result[0]["platform"] == "linkedin"
        assert result[0]["title"] == "Post LinkedIn 0"
        assert result[0]["description"] == "Conteúdo completo do post 0"

    def test_uses_correct_actor(self):
        mock_client = self._make_apify_mock([])

        with patch(
            "app.agents.research.linkedin_collector.ApifyClient",
            return_value=mock_client,
        ):
            from app.agents.research import linkedin_collector

            linkedin_collector.collect("https://www.linkedin.com/in/usuario")

        mock_client.actor.assert_called_once_with("apify/linkedin-scraper")

    def test_passes_profile_url_to_actor(self):
        profile_url = "https://www.linkedin.com/in/meu-perfil"
        mock_client = self._make_apify_mock([])

        with patch(
            "app.agents.research.linkedin_collector.ApifyClient",
            return_value=mock_client,
        ):
            from app.agents.research import linkedin_collector

            linkedin_collector.collect(profile_url)

        call_kwargs = mock_client.actor.return_value.call.call_args[1]["run_input"]
        assert call_kwargs["startUrls"][0]["url"] == profile_url

    def test_exception_returns_empty(self):
        with patch(
            "app.agents.research.linkedin_collector.ApifyClient",
            side_effect=Exception("apify offline"),
        ):
            from app.agents.research import linkedin_collector

            result = linkedin_collector.collect("https://www.linkedin.com/in/usuario")

        assert result == []

    def test_empty_result_returns_empty_list(self):
        mock_client = self._make_apify_mock([])

        with patch(
            "app.agents.research.linkedin_collector.ApifyClient",
            return_value=mock_client,
        ):
            from app.agents.research import linkedin_collector

            result = linkedin_collector.collect("https://www.linkedin.com/in/usuario")

        assert result == []

    def test_fallback_fields_when_title_absent(self):
        """Quando 'title' ausente, usa 'text' como título."""
        posts = [{"text": "Conteúdo sem título", "url": "https://x.com", "publishedAt": "2026"}]
        mock_client = self._make_apify_mock(posts)

        with patch(
            "app.agents.research.linkedin_collector.ApifyClient",
            return_value=mock_client,
        ):
            from app.agents.research import linkedin_collector

            result = linkedin_collector.collect("https://www.linkedin.com/in/u")

        assert result[0]["title"] == "Conteúdo sem título"

    def test_url_falls_back_to_profile_url(self):
        """Quando post não tem 'url', usa profile_url como fallback."""
        profile_url = "https://www.linkedin.com/in/u"
        posts = [{"text": "Post sem URL", "publishedAt": "2026"}]
        mock_client = self._make_apify_mock(posts)

        with patch(
            "app.agents.research.linkedin_collector.ApifyClient",
            return_value=mock_client,
        ):
            from app.agents.research import linkedin_collector

            result = linkedin_collector.collect(profile_url)

        assert result[0]["url"] == profile_url
