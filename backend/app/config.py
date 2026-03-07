import sys

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Campos obrigatórios em produção — qualquer ausência causa exit(1) no startup
_REQUIRED_IN_PRODUCTION: tuple[str, ...] = (
    "SECRET_KEY",
    "DATABASE_URL",
    "ANTHROPIC_API_KEY",
    "ENCRYPTION_KEY",
    "SENTRY_DSN",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Backend
    SECRET_KEY: str = "dev-secret-change-in-production"
    DATABASE_URL: str = "sqlite+aiosqlite:///./logia.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    DEBUG: bool = True

    # LLM
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Social — Instagram
    META_ACCESS_TOKEN: str = ""
    META_INSTAGRAM_ACCOUNT_ID: str = ""

    # Social — Twitter
    TWITTER_BEARER_TOKEN: str = ""
    TWITTER_CONSUMER_KEY: str = ""
    TWITTER_CONSUMER_SECRET: str = ""
    TWITTER_ACCESS_TOKEN: str = ""
    TWITTER_ACCESS_TOKEN_SECRET: str = ""

    # Social — LinkedIn
    LINKEDIN_ACCESS_TOKEN: str = ""
    LINKEDIN_PERSON_ID: str = ""

    # Email
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "newsletter@dominio.com"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""

    # Coleta
    APIFY_TOKEN: str = ""
    YOUTUBE_API_KEY: str = ""
    RAPIDAPI_KEY: str = ""

    # Google
    GOOGLE_SERVICE_ACCOUNT_JSON: str = "./credentials/google-sa.json"
    GOOGLE_DRIVE_FOLDER_ID: str = ""

    # Imagem
    STABILITY_AI_KEY: str = ""

    # Observabilidade
    SENTRY_DSN: str = ""
    ENVIRONMENT: str = "development"  # development | production
    BUILD_SHA: str = "dev"            # injetado pelo Docker build-arg

    # Criptografia de tokens OAuth
    # Gerar com: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    ENCRYPTION_KEY: str = ""

    # Alertas
    SLACK_WEBHOOK: str = ""

    # Admin (beta launch)
    # Gerar com: openssl rand -hex 24
    ADMIN_KEY: str = ""

    # Monitoramento de custos de IA
    # Alerta Slack se custo diário > este valor (USD)
    AI_COST_ALERT_USD: float = 10.0

    @field_validator("ENCRYPTION_KEY")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        if v and len(v) != 44:
            raise ValueError(
                "ENCRYPTION_KEY inválida — deve ser gerada com Fernet.generate_key() "
                f"(44 chars base64). Tamanho atual: {len(v)}"
            )
        return v


settings = Settings()


def validate_production_config() -> None:
    """Verifica variáveis obrigatórias em produção. Chama no lifespan do app.

    Se qualquer campo obrigatório estiver vazio, loga erro crítico e encerra
    o processo imediatamente — nunca subir em produção com config incompleta.
    """
    if settings.ENVIRONMENT != "production":
        return

    missing = [
        field for field in _REQUIRED_IN_PRODUCTION
        if not getattr(settings, field, "")
    ]
    if missing:
        # Usar print direto — logger pode não estar configurado ainda
        print(
            f"[CRITICAL] Variáveis obrigatórias ausentes em produção: {missing}. "
            "Encerrando o processo.",
            file=sys.stderr,
        )
        sys.exit(1)
