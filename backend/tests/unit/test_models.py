"""Testes unitários dos models SQLAlchemy (sem banco real)."""

import json
from datetime import datetime, timezone

from app.models.user import User
from app.models.pipeline import Pipeline, PipelineState
from app.models.topic import Topic
from app.models.copy import Copy, CopyChannel, CopyStatus
from app.models.art import Art, ArtType
from app.models.monitored_profiles import MonitoredProfile
from app.models.scheduled_post import ScheduledPost, ScheduledPostStatus
from app.models.social_tokens import SocialToken

# ── User ──────────────────────────────────────────────────────────────────────


class TestUserModel:
    def test_user_instantiation(self):
        """
        Em SQLAlchemy 2.0, column defaults (default=) são aplicados no INSERT,
        não na construção do objeto. Verificamos estrutura e campos opcionais aqui;
        os valores padrão de colunas são verificados nos testes de integração.
        """
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            name="Teste",
        )
        assert user.email == "test@example.com"
        assert user.name == "Teste"
        assert user.nicho is None
        assert user.persona is None
        assert user.brand_identity is None

    def test_user_repr(self):
        user = User(id="abc-123", email="test@example.com", hashed_password="x", name="T")
        assert "abc-123" in repr(user)
        assert "test@example.com" in repr(user)


# ── Pipeline ──────────────────────────────────────────────────────────────────


class TestPipelineModel:
    def test_pipeline_state_enum_values(self):
        states = [s.value for s in PipelineState]
        assert "RESEARCHING" in states
        assert "AWAITING_SELECTION" in states
        assert "PUBLISHED" in states
        assert "FAILED" in states
        assert len(states) == 11

    def test_pipeline_nullable_fields(self):
        """Campos opcionais devem ser None antes do INSERT."""
        p = Pipeline(user_id="user-1")
        assert p.topic_selected is None
        assert p.error_detail is None

    def test_pipeline_repr(self):
        p = Pipeline(id="pip-1", user_id="u-1")
        assert "pip-1" in repr(p)


# ── Topic ─────────────────────────────────────────────────────────────────────


class TestTopicModel:
    def test_topic_requires_source_url(self):
        """source_url nunca pode ser vazio — regra crítica do sistema."""
        t = Topic(
            pipeline_id="pip-1",
            user_id="user-1",
            title="Tema Teste",
            summary="Resumo do tema",
            source_url="https://example.com/artigo",
            rank=1,
        )
        assert t.source_url == "https://example.com/artigo"
        assert t.source_url != ""

    def test_topic_score_accepted(self):
        t = Topic(
            pipeline_id="p",
            user_id="u",
            title="T",
            summary="S",
            source_url="https://x.com",
            rank=1,
            score=0.92,
        )
        assert t.score == 0.92

    def test_topic_channels_found_json(self):
        raw = json.dumps(["instagram", "youtube"])
        t = Topic(
            pipeline_id="p",
            user_id="u",
            title="T",
            summary="S",
            source_url="https://x.com",
            rank=1,
            channels_found=raw,
        )
        assert json.loads(t.channels_found) == ["instagram", "youtube"]

    def test_topic_rank_range(self):
        """Orquestrador gera até 10 temas (rank 1–10)."""
        for rank in range(1, 11):
            t = Topic(
                pipeline_id="p",
                user_id="u",
                title="T",
                summary="S",
                source_url="https://x.com",
                rank=rank,
            )
            assert 1 <= t.rank <= 10


# ── Copy ──────────────────────────────────────────────────────────────────────


class TestCopyModel:
    def test_copy_channels(self):
        channels = [c.value for c in CopyChannel]
        assert set(channels) == {"instagram", "linkedin", "twitter", "youtube", "email"}

    def test_copy_explicit_status(self):
        c = Copy(
            pipeline_id="p",
            channel=CopyChannel.INSTAGRAM,
            content='{"caption": "test"}',
            source_url="https://example.com",
            status=CopyStatus.APPROVED,
        )
        assert c.status == CopyStatus.APPROVED

    def test_copy_source_url_not_empty(self):
        c = Copy(
            pipeline_id="p",
            channel=CopyChannel.LINKEDIN,
            content="{}",
            source_url="https://real-source.com/artigo",
        )
        assert c.source_url
        assert c.source_url.startswith("https://")


# ── Art ───────────────────────────────────────────────────────────────────────


class TestArtModel:
    def test_art_types(self):
        assert ArtType.STATIC.value == "static"
        assert ArtType.CAROUSEL.value == "carousel"
        assert ArtType.THUMBNAIL.value == "thumbnail"

    def test_art_explicit_type(self):
        a = Art(pipeline_id="p", copy_id="c", art_type=ArtType.STATIC)
        assert a.art_type == ArtType.STATIC

    def test_art_image_urls_explicit(self):
        urls = json.dumps(["https://drive.google.com/uc?id=abc"])
        a = Art(pipeline_id="p", copy_id="c", art_type=ArtType.CAROUSEL, image_urls=urls)
        assert json.loads(a.image_urls)[0].startswith("https://")


# ── MonitoredProfile ──────────────────────────────────────────────────────────


class TestMonitoredProfileModel:
    def test_explicit_inactive(self):
        p = MonitoredProfile(user_id="u", platform="instagram", handle="@logia", active=False)
        assert p.active is False

    def test_url_nullable(self):
        p = MonitoredProfile(user_id="u", platform="youtube", handle="UCxxx")
        assert p.url is None

    def test_platform_as_string(self):
        p = MonitoredProfile(user_id="u", platform="linkedin", handle="profile")
        assert p.platform == "linkedin"


# ── ScheduledPost ─────────────────────────────────────────────────────────────


class TestScheduledPostModel:
    def test_explicit_status(self):
        sp = ScheduledPost(
            pipeline_id="p",
            copy_id="c",
            user_id="u",
            channel="instagram",
            scheduled_for=datetime.now(timezone.utc),
            status=ScheduledPostStatus.PENDING,
        )
        assert sp.status == ScheduledPostStatus.PENDING

    def test_art_id_nullable(self):
        sp = ScheduledPost(
            pipeline_id="p",
            copy_id="c",
            user_id="u",
            channel="linkedin",
            scheduled_for=datetime.now(timezone.utc),
        )
        assert sp.art_id is None

    def test_status_enum_values(self):
        values = {s.value for s in ScheduledPostStatus}
        assert values == {"pending", "publishing", "published", "failed"}


# ── SocialToken ───────────────────────────────────────────────────────────────


class TestSocialTokenModel:
    def test_platform_as_string(self):
        t = SocialToken(user_id="u", platform="instagram", access_token="tok")
        assert t.platform == "instagram"

    def test_optional_fields_none(self):
        t = SocialToken(user_id="u", platform="twitter", access_token="tok")
        assert t.refresh_token is None
        assert t.expires_at is None
