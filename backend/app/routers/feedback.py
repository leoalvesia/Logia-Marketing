"""Router de feedback: NPS, pós-publicação e bug reports.

Endpoints públicos (requer autenticação JWT):
  POST /feedback/nps     → Net Promoter Score
  POST /feedback/post    → Avaliação pós-publicação
  POST /feedback/bug     → Bug report (capturado no Sentry + alerta Slack)

Endpoints admin (requer X-Admin-Key):
  GET  /feedback/nps/stats  → Estatísticas NPS
  GET  /feedback/nps        → Lista NPS com filtros
  GET  /feedback/bugs       → Lista bug reports
  PATCH /feedback/bugs/{id} → Atualiza status do bug
  GET  /feedback/export     → Exporta CSV
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import sentry_sdk
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.logger import get_logger
from app.models.feedback import BugReport, NpsFeedback, PostFeedback
from app.models.user import User

router = APIRouter()
logger = get_logger(__name__)


# ── Admin dependency (reutilizada do invites router) ──────────────────────────


async def _require_admin(x_admin_key: str = Header(..., alias="X-Admin-Key")) -> None:
    if not settings.ADMIN_KEY:
        raise HTTPException(status_code=503, detail="ADMIN_KEY não configurado")
    if x_admin_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Acesso negado")


# ── Schemas ────────────────────────────────────────────────────────────────────


class NpsRequest(BaseModel):
    score: int = Field(..., ge=0, le=10)
    comment: Optional[str] = Field(default=None, max_length=2000)


class PostFeedbackRequest(BaseModel):
    pipeline_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=2000)


class BugReportRequest(BaseModel):
    description: str = Field(..., min_length=10, max_length=5000)
    url: Optional[str] = Field(default=None, max_length=1000)
    user_agent: Optional[str] = Field(default=None, max_length=500)
    screenshot_b64: Optional[str] = Field(default=None)


class BugStatusPatch(BaseModel):
    status: str = Field(..., pattern="^(new|analyzing|resolved)$")


# ── Endpoints de usuário ───────────────────────────────────────────────────────


@router.post("/nps", status_code=status.HTTP_201_CREATED)
async def submit_nps(
    body: NpsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Salva resposta de NPS. Dispara alerta Slack se score ≤ 6."""
    entry = NpsFeedback(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        score=body.score,
        comment=body.comment,
    )
    db.add(entry)
    await db.commit()
    logger.info("nps_submitted", user_id=current_user.id, score=body.score)

    # Alerta imediato para detratores (score ≤ 6)
    if body.score <= 6:
        try:
            from app.tasks.feedback_tasks import alert_low_nps

            alert_low_nps.delay(
                current_user.id,
                current_user.email,
                body.score,
                body.comment,
            )
        except Exception as exc:
            logger.warning("nps_alert_task_failed", error=str(exc))

    return {"id": entry.id, "score": body.score}


@router.post("/post", status_code=status.HTTP_201_CREATED)
async def submit_post_feedback(
    body: PostFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Salva avaliação pós-publicação (1–5 estrelas)."""
    entry = PostFeedback(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        pipeline_id=body.pipeline_id,
        rating=body.rating,
        comment=body.comment,
    )
    db.add(entry)
    await db.commit()
    logger.info("post_feedback_submitted", user_id=current_user.id, rating=body.rating)
    return {"id": entry.id, "rating": body.rating}


@router.post("/bug", status_code=status.HTTP_201_CREATED)
async def submit_bug_report(
    body: BugReportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Salva bug report, envia ao Sentry e alerta Slack."""
    # Capturar no Sentry como user feedback
    sentry_event_id: Optional[str] = None
    try:
        with sentry_sdk.push_scope() as scope:
            scope.user = {"id": current_user.id, "email": current_user.email}
            scope.set_extra("url", body.url)
            scope.set_extra("user_agent", body.user_agent)
            sentry_event_id = sentry_sdk.capture_message(
                f"Bug report: {body.description[:100]}",
                level="warning",
            )
    except Exception as exc:
        logger.warning("sentry_capture_failed", error=str(exc))

    entry = BugReport(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        description=body.description,
        url=body.url,
        user_agent=body.user_agent,
        # Screenshot não persiste mais que 10 MB — truncar se necessário
        screenshot_b64=body.screenshot_b64[:1_400_000] if body.screenshot_b64 else None,
        sentry_event_id=sentry_event_id,
    )
    db.add(entry)
    await db.commit()
    logger.info("bug_report_submitted", user_id=current_user.id, bug_id=entry.id)

    try:
        from app.tasks.feedback_tasks import alert_bug_report

        alert_bug_report.delay(entry.id, current_user.email, body.description, body.url)
    except Exception as exc:
        logger.warning("bug_alert_task_failed", error=str(exc))

    return {"id": entry.id, "message": "Recebemos! Investigaremos em breve."}


# ── Endpoints admin ────────────────────────────────────────────────────────────


@router.get("/nps/stats", dependencies=[Depends(_require_admin)])
async def nps_stats(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Estatísticas de NPS: média, distribuição e tendência diária."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Média e total
    agg = await db.execute(
        select(
            func.avg(NpsFeedback.score).label("avg"),
            func.count(NpsFeedback.id).label("total"),
            func.sum(func.case((NpsFeedback.score >= 9, 1), else_=0)).label("promoters"),
            func.sum(func.case((NpsFeedback.score <= 6, 1), else_=0)).label("detractors"),
        ).where(NpsFeedback.created_at >= since)
    )
    row = agg.one()
    total = row.total or 0
    avg_score = round(float(row.avg), 1) if row.avg else None
    promoters = int(row.promoters or 0)
    detractors = int(row.detractors or 0)
    nps_score = round((promoters - detractors) / total * 100) if total > 0 else None

    # Distribuição 0–10
    dist_q = await db.execute(
        select(NpsFeedback.score, func.count(NpsFeedback.id))
        .where(NpsFeedback.created_at >= since)
        .group_by(NpsFeedback.score)
        .order_by(NpsFeedback.score)
    )
    distribution = {str(score): count for score, count in dist_q.all()}

    # Tendência diária (agrupado por dia)
    trend_q = await db.execute(
        select(
            func.date(NpsFeedback.created_at).label("day"),
            func.avg(NpsFeedback.score).label("avg"),
            func.count(NpsFeedback.id).label("count"),
        )
        .where(NpsFeedback.created_at >= since)
        .group_by(func.date(NpsFeedback.created_at))
        .order_by(func.date(NpsFeedback.created_at))
    )
    trend = [
        {"day": str(day), "avg": round(float(avg), 1), "count": count}
        for day, avg, count in trend_q.all()
    ]

    return {
        "period_days": days,
        "total": total,
        "avg_score": avg_score,
        "nps_score": nps_score,
        "promoters": promoters,
        "detractors": detractors,
        "distribution": distribution,
        "trend": trend,
    }


@router.get("/nps", dependencies=[Depends(_require_admin)])
async def list_nps(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    min_score: Optional[int] = Query(default=None, ge=0, le=10),
    max_score: Optional[int] = Query(default=None, ge=0, le=10),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Lista respostas NPS com paginação e filtro de score."""
    q = select(NpsFeedback).order_by(NpsFeedback.created_at.desc())
    if min_score is not None:
        q = q.where(NpsFeedback.score >= min_score)
    if max_score is not None:
        q = q.where(NpsFeedback.score <= max_score)

    total_q = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_q.scalar_one()

    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    rows = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_next": (page * per_page) < total,
        "items": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "score": r.score,
                "comment": r.comment,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ],
    }


@router.get("/bugs", dependencies=[Depends(_require_admin)])
async def list_bugs(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Lista bug reports com filtro de status e paginação."""
    q = select(BugReport).order_by(BugReport.created_at.desc())
    if status_filter:
        q = q.where(BugReport.status == status_filter)

    total_q = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_q.scalar_one()

    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    rows = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_next": (page * per_page) < total,
        "items": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "description": r.description,
                "url": r.url,
                "user_agent": r.user_agent,
                "status": r.status,
                "sentry_event_id": r.sentry_event_id,
                "has_screenshot": bool(r.screenshot_b64),
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ],
    }


@router.patch("/bugs/{bug_id}", dependencies=[Depends(_require_admin)])
async def update_bug_status(
    bug_id: str,
    body: BugStatusPatch,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Atualiza status de um bug report (new → analyzing → resolved)."""
    result = await db.execute(select(BugReport).where(BugReport.id == bug_id))
    bug = result.scalar_one_or_none()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug report não encontrado")
    bug.status = body.status
    await db.commit()
    return {"id": bug_id, "status": body.status}


@router.get("/export", dependencies=[Depends(_require_admin)])
async def export_csv(
    tipo: str = Query(default="nps", pattern="^(nps|bugs|posts)$"),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Exporta feedback em CSV. tipo=nps|bugs|posts."""
    output = io.StringIO()

    if tipo == "nps":
        result = await db.execute(select(NpsFeedback).order_by(NpsFeedback.created_at.desc()))
        rows = result.scalars().all()
        writer = csv.DictWriter(
            output, fieldnames=["id", "user_id", "score", "comment", "created_at"]
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "score": r.score,
                    "comment": r.comment or "",
                    "created_at": r.created_at.isoformat(),
                }
            )

    elif tipo == "bugs":
        result = await db.execute(select(BugReport).order_by(BugReport.created_at.desc()))
        rows = result.scalars().all()
        writer = csv.DictWriter(
            output,
            fieldnames=["id", "user_id", "description", "url", "status", "created_at"],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "description": r.description,
                    "url": r.url or "",
                    "status": r.status,
                    "created_at": r.created_at.isoformat(),
                }
            )

    else:  # posts
        result = await db.execute(select(PostFeedback).order_by(PostFeedback.created_at.desc()))
        rows = result.scalars().all()
        writer = csv.DictWriter(
            output,
            fieldnames=["id", "user_id", "pipeline_id", "rating", "comment", "created_at"],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "pipeline_id": r.pipeline_id,
                    "rating": r.rating,
                    "comment": r.comment or "",
                    "created_at": r.created_at.isoformat(),
                }
            )

    output.seek(0)
    filename = f"logia_feedback_{tipo}_{datetime.now().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
