"""Package dos agentes de copy — mapeamento canal → classe."""

from app.agents.copy.instagram import InstagramCopyAgent
from app.agents.copy.linkedin import LinkedinCopyAgent
from app.agents.copy.twitter import TwitterCopyAgent
from app.agents.copy.youtube import YoutubeCopyAgent
from app.agents.copy.email import EmailCopyAgent

# Mapeamento canal (string) → classe do agente
CHANNEL_AGENTS: dict[str, type] = {
    "instagram": InstagramCopyAgent,
    "linkedin": LinkedinCopyAgent,
    "twitter": TwitterCopyAgent,
    "youtube": YoutubeCopyAgent,
    "email": EmailCopyAgent,
}


def get_agent(channel: str):
    """Retorna instância do agente para o canal especificado.

    Raises:
        ValueError: Se o canal não for reconhecido.
    """
    cls = CHANNEL_AGENTS.get(channel)
    if cls is None:
        raise ValueError(f"Canal desconhecido: {channel!r}")
    return cls()
