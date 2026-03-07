#!/usr/bin/env python
"""
scripts/benchmark_baseline.py
==============================
Mede latência de resposta dos endpoints principais (10 requests cada).

Usa httpx.AsyncClient com ASGITransport (in-process) e SQLite em memória
para resultados reproduzíveis sem necessidade de servidor externo.

Salva resultados em scripts/benchmark_results.json como baseline.

Uso:
    cd backend
    python scripts/benchmark_baseline.py
"""

from __future__ import annotations

import asyncio
import json
import statistics
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import logging

import httpx
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Silenciar SQLAlchemy echo durante o benchmark
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
logging.getLogger("app").setLevel(logging.WARNING)

# ── Banco de dados em memória para o benchmark ────────────────────────────────

_TEST_ENGINE = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    echo=False,
)
_TEST_MAKER = async_sessionmaker(
    _TEST_ENGINE, class_=AsyncSession, expire_on_commit=False
)


async def _get_db_override():
    async with _TEST_MAKER() as session:
        yield session


# ── Imports da app (após configurar o engine) ─────────────────────────────────
# NOTA: 'app' é o nome do pacote Python. A instância FastAPI é importada como
# 'fastapi_app' para evitar que 'import app.models' sobrescreva o binding.

import app.models  # noqa: E402,F401 — registra todos os models ANTES de tudo
from app.auth import get_current_user  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.models.art import Art, ArtType  # noqa: E402
from app.models.copy import Copy, CopyChannel, CopyStatus  # noqa: E402
from app.models.pipeline import Pipeline, PipelineState  # noqa: E402
from app.models.user import User  # noqa: E402

# ── Setup de dados de teste ───────────────────────────────────────────────────


async def _setup_data() -> dict[str, str]:
    """Cria schema e dados iniciais no banco em memória."""
    async with _TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    user_id = str(uuid.uuid4())
    pipeline_id = str(uuid.uuid4())
    copy_id = str(uuid.uuid4())
    art_id = str(uuid.uuid4())

    async with _TEST_MAKER() as db:
        db.add(User(id=user_id, email="bench@logia.com", hashed_password="hash", name="Bench"))
        await db.flush()
        db.add(Pipeline(id=pipeline_id, user_id=user_id, state=PipelineState.RESEARCHING))
        await db.flush()
        db.add(
            Copy(
                id=copy_id,
                pipeline_id=pipeline_id,
                channel=CopyChannel.INSTAGRAM,
                status=CopyStatus.DRAFT,
                content='{"caption":"Benchmark","hashtags":["#ia","#marketing"]}',
                source_url="https://example.com/benchmark",
            )
        )
        db.add(
            Art(
                id=art_id,
                copy_id=copy_id,
                pipeline_id=pipeline_id,
                art_type=ArtType.STATIC,
                image_urls='["https://example.com/bench.png"]',
            )
        )
        await db.commit()

    return {
        "user_id": user_id,
        "pipeline_id": pipeline_id,
        "copy_id": copy_id,
        "art_id": art_id,
    }


# ── Runner de benchmark ───────────────────────────────────────────────────────


async def _bench(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    headers: dict[str, str],
    json_body: dict | None = None,
    n_warmup: int = 3,
    n_measure: int = 10,
) -> dict[str, Any]:
    """Executa n_measure requests e devolve estatísticas de latência (ms)."""
    # Warmup — aquece JIT / conexão
    for _ in range(n_warmup):
        if method == "GET":
            await client.get(path, headers=headers)
        else:
            await client.post(path, headers=headers, json=json_body)

    durations: list[float] = []
    status_codes: list[int] = []

    for _ in range(n_measure):
        t0 = time.perf_counter()
        if method == "GET":
            resp = await client.get(path, headers=headers)
        else:
            resp = await client.post(path, headers=headers, json=json_body)
        durations.append((time.perf_counter() - t0) * 1000)
        status_codes.append(resp.status_code)

    sorted_d = sorted(durations)
    return {
        "endpoint": f"{method} {path}",
        "n": n_measure,
        "min_ms": round(min(durations), 2),
        "max_ms": round(max(durations), 2),
        "mean_ms": round(statistics.mean(durations), 2),
        "median_ms": round(statistics.median(durations), 2),
        "p95_ms": round(sorted_d[max(0, int(n_measure * 0.95) - 1)], 2),
        "status_codes": sorted(set(status_codes)),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Main ──────────────────────────────────────────────────────────────────────


async def main() -> None:
    print("=" * 55)
    print("  Logia Backend — Benchmark Baseline")
    print("  Ambiente: ASGITransport + SQLite in-memory")
    print("=" * 55)

    # Override de dependências
    fastapi_app.dependency_overrides[get_db] = _get_db_override
    ids = await _setup_data()

    mock_user = MagicMock(spec=User)
    mock_user.id = ids["user_id"]
    mock_user.is_active = True
    fastapi_app.dependency_overrides[get_current_user] = lambda: mock_user

    auth_header = {"Authorization": "Bearer mock-not-validated"}

    # Endpoints a medir: (method, path, json_body, description)
    endpoints: list[tuple[str, str, dict | None, str]] = [
        ("POST", "/api/pipeline/start",
         {"channels": ["instagram", "linkedin", "twitter", "youtube", "email"]},
         "Criar pipeline"),
        ("GET",  f"/api/pipeline/{ids['pipeline_id']}",
         None,
         "Buscar pipeline por ID"),
        ("GET",  "/api/library/copies",
         None,
         "Listar copies (sem filtro)"),
        ("GET",  "/api/library/copies?channel=instagram",
         None,
         "Listar copies (filtro canal)"),
        ("GET",  "/api/library/arts",
         None,
         "Listar artes"),
        ("GET",  "/api/library/posts",
         None,
         "Listar posts (copies+arts por pipeline)"),
        ("GET",  "/api/settings/profiles",
         None,
         "Listar perfis monitorados"),
        ("GET",  "/health",
         None,
         "Health check"),
    ]

    results: list[dict[str, Any]] = []

    async with httpx.AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://testserver",
    ) as client:
        for method, path, body, desc in endpoints:
            label = f"{method:4s} {path}"
            print(f"\n  [{desc}]")
            print(f"  {label}")
            result = await _bench(client, method, path, auth_header, body)
            results.append(result)
            print(
                f"  min={result['min_ms']:.1f}ms  "
                f"median={result['median_ms']:.1f}ms  "
                f"mean={result['mean_ms']:.1f}ms  "
                f"p95={result['p95_ms']:.1f}ms  "
                f"status={result['status_codes']}"
            )

    fastapi_app.dependency_overrides.clear()

    # Aguarda tasks de métricas finalizarem
    await asyncio.sleep(0.1)

    # Ordena por mediana descrescente para o relatório
    by_slowest = sorted(results, key=lambda r: r["median_ms"], reverse=True)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": "ASGITransport + SQLite in-memory (Python in-process)",
        "warmup_requests_per_endpoint": 3,
        "measured_requests_per_endpoint": 10,
        "results": results,
        "results_by_slowest": [
            {"rank": i + 1, **r} for i, r in enumerate(by_slowest)
        ],
    }

    out_path = Path(__file__).parent / "benchmark_results.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 55)
    print("  TOP 5 ENDPOINTS MAIS LENTOS (por mediana)")
    print("=" * 55)
    for i, r in enumerate(by_slowest[:5], 1):
        print(f"  #{i} {r['endpoint']:<45} {r['median_ms']:.1f} ms")

    print(f"\n  Resultados salvos em: {out_path.resolve()}\n")


if __name__ == "__main__":
    asyncio.run(main())
