"""
Logging estruturado com structlog.

JSON em produção, pretty-print em dev.
Campos obrigatórios em todo log:
  timestamp, level, service, environment, request_id, event
"""
from __future__ import annotations

import logging
import sys

import structlog

from app.config import settings

_CONFIGURED = False


def configure_logging() -> None:
    """Chama uma vez no startup — main.py lifespan."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    shared_processors: list = [
        # Injeta campos vindos de structlog.contextvars (request_id, user_id)
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        # Campos fixos de serviço
        _add_service_fields,
    ]

    if settings.ENVIRONMENT == "production":
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )

    # Redirecionar logging stdlib para structlog (captura uvicorn, sqlalchemy, etc.)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    _CONFIGURED = True


def _add_service_fields(logger, method, event_dict: dict) -> dict:
    """Processor que injeta campos fixos em todos os logs."""
    event_dict.setdefault("service", "logia-backend")
    event_dict.setdefault("environment", settings.ENVIRONMENT)
    return event_dict


def get_logger(name: str = "logia") -> structlog.types.FilteringBoundLogger:
    """Retorna logger pré-configurado. Usar no nível de módulo."""
    return structlog.get_logger(name)
