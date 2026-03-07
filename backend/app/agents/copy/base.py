"""Classe base para agentes de geração de copy via Claude Sonnet."""

from __future__ import annotations

import json
import logging
import re
from abc import abstractmethod
from typing import Any, Callable, Dict, Optional

from anthropic import Anthropic

from app.config import settings

logger = logging.getLogger(__name__)

_SONNET_MODEL = "claude-sonnet-4-6"

# Cláusula anti-invenção + instrução de formato — idêntica em todos os agentes.
# Centralizada aqui para evitar drift entre os prompts de cada canal.
_NEVER_INVENT_CLAUSE = (
    "NUNCA invente dados — use apenas informações do tema fornecido. "
    "Responda SOMENTE com JSON válido, sem texto fora do bloco JSON."
)


class CopyAgent:
    """Agente base para geração de copy usando Claude Sonnet.

    Cada canal herda esta classe e fornece:
      - ``CHANNEL``        : identificador do canal (str)
      - ``MAX_TOKENS``     : limite de tokens da resposta do LLM (int)
      - ``_CHANNEL_ACTION``: instrução final do user prompt, específica por canal (str)
      - ``_system_prompt``: prompt de sistema com persona e formato JSON esperado
      - ``_empty_output``  : dict válido (schema correto, valores vazios) para caso de erro

    O método ``generate(context)`` é o único ponto de entrada público. Ele:
      1. Chama Claude Sonnet com os prompts montados.
      2. Faz parse do JSON retornado (tolerante a markdown code blocks).
      3. Garante que ``source_url`` sempre vale ``context["link_origem"]``.
      4. Nunca propaga exceção — em erro retorna ``{"error": ..., "source_url": ...}``.
    """

    CHANNEL: str = "base"
    MAX_TOKENS: int = 2048

    # Texto da instrução final do user prompt — sobrescrito por cada subclasse.
    _CHANNEL_ACTION: str = "Gere o conteúdo no formato JSON especificado acima."

    # ── Métodos abstratos ─────────────────────────────────────────────────────

    @abstractmethod
    def _system_prompt(self) -> str:
        """System prompt com persona do especialista e formato JSON esperado."""
        ...

    @abstractmethod
    def _empty_output(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Dict com schema correto e valores vazios — usado quando o LLM falha."""
        ...

    # ── Método público ────────────────────────────────────────────────────────

    def generate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Gera copy para o canal usando Claude Sonnet.

        Args:
            context: Dicionário com as chaves:
                - tema (str): título/tema do conteúdo
                - resumo (str): resumo de 2-3 frases
                - link_origem (str): URL da fonte — obrigatório no output
                - plataformas_origem (list[str]): canais onde o tema foi encontrado
                - nicho_usuario (str): nicho do usuário (ex.: "consultoria B2B")
                - persona_usuario (str): persona-alvo (ex.: "consultores de RH")

        Returns:
            Dict com o conteúdo gerado + ``source_url`` obrigatório.
            Em caso de erro: ``{"error": "<mensagem>", "source_url": "<link_origem>"}``.
            Nunca lança exceção.
        """
        try:
            client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            resp = client.messages.create(
                model=_SONNET_MODEL,
                max_tokens=self.MAX_TOKENS,
                system=self._system_prompt(),
                messages=[{"role": "user", "content": self._user_prompt(context)}],
            )
            raw_text: str = resp.content[0].text
            result: Dict[str, Any] = self._parse_json(raw_text)
        except Exception as e:
            logger.error(f"{self.CHANNEL}: generate falhou: {e}")
            result = {"error": str(e)}

        # REGRA CRÍTICA: source_url SEMPRE vem do contexto — nunca do LLM.
        result["source_url"] = context.get("link_origem", "")
        return result

    def generate_streaming(
        self,
        context: Dict[str, Any],
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """Gera copy com streaming — invoca ``on_chunk`` para cada delta de texto.

        Usa ``client.messages.stream()`` para receber a resposta do Claude
        incrementalmente. O resultado final é idêntico ao de ``generate()``.

        Args:
            context: Mesmo dicionário de ``generate()``.
            on_chunk: Callable(str) chamado para cada delta de texto recebido.
                      Útil para emitir chunks via WebSocket em tempo real.

        Returns:
            Dict com o conteúdo gerado + ``source_url``. Em caso de erro,
            devolve ``{"error": ..., "source_url": ...}``.
        """
        full_text = ""
        try:
            client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            with client.messages.stream(
                model=_SONNET_MODEL,
                max_tokens=self.MAX_TOKENS,
                system=self._system_prompt(),
                messages=[{"role": "user", "content": self._user_prompt(context)}],
            ) as stream:
                for text_delta in stream.text_stream:
                    full_text += text_delta
                    if on_chunk:
                        try:
                            on_chunk(text_delta)
                        except Exception:
                            pass  # chunk emission failure nunca aborta a geração
            result: Dict[str, Any] = self._parse_json(full_text)
        except Exception as e:
            logger.error(f"{self.CHANNEL}: generate_streaming falhou: {e}")
            result = {"error": str(e)}

        result["source_url"] = context.get("link_origem", "")
        return result

    # ── Método concreto compartilhado ─────────────────────────────────────────

    def _user_prompt(self, context: Dict[str, Any]) -> str:
        """Monta o user prompt a partir do contexto + _CHANNEL_ACTION da subclasse.

        Subclasses não precisam sobrescrever este método — basta definir
        ``_CHANNEL_ACTION`` com a instrução final específica do canal.
        """
        return self._build_context_header(context) + f"\n{self._CHANNEL_ACTION}"

    # ── Helpers estáticos ─────────────────────────────────────────────────────

    @staticmethod
    def _parse_json(text: str) -> Dict[str, Any]:
        """Extrai dict de resposta que pode conter bloco markdown ```json```."""
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            text = match.group(1)
        return json.loads(text.strip())

    @staticmethod
    def _build_context_header(context: Dict[str, Any]) -> str:
        """Formata as chaves do contexto como cabeçalho de prompt."""
        platforms = ", ".join(context.get("plataformas_origem", []))
        return (
            f"Nicho do usuário: {context.get('nicho_usuario', '')}\n"
            f"Persona-alvo: {context.get('persona_usuario', '')}\n"
            f"Tema: {context.get('tema', '')}\n"
            f"Resumo: {context.get('resumo', '')}\n"
            f"Plataformas de origem: {platforms}\n"
            f"Link da fonte: {context.get('link_origem', '')}\n"
        )
