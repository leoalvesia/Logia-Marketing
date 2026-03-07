"""Constantes globais da plataforma Logia.

Centraliza limites de caracteres por canal para evitar magic numbers
espalhados nos system prompts e na camada de validação.
"""

from __future__ import annotations

# Limites por canal — usados nos system prompts e na validação de output.
# Chaves numéricas são limites máximos; "_min" e "_max" definem faixas.
CHANNEL_LIMITS: dict[str, dict[str, int]] = {
    "instagram": {
        "caption": 2200,
        "hashtags_min": 5,
        "hashtags_max": 10,
    },
    "linkedin": {
        "post": 3000,
        "abertura_gancho": 150,
    },
    "twitter": {
        "tweet": 280,
        "thread_max": 5,
    },
    "youtube": {
        "descricao": 5000,
        "tags_min": 5,
        "tags_max": 15,
    },
    "email": {
        "subject": 60,
        "preview_text": 90,
        "cta": 40,
        "sections_min": 2,
        "sections_max": 4,
    },
}
