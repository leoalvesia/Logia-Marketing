"""Endpoints de gestão de conta — LGPD/GDPR.

GET  /account/export  → exporta todos os dados do usuário em JSON
DELETE /account       → soft delete: anonimiza conta, hard delete após 30 dias

Compliance LGPD:
  Art. 18 LGPD — direito de acesso e portabilidade (export)
  Art. 18 §3 LGPD — direito ao apagamento (delete)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.logger import get_logger
from app.models.art import Art
from app.models.copy import Copy
from app.models.monitored_profiles import MonitoredProfile
from app.models.pipeline import Pipeline
from app.models.user import User

router = APIRouter()
logger = get_logger(__name__)


@router.get("/export")
async def export_account_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Exporta todos os dados do usuário em formato JSON (portabilidade LGPD).

    Inclui: perfil, pipelines, copies, arts, perfis monitorados.
    Exclui: senha (hash nunca exportado), tokens OAuth, logs internos.
    """
    # Pipelines
    pipelines_q = await db.execute(
        select(Pipeline).where(Pipeline.user_id == current_user.id)
        .order_by(Pipeline.created_at.desc())
    )
    pipelines = pipelines_q.scalars().all()
    pipeline_ids = [p.id for p in pipelines]

    # Copies (apenas dos pipelines do usuário)
    copies_q = await db.execute(
        select(Copy).where(Copy.pipeline_id.in_(pipeline_ids))
        .order_by(Copy.created_at.desc())
    ) if pipeline_ids else None
    copies = copies_q.scalars().all() if copies_q else []

    # Arts
    arts_q = await db.execute(
        select(Art).where(Art.pipeline_id.in_(pipeline_ids))
        .order_by(Art.created_at.desc())
    ) if pipeline_ids else None
    arts = arts_q.scalars().all() if arts_q else []

    # Perfis monitorados
    profiles_q = await db.execute(
        select(MonitoredProfile).where(MonitoredProfile.user_id == current_user.id)
    )
    profiles = profiles_q.scalars().all()

    payload = {
        "export_date": datetime.now(timezone.utc).isoformat(),
        "logia_version": "2.0",
        "profile": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "nicho": current_user.nicho,
            "persona": current_user.persona,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "accepted_terms_at": (
                current_user.accepted_terms_at.isoformat()
                if current_user.accepted_terms_at else None
            ),
        },
        "pipelines": [
            {
                "id": p.id,
                "status": p.status,
                "selected_topic_id": p.selected_topic_id,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in pipelines
        ],
        "copies": [
            {
                "id": c.id,
                "pipeline_id": c.pipeline_id,
                "channel": c.channel,
                "content": c.content,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in copies
        ],
        "arts": [
            {
                "id": a.id,
                "pipeline_id": a.pipeline_id,
                "image_url": a.image_url,
                "art_type": a.art_type,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in arts
        ],
        "monitored_profiles": [
            {
                "id": p.id,
                "platform": p.platform,
                "handle": p.handle,
                "is_active": p.is_active,
            }
            for p in profiles
        ],
    }

    logger.info("account_data_exported", user_id=current_user.id)
    return JSONResponse(
        content=payload,
        headers={
            "Content-Disposition": (
                f'attachment; filename="logia_data_{current_user.id[:8]}_'
                f'{datetime.now().strftime("%Y%m%d")}.json"'
            ),
            "Content-Type": "application/json",
        },
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Solicita exclusão de conta (LGPD Art. 18 §3).

    Soft delete imediato:
      - Email anonimizado: deleted_{id}@deleted.logia
      - Nome, nicho, persona e brand_identity removidos
      - deleted_at preenchido com timestamp atual
      - is_active = False (bloqueia login)

    Hard delete:
      - Agendado para 30 dias após deleted_at
      - Executado pelo Celery Beat (task hard_delete_expired_accounts)
    """
    if current_user.deleted_at is not None:
        raise HTTPException(status_code=409, detail="Conta já marcada para exclusão")

    now = datetime.now(timezone.utc)

    # Anonimizar dados pessoais imediatamente
    current_user.email = f"deleted_{current_user.id[:8]}@deleted.logia"
    current_user.name = "Usuário Removido"
    current_user.nicho = None
    current_user.persona = None
    current_user.brand_identity = None
    current_user.is_active = False
    current_user.deleted_at = now

    await db.commit()

    logger.info("account_soft_deleted", user_id=current_user.id)

    # Agendar revogação de tokens OAuth via Celery (fire-and-forget)
    try:
        from app.tasks.account_tasks import revoke_oauth_tokens
        revoke_oauth_tokens.delay(current_user.id)
    except Exception as exc:
        logger.warning("revoke_oauth_tokens_failed", error=str(exc))
