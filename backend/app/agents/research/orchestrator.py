"""Orquestrador de pesquisa.

Agrupa resultados brutos dos coletores por tema similar, calcula score
ponderado (freq × canais, recência, relevância ao nicho) e retorna
os top 10 temas ordenados por score decrescente.
"""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import httpx
from anthropic import Anthropic
from rapidfuzz import fuzz

from app.config import settings

logger = logging.getLogger(__name__)

# ── Constantes ────────────────────────────────────────────────────────────────

_SIMILARITY_THRESHOLD = 70  # % mínimo (token_set_ratio) para considerar mesmo tema
_MAX_TOPICS = 10
_HAIKU_MODEL = "claude-haiku-4-5-20251001"
_URL_VERIFY_TIMEOUT = 5.0  # segundos por requisição HEAD
_URL_VERIFY_WORKERS = 5  # threads paralelas na verificação

# ── Ponto de entrada público ──────────────────────────────────────────────────


def orchestrate(raw_results: list[dict], user_nicho: str) -> list[dict]:
    """Agrupa, pondera e ranqueia temas coletados.

    Args:
        raw_results: Saída combinada dos 4 coletores. Cada item deve ter:
                     {title, description, url, published_at, platform}.
        user_nicho:  Nicho do usuário (ex.: "consultoria de marketing digital").

    Returns:
        Lista de até 10 temas no formato padronizado, ordenados por score
        decrescente. Cada item inclui ``source_verified`` indicando se a URL
        respondeu com HTTP 2xx/3xx. Nunca lança exceção — retorna lista vazia
        em erro.
    """
    if not raw_results:
        return []

    try:
        # 1. Agrupar por similaridade de título
        groups = _group_by_theme(raw_results)

        # 2. Número de plataformas distintas em toda a coleta (normalização)
        all_platforms = {r.get("platform", "") for r in raw_results if r.get("platform")}
        total_platforms = max(1, len(all_platforms))

        # 3. Pontuar cada grupo
        scored: list[dict] = []
        for group in groups:
            item = _build_scored_item(group, user_nicho, total_platforms)
            scored.append(item)

        # 4. Regra crítica: link_origem ausente → score = 0
        for item in scored:
            if not item.get("link_origem"):
                item["score"] = 0.0

        # 5. Verificar URLs em paralelo — nunca retornar fonte sem validação
        unique_urls = list({item["link_origem"] for item in scored if item.get("link_origem")})
        verified_map = _verify_urls_parallel(unique_urls)

        for item in scored:
            url = item.get("link_origem", "")
            if url:
                item["source_verified"] = verified_map.get(url, False)
                if not item["source_verified"]:
                    # Penalidade: URL morta reduz relevância do tema
                    item["score"] = round(item["score"] * 0.5, 4)
                    logger.warning(f"orchestrator: URL não verificável: {url}")
            else:
                item["source_verified"] = False

        # 6. Ordenar por score decrescente (após penalidades)
        scored.sort(key=lambda x: x["score"], reverse=True)

        return scored[:_MAX_TOPICS]

    except Exception as e:
        logger.error(f"orchestrator: falha crítica: {e}")
        return []


# ── Agrupamento ───────────────────────────────────────────────────────────────


def _group_by_theme(items: list[dict]) -> list[list[dict]]:
    """Agrupa itens cujos títulos têm similaridade >= _SIMILARITY_THRESHOLD."""
    groups: list[list[dict]] = []
    representative_titles: list[str] = []

    for item in items:
        title = item.get("title", "")
        matched = False
        for idx, rep_title in enumerate(representative_titles):
            if fuzz.token_set_ratio(title, rep_title) >= _SIMILARITY_THRESHOLD:
                groups[idx].append(item)
                matched = True
                break
        if not matched:
            groups.append([item])
            representative_titles.append(title)

    return groups


# ── Construção e pontuação de cada grupo ─────────────────────────────────────


def _build_scored_item(
    group: list[dict],
    nicho: str,
    total_platforms: int,
) -> dict:
    """Transforma um grupo de itens similares em um tema pontuado."""
    # Selecionar o item representativo: maior descrição (mais informação)
    representative = max(group, key=lambda x: len(x.get("description", "")))

    titulo = representative.get("title", "")
    resumo = _extract_resumo(representative.get("description", ""))
    link_origem = _best_url(group)

    unique_platforms = sorted({item.get("platform", "") for item in group if item.get("platform")})

    # Componentes do score
    freq_entre_canais = len(unique_platforms) / total_platforms  # 0.0–1.0
    recencia = max(_calc_recencia(item.get("published_at", "")) for item in group)
    relevancia_nicho = _score_nicho_relevance(titulo, resumo, nicho)  # 0.0–1.0

    score = round(
        (freq_entre_canais * 0.4) + (recencia * 0.35) + (relevancia_nicho * 0.25),
        4,
    )

    # Data de publicação do item mais recente do grupo
    publicado_em = _best_date(group)

    # Extrair dados numéricos/estatísticas da descrição completa para enriquecer o copy
    full_description = representative.get("description", "")
    dados_pesquisa = _extract_statistics(full_description)

    return {
        "titulo": titulo,
        "resumo": resumo,
        "link_origem": link_origem,
        "plataformas": unique_platforms,
        "score": score,
        "publicado_em": publicado_em,
        "dados_pesquisa": dados_pesquisa,
        "source_verified": False,  # atualizado em orchestrate() após HEAD request
    }


def _extract_resumo(description: str) -> str:
    """Retorna até 3 frases da descrição original, sem inventar conteúdo."""
    if not description:
        return ""
    sentences = [s.strip() for s in description.split(".") if s.strip()]
    return ". ".join(sentences[:3]) + ("." if sentences else "")


def _extract_statistics(description: str) -> str:
    """Extrai frases com dados numéricos da descrição (percentuais, valores, multiplicadores).

    Exemplos capturados: "ROI de 180%", "cresceu 3x", "R$ 1.000", "42 vezes mais".
    Retorna até 3 frases concatenadas, ou string vazia se não houver dados numéricos.
    """
    if not description:
        return ""
    sentences = [s.strip() for s in re.split(r"[.!?\n]", description) if s.strip()]
    _NUMBER_RE = re.compile(
        r"\d+\s*%"  # percentuais: 70%, 3,5%
        r"|\bR\$\s*[\d\.,]+"  # valores em reais: R$ 1.000
        r"|\d+[xX]\b"  # multiplicadores: 3x, 10X
        r"|\d+\s*vezes"  # "42 vezes"
        r"|\d{2,}"  # números com 2+ dígitos: "150 empresas", "42 ferramentas"
    )
    stats = [s for s in sentences if _NUMBER_RE.search(s)]
    return ". ".join(stats[:3]) + ("." if stats else "")


def _best_url(group: list[dict]) -> str:
    """Retorna a primeira URL não vazia do grupo."""
    for item in group:
        url = item.get("url", "").strip()
        if url:
            return url
    return ""


def _best_date(group: list[dict]) -> str:
    """Retorna a data 'YYYY-MM-DD' do item mais recente do grupo."""
    best_dt: datetime | None = None
    for item in group:
        dt = _parse_date(item.get("published_at", ""))
        if dt and (best_dt is None or dt > best_dt):
            best_dt = dt
    if best_dt:
        return best_dt.strftime("%Y-%m-%d")
    return ""


# ── Cálculo de recência ───────────────────────────────────────────────────────


def _calc_recencia(published_at: str) -> float:
    """Pontuação de recência: <48h=1.0, <7dias=0.6, mais antigo=0.2."""
    dt = _parse_date(published_at)
    if dt is None:
        return 0.2
    now = datetime.now(timezone.utc)
    hours_ago = (now - dt).total_seconds() / 3600
    if hours_ago <= 48:
        return 1.0
    if hours_ago <= 168:  # 7 dias
        return 0.6
    return 0.2


def _parse_date(value: str) -> datetime | None:
    """Tenta parsear ISO 8601 com ou sem timezone."""
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


# ── Verificação de URLs ────────────────────────────────────────────────────────


def _verify_url(url: str) -> bool:
    """Faz HEAD request para confirmar que a URL está acessível.

    Retorna True se o servidor responder com HTTP < 400. Retorna False para
    4xx/5xx ou qualquer erro de conexão. Timeout de 5 s para não bloquear.

    Nunca lança exceção — falha silenciosa é tratada como não verificada.
    """
    if not url or not url.startswith(("http://", "https://")):
        return False
    try:
        with httpx.Client(
            timeout=_URL_VERIFY_TIMEOUT,
            follow_redirects=True,
        ) as client:
            resp = client.head(url, headers={"User-Agent": "Logia-Verifier/1.0"})
            return resp.status_code < 400
    except Exception:
        return False


def _verify_urls_parallel(urls: list[str]) -> dict[str, bool]:
    """Verifica uma lista de URLs em paralelo com ThreadPoolExecutor.

    Retorna dict {url: bool} para cada URL fornecida.
    """
    if not urls:
        return {}
    results: dict[str, bool] = {}
    with ThreadPoolExecutor(max_workers=_URL_VERIFY_WORKERS) as executor:
        future_to_url = {executor.submit(_verify_url, url): url for url in urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                results[url] = future.result()
            except Exception:
                results[url] = False
    return results


# ── Relevância ao nicho via Claude Haiku ─────────────────────────────────────


def _score_nicho_relevance(titulo: str, resumo: str, nicho: str) -> float:
    """Pontua de 0 a 1 a relevância do tema para o nicho do usuário.

    Usa Claude Haiku para a avaliação. Retorna 0.5 como fallback seguro
    quando a API não está disponível ou retorna resposta inválida.
    """
    if not settings.ANTHROPIC_API_KEY:
        return 0.5
    try:
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model=_HAIKU_MODEL,
            max_tokens=10,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Pontue de 0 a 1 (número decimal) a relevância do tema "
                        f"abaixo para um profissional do nicho indicado.\n\n"
                        f"Nicho: {nicho}\n"
                        f"Tema: {titulo}\n"
                        f"Resumo: {resumo[:300]}\n\n"
                        f"REGRAS OBRIGATÓRIAS:\n"
                        f"- NÃO invente URLs, estudos, estatísticas ou fontes.\n"
                        f"- NÃO cite percentuais ou números sem fonte real.\n"
                        f"- Use 'segundo tendências do setor' quando não há dado exato.\n"
                        f"- Avalie APENAS com base no texto fornecido acima.\n\n"
                        f"Responda APENAS com um número decimal entre 0 e 1, "
                        f"sem texto adicional. Exemplo: 0.8"
                    ),
                }
            ],
        )
        value = float(resp.content[0].text.strip())
        return max(0.0, min(1.0, value))
    except Exception as e:
        logger.warning(f"orchestrator: relevância_nicho falhou: {e}")
        return 0.5
