"""
Criptografia simétrica para tokens OAuth armazenados no banco.

Usa Fernet (AES-128-CBC + HMAC-SHA256) da biblioteca cryptography.
Gerar chave: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Regras:
  - NUNCA logar tokens, nem em debug — usar apenas IDs/plataformas nos logs
  - encrypt_token / decrypt_token são a única interface pública
  - Se ENCRYPTION_KEY estiver vazia (dev sem configuração), opera sem criptografia
    e emite aviso. Em produção, a config.py valida que a chave está presente.
"""
from __future__ import annotations

import logging

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

_fernet: Fernet | None = None
_warn_no_key_sent = False


def _get_fernet() -> Fernet | None:
    global _fernet, _warn_no_key_sent
    if _fernet is not None:
        return _fernet

    from app.config import settings

    key = settings.ENCRYPTION_KEY
    if not key:
        if not _warn_no_key_sent:
            logger.warning(
                "ENCRYPTION_KEY não configurada — tokens armazenados sem criptografia. "
                "Defina ENCRYPTION_KEY em produção."
            )
            _warn_no_key_sent = True
        return None

    _fernet = Fernet(key.encode())
    return _fernet


def encrypt_token(plain: str) -> str:
    """Criptografa um token OAuth antes de persistir no banco.

    Retorna o token em base64 cifrado. Se ENCRYPTION_KEY não estiver
    configurada, retorna o texto plano com prefixo indicador.
    """
    fernet = _get_fernet()
    if fernet is None:
        return plain  # dev sem chave — não criptografa

    return fernet.encrypt(plain.encode()).decode()


def decrypt_token(stored: str) -> str:
    """Decriptografa um token OAuth lido do banco.

    Lida com tokens antigos (texto plano) transparentemente.
    Nunca loga o valor decriptografado.
    """
    fernet = _get_fernet()
    if fernet is None:
        return stored  # dev sem chave

    try:
        return fernet.decrypt(stored.encode()).decode()
    except InvalidToken:
        # Token pode ser texto plano legado (antes da implementação da crypto)
        logger.warning("decrypt_token: token não é Fernet — retornando como texto plano (legado)")
        return stored
    except Exception as exc:
        logger.error("decrypt_token: falha inesperada", exc_info=exc)
        raise
