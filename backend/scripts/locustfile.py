"""Locust load testing — Logia Marketing Platform.

Cenários:
  NormalUser        (weight=80) — uso normal: health + pipeline + library
  PipelineCreator   (weight=15) — criação de pipeline
  LibraryBrowser    (weight=5)  — leitura da biblioteca com paginação/filtros

Pré-requisitos:
  1. Backend rodando em http://localhost:8000
  2. DB migrado (alembic upgrade head)

Execução:
  locust -f scripts/locustfile.py --headless -u 10  -r 2  --run-time 60s --csv scripts/results_10u
  locust -f scripts/locustfile.py --headless -u 50  -r 5  --run-time 60s --csv scripts/results_50u
  locust -f scripts/locustfile.py --headless -u 100 -r 10 --run-time 60s --csv scripts/results_100u
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jose import jwt
from locust import HttpUser, between, events, tag, task

# ── Constantes ────────────────────────────────────────────────────────────────

SECRET_KEY = "dev-secret-change-in-production"
ALGORITHM = "HS256"
DB_PATH = str(Path(__file__).parent.parent / "logia.db")
NUM_TEST_USERS = 50

# Pool compartilhado: preenchido no evento test_start
_user_pool: list[dict] = []   # [{"id": str, "token": str, "pipeline_id": str}]
_pool_index = 0


# ── Seeding ───────────────────────────────────────────────────────────────────


def _make_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    return jwt.encode(
        {"sub": user_id, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM
    )


def _seed_db() -> list[dict]:
    """Insere usuários e pipelines de teste no SQLite, idempotente."""
    conn = sqlite3.connect(DB_PATH)
    now = datetime.now(timezone.utc).isoformat()
    users = []

    for i in range(NUM_TEST_USERS):
        user_id = f"lt-user-{i:03d}"
        pipeline_id = f"lt-pipe-{i:03d}"
        email = f"loadtest{i:03d}@logia.test"

        # Upsert user
        conn.execute(
            """
            INSERT OR IGNORE INTO users
              (id, email, hashed_password, name, is_active, nicho, persona, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                email,
                "$2b$12$placeholder_hash_for_load_test_only",  # nunca usado: auth via JWT
                "Load Test User",
                1,
                "marketing digital",
                "empreendedores",
                now,
                now,
            ),
        )

        # Upsert pipeline
        conn.execute(
            """
            INSERT OR IGNORE INTO pipeline_sessions
              (id, user_id, state, channels_selected, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                pipeline_id,
                user_id,
                "RESEARCHING",
                '["instagram","linkedin"]',
                now,
                now,
            ),
        )

        users.append(
            {
                "id": user_id,
                "token": _make_token(user_id),
                "pipeline_id": pipeline_id,
            }
        )

    conn.commit()
    conn.close()
    return users


# ── Eventos Locust ────────────────────────────────────────────────────────────


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global _user_pool
    print(f"\n[seed] Populando {NUM_TEST_USERS} usuários de teste em {DB_PATH}...")
    _user_pool = _seed_db()
    print(f"[seed] {len(_user_pool)} usuários prontos.\n")


# ── Mixin de autenticação ─────────────────────────────────────────────────────


class _AuthMixin:
    """Seleciona um slot de usuário do pool e configura headers."""

    def on_start(self):
        global _pool_index
        idx = _pool_index % len(_user_pool)
        _pool_index += 1
        slot = _user_pool[idx]
        self.user_id: str = slot["id"]
        self.pipeline_id: str = slot["pipeline_id"]
        self.auth_headers: dict = {"Authorization": f"Bearer {slot['token']}"}


# ── Cenário 1: Uso Normal (weight=80) ─────────────────────────────────────────


class NormalUser(_AuthMixin, HttpUser):
    """80 % do tráfego — navegação típica da plataforma."""

    weight = 80
    wait_time = between(2, 5)

    @task(1)
    def health(self):
        self.client.get("/health", name="GET /health")

    @task(3)
    def get_pipeline(self):
        self.client.get(
            f"/api/pipeline/{self.pipeline_id}",
            headers=self.auth_headers,
            name="GET /api/pipeline/{id}",
        )

    @task(4)
    def get_library_copies(self):
        self.client.get(
            "/api/library/copies?page=1&per_page=20",
            headers=self.auth_headers,
            name="GET /api/library/copies",
        )

    @task(2)
    def get_library_copies_p2(self):
        self.client.get(
            "/api/library/copies?page=2&per_page=20",
            headers=self.auth_headers,
            name="GET /api/library/copies (p2)",
        )


# ── Cenário 2: Criação de Pipeline (weight=15) ────────────────────────────────


class PipelineCreator(_AuthMixin, HttpUser):
    """15 % do tráfego — criação e acompanhamento de pipeline."""

    weight = 15
    wait_time = between(5, 15)

    @task(1)
    def start_pipeline(self):
        with self.client.post(
            "/api/pipeline/start",
            json={"channels": ["instagram", "linkedin"]},
            headers=self.auth_headers,
            name="POST /api/pipeline/start",
            catch_response=True,
        ) as resp:
            if resp.status_code in (201, 429):
                resp.success()  # 429 é esperado pelo rate limit

    @task(2)
    def poll_pipeline(self):
        self.client.get(
            f"/api/pipeline/{self.pipeline_id}",
            headers=self.auth_headers,
            name="GET /api/pipeline/{id} (poll)",
        )

    @task(1)
    def get_library_posts(self):
        self.client.get(
            "/api/library/posts?page=1&per_page=10",
            headers=self.auth_headers,
            name="GET /api/library/posts",
        )


# ── Cenário 3: Leitura da Biblioteca (weight=5) ───────────────────────────────


class LibraryBrowser(_AuthMixin, HttpUser):
    """5 % do tráfego — navegação intensiva na biblioteca."""

    weight = 5
    wait_time = between(1, 3)

    @task(3)
    def get_copies_instagram(self):
        self.client.get(
            "/api/library/copies?channel=instagram&page=1&per_page=20",
            headers=self.auth_headers,
            name="GET /api/library/copies?channel=instagram",
        )

    @task(2)
    def get_copies_linkedin(self):
        self.client.get(
            "/api/library/copies?channel=linkedin&page=1&per_page=20",
            headers=self.auth_headers,
            name="GET /api/library/copies?channel=linkedin",
        )

    @task(2)
    def get_arts(self):
        self.client.get(
            "/api/library/arts?page=1&per_page=20",
            headers=self.auth_headers,
            name="GET /api/library/arts",
        )

    @task(1)
    def get_profiles(self):
        self.client.get(
            "/api/settings/profiles",
            headers=self.auth_headers,
            name="GET /api/settings/profiles",
        )
