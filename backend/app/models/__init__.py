# Importar todos os models garante que o metadata do Base fica completo
# antes de qualquer create_all ou migração Alembic.
from app.models.user import User
from app.models.pipeline import Pipeline, PipelineState
from app.models.topic import Topic
from app.models.copy import Copy, CopyChannel, CopyStatus
from app.models.art import Art, ArtType
from app.models.monitored_profiles import MonitoredProfile
from app.models.scheduled_post import ScheduledPost, ScheduledPostStatus
from app.models.social_tokens import SocialToken
from app.models.request_log import RequestLog
from app.models.invite import Invite
from app.models.feedback import NpsFeedback, PostFeedback, BugReport
from app.models.ai_usage import AiUsageLog

__all__ = [
    "User",
    "Pipeline",
    "PipelineState",
    "Topic",
    "Copy",
    "CopyChannel",
    "CopyStatus",
    "Art",
    "ArtType",
    "MonitoredProfile",
    "ScheduledPost",
    "ScheduledPostStatus",
    "SocialToken",
    "RequestLog",
    "Invite",
    "NpsFeedback",
    "PostFeedback",
    "BugReport",
    "AiUsageLog",
]
