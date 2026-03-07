"""Router de autenticação: registro com convite, login e perfil do usuário."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.database import get_db
from app.middleware.rate_limit import track_login_failure
from app.models.invite import Invite
from app.models.user import User
from app.publishers.welcome_email import send_welcome_email

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    invite_code: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict  # {id, name, email, onboarding_completed}


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=TokenResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    # 1. Validar invite_code — 404 para não revelar existência
    result = await db.execute(select(Invite).where(Invite.code == body.invite_code))
    invite = result.scalar_one_or_none()
    if invite is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convite inválido")

    if invite.is_expired:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Convite expirado")

    if invite.is_used:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Convite já utilizado"
        )

    # 2. Email único
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email já cadastrado"
        )

    # 3. Criar usuário
    user = User(
        id=str(uuid.uuid4()),
        email=body.email,
        hashed_password=hash_password(body.password),
        name=body.name,
    )
    db.add(user)
    await db.flush()  # gera user.id sem commit ainda

    # 4. Marcar convite como usado
    invite.uses_count += 1
    if invite.used_by is None:
        invite.used_by = user.id
        invite.used_at = datetime.now(timezone.utc)

    await db.commit()

    # 5. Email de boas-vindas em background (fire-and-forget)
    asyncio.get_event_loop().run_in_executor(
        None, send_welcome_email, user.name, user.email
    )

    # 6. Retornar token diretamente (evita segundo roundtrip de login)
    token = create_access_token({"sub": user.id})
    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "onboarding_completed": user.onboarding_completed,
        },
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.hashed_password):
        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or (
            request.client.host if request.client else "unknown"
        )
        await track_login_failure(ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": user.id})
    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "onboarding_completed": user.onboarding_completed,
        },
    )


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)) -> dict:
    """Retorna dados do usuário autenticado."""
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "nicho": current_user.nicho,
        "persona": current_user.persona,
        "onboarding_completed": current_user.onboarding_completed,
    }


@router.patch("/me/onboarding", status_code=status.HTTP_200_OK)
async def complete_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Marca o onboarding como concluído para o usuário autenticado."""
    current_user.onboarding_completed = True
    db.add(current_user)
    await db.commit()
    return {"onboarding_completed": True}
