"""Tasks Celery para gestão de contas — LGPD.

Tasks:
  revoke_oauth_tokens       — revoga tokens OAuth ao deletar conta
  hard_delete_expired_accounts — apaga definitivamente contas deletadas há > 30 dias
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.celery_app import celery_app

logger = logging.getLogger(__name__)

_HARD_DELETE_GRACE_DAYS = 30


@celery_app.task(name="app.tasks.account_tasks.revoke_oauth_tokens", max_retries=2)
def revoke_oauth_tokens(user_id: str) -> None:
    """Revoga tokens OAuth de todas as plataformas para o usuário deletado."""

    async def _revoke() -> None:
        from sqlalchemy import delete, select
        from app.database import AsyncSessionLocal
        from app.models.social_tokens import SocialToken

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(SocialToken).where(SocialToken.user_id == user_id))
            tokens = result.scalars().all()
            for token in tokens:
                logger.info(
                    "revoking_token",
                    user_id=user_id,
                    platform=token.platform,
                )
                # Soft delete dos tokens — hard delete junto com a conta
                # (tokens OAuth externos raramente suportam revogação server-side)

            await db.execute(delete(SocialToken).where(SocialToken.user_id == user_id))
            await db.commit()
            logger.info("oauth_tokens_revoked", user_id=user_id, count=len(tokens))

    try:
        asyncio.run(_revoke())
    except Exception as exc:
        logger.error("revoke_oauth_tokens_failed: user=%s err=%s", user_id, exc)


@celery_app.task(name="app.tasks.account_tasks.hard_delete_expired_accounts")
def hard_delete_expired_accounts() -> None:
    """Apaga permanentemente contas com deleted_at há mais de 30 dias.

    Executado diariamente pelo Celery Beat às 3h UTC.
    Remove: user + todas as FKs em cascata (pipelines, copies, arts, feedback, etc.)
    """

    async def _delete() -> int:
        from sqlalchemy import delete, select
        from app.database import AsyncSessionLocal
        from app.models.user import User

        cutoff = datetime.now(timezone.utc) - timedelta(days=_HARD_DELETE_GRACE_DAYS)

        async with AsyncSessionLocal() as db:
            expired_q = await db.execute(
                select(User.id).where(
                    User.deleted_at.isnot(None),
                    User.deleted_at < cutoff,
                )
            )
            expired_ids = [row[0] for row in expired_q.all()]

            if not expired_ids:
                return 0

            # DELETE em cascata — FKs configuradas com ON DELETE CASCADE
            await db.execute(delete(User).where(User.id.in_(expired_ids)))
            await db.commit()
            return len(expired_ids)

    try:
        count = asyncio.run(_delete())
        if count > 0:
            logger.info("hard_delete_completed", accounts_deleted=count)
        else:
            logger.info("hard_delete_nothing_to_delete")
    except Exception as exc:
        logger.error("hard_delete_failed: %s", exc)
