"""Feature flags — controle de features em produção sem redeploy.

Valores padrão lidos de variáveis de ambiente no startup do processo.
Overrides em memória sobrepõem os defaults até o próximo restart do servidor.

Variáveis de ambiente:
  FF_CAROUSEL=true          habilita agente de carrossel
  FF_THUMBNAIL=true         habilita agente de thumbnail
  FF_LINKEDIN=false         desabilita publicação no LinkedIn
  FF_YOUTUBE_RESEARCH=false desabilita coleta do YouTube
"""

from __future__ import annotations

import os

# Valores padrão lidos de env vars no startup
_DEFAULTS: dict[str, bool] = {
    "carousel_agent":   os.getenv("FF_CAROUSEL", "false") == "true",
    "thumbnail_agent":  os.getenv("FF_THUMBNAIL", "false") == "true",
    "linkedin_publish": os.getenv("FF_LINKEDIN", "true") == "true",
    "youtube_research": os.getenv("FF_YOUTUBE_RESEARCH", "true") == "true",
}

# Overrides em memória — persistem enquanto o processo estiver rodando
_overrides: dict[str, bool] = {}


def get_flags() -> dict[str, bool]:
    """Retorna todos os feature flags com overrides aplicados."""
    return {**_DEFAULTS, **_overrides}


def get_flag(name: str) -> bool:
    """Retorna o valor atual de um feature flag."""
    if name in _overrides:
        return _overrides[name]
    return _DEFAULTS.get(name, False)


def set_flag(name: str, enabled: bool) -> None:
    """Sobrepõe um feature flag em memória (reset no próximo restart).

    Raises:
        KeyError: se o nome não for um flag registrado.
    """
    if name not in _DEFAULTS:
        raise KeyError(f"Feature flag desconhecida: {name!r}")
    _overrides[name] = enabled
