"""
Chat service for PlantaOS × Rock in Rio Lisboa 2026.

If GEMINI_API_KEY is present, uses Gemini 2.5 Flash with live context.
Otherwise, uses a deterministic local fallback that answers from the
context dict. NEVER invents data not present in the context.

All responses are in European Portuguese.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Gemini configuration
# ---------------------------------------------------------------------------
_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent"
)

_SYSTEM_PROMPT_TEMPLATE = """
És o assistente operacional PlantaOS para o Rock in Rio Lisboa 2026.
Respondes SEMPRE em Português Europeu.
Baseias as tuas respostas EXCLUSIVAMENTE nos dados em tempo real fornecidos abaixo.
Nunca inventas dados, nunca referes valores que não estejam no contexto.
Não faças referência a qualquer sistema ou empresa de segurança por nome.
Não incluas dados ambientais (CO2, temperatura, humidade) — apenas contagens de pessoas e fluxos.

ESTADO ACTUAL DO FESTIVAL:
{context_json}

Responde de forma concisa e operacional, como um assistente de controlo de multidões.
""".strip()


# ---------------------------------------------------------------------------
# Local fallback
# ---------------------------------------------------------------------------

def _build_context_summary(context: Dict[str, Any]) -> str:
    """Build a brief Portuguese summary from the context dict."""
    lines = []

    clusters = context.get("clusters", [])
    if clusters:
        lines.append("Estado actual dos clusters WC:")
        for cl in clusters:
            cid = cl.get("cluster_id", "?")
            secoes = cl.get("secoes", {})
            alertas = cl.get("alertas", [])
            for sec_key, sec in secoes.items():
                occ = sec.get("ocupacao_pct", 0)
                fila = sec.get("fila_actual", 0)
                status = sec.get("status", "?")
                lines.append(
                    f"  {cid}/{sec_key}: {occ:.0f}% ocupação, fila={fila}, estado={status}"
                )
            if alertas:
                for a in alertas:
                    lines.append(f"  ALERTA {a.get('severidade','?')}: {a.get('mensagem','')}")

    kpis = context.get("kpis", {})
    if kpis:
        lines.append(
            f"KPIs: Fluxo={kpis.get('kpi_01','?')}, "
            f"Ocupação média={kpis.get('kpi_02','?')}%, "
            f"Alertas críticos={kpis.get('kpi_03','?')}, "
            f"Redirecionados hoje={kpis.get('kpi_04','?')}"
        )

    show = context.get("show_activo")
    if show:
        lines.append(f"Show activo: {show}")

    mins = context.get("minutos_para_headliner")
    if mins is not None:
        lines.append(f"Próximo headliner em {mins:.0f} minutos.")

    return "\n".join(lines) if lines else "Sem dados disponíveis."


def _find_most_free_cluster(context: Dict[str, Any]) -> Optional[str]:
    """Return the cluster_id with the lowest average occupancy."""
    clusters = context.get("clusters", [])
    best_id = None
    best_occ = 101.0
    for cl in clusters:
        secoes = cl.get("secoes", {})
        if not secoes:
            continue
        avg = sum(s.get("ocupacao_pct", 0) for s in secoes.values()) / len(secoes)
        if avg < best_occ:
            best_occ = avg
            best_id = cl.get("cluster_id")
    return best_id


def _find_cluster_to_avoid(context: Dict[str, Any]) -> Optional[str]:
    """Return the cluster_id with the highest average occupancy (CRITICO preferred)."""
    clusters = context.get("clusters", [])
    worst_id = None
    worst_occ = -1.0
    for cl in clusters:
        secoes = cl.get("secoes", {})
        if not secoes:
            continue
        avg = sum(s.get("ocupacao_pct", 0) for s in secoes.values()) / len(secoes)
        if avg > worst_occ:
            worst_occ = avg
            worst_id = cl.get("cluster_id")
    return worst_id


def _local_fallback(mensagem: str, context: Dict[str, Any]) -> str:
    """
    Answer common operational questions from the context dict.
    Returns a response string in European Portuguese.
    """
    msg_lower = mensagem.lower().strip()

    # "Qual é o WC mais livre?"
    if any(kw in msg_lower for kw in [
        "mais livre", "mais vazio", "most free", "least occupied",
        "menos cheio", "menor ocupação",
    ]):
        best = _find_most_free_cluster(context)
        if best:
            clusters = {cl["cluster_id"]: cl for cl in context.get("clusters", [])}
            cl = clusters.get(best, {})
            secoes = cl.get("secoes", {})
            avg = (
                sum(s.get("ocupacao_pct", 0) for s in secoes.values()) / len(secoes)
                if secoes else 0
            )
            nome = cl.get("nome", best)
            return (
                f"O WC com menor ocupação neste momento é **{best}** ({nome}), "
                f"com uma ocupação média de {avg:.0f}%. "
                f"Recomenda-se redireccionar o público para este cluster."
            )
        return "Não há dados suficientes para determinar o WC mais livre."

    # "Qual é o WC a evitar?"
    if any(kw in msg_lower for kw in [
        "evitar", "avoid", "mais cheio", "mais ocupado", "more occupied",
        "crítico", "critico",
    ]):
        worst = _find_cluster_to_avoid(context)
        if worst:
            clusters = {cl["cluster_id"]: cl for cl in context.get("clusters", [])}
            cl = clusters.get(worst, {})
            secoes = cl.get("secoes", {})
            avg = (
                sum(s.get("ocupacao_pct", 0) for s in secoes.values()) / len(secoes)
                if secoes else 0
            )
            nome = cl.get("nome", worst)
            return (
                f"O WC a evitar neste momento é **{worst}** ({nome}), "
                f"com uma ocupação média de {avg:.0f}%. "
                f"Recomenda-se não enviar mais público para este cluster."
            )
        return "Não há dados suficientes para determinar o WC mais congestionado."

    # "Alertas críticos"
    if any(kw in msg_lower for kw in [
        "alertas críticos", "alertas criticos", "critical alerts",
        "quantos alertas", "how many alerts",
    ]):
        kpis = context.get("kpis", {})
        criticos = kpis.get("kpi_03", 0)
        all_alerts = context.get("alertas_activos", criticos)
        if criticos == 0:
            return (
                f"Neste momento não há alertas CRÍTICOS activos. "
                f"Total de alertas activos: {all_alerts}."
            )
        return (
            f"Existem **{criticos} alerta(s) CRÍTICO(s)** activos neste momento. "
            f"Total de alertas activos: {all_alerts}. "
            f"Verifique o painel de clusters para detalhes."
        )

    # "Show activo"
    if any(kw in msg_lower for kw in [
        "show activo", "show ativo", "active show", "que show", "qual show",
        "headliner", "artista",
    ]):
        show = context.get("show_activo")
        mins = context.get("minutos_para_headliner")
        festival_day = context.get("kpis", {}).get("festival_day")

        if show:
            return f"O headliner activo neste momento é **{show}**."
        elif mins is not None:
            return f"Não há headliner em cena agora. O próximo headliner começa em {mins:.0f} minutos."
        elif festival_day:
            return f"Estamos no Dia {festival_day} do festival. Nenhum headliner activo neste momento."
        return "Não há informação de show activo disponível."

    # "Redirecionar de WC-05"
    if any(kw in msg_lower for kw in [
        "redirecionar", "redirect", "wc-05", "wc05", "entry only",
    ]):
        recs = context.get("routing_recommendations", [])
        wc05_recs = [r for r in recs if r.get("from_cluster_id") == "WC-05"]
        if wc05_recs:
            rec = wc05_recs[0]
            dest = rec.get("recommended_cluster_id", "?")
            reason = rec.get("reason", "")
            return (
                f"Recomenda-se redirecionar público de WC-05 para **{dest}**. "
                f"{reason}"
            )
        return (
            "WC-05 é um cluster ENTRY ONLY (sem saídas de emergência). "
            "Neste momento não há recomendação de redirecionamento activa para WC-05. "
            "Se a ocupação for crítica, use o painel de routing para obter alternativas."
        )

    # Generic: list current state
    summary = _build_context_summary(context)
    return (
        f"Estado actual do festival:\n\n{summary}\n\n"
        f"Para questões específicas, pergunte sobre o WC mais livre, "
        f"alertas críticos, show activo, ou redirecionamento."
    )


# ---------------------------------------------------------------------------
# Gemini integration
# ---------------------------------------------------------------------------

async def _call_gemini(
    mensagem: str,
    historico: List[Dict[str, str]],
    context: Dict[str, Any],
    api_key: str,
) -> str:
    """Call Gemini 2.5 Flash with the live festival context."""
    context_json = json.dumps(context, ensure_ascii=False, indent=2)
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(context_json=context_json)

    # Build contents list
    contents = []

    # Inject system instruction as a user/model pair if needed
    # Gemini supports systemInstruction field directly
    for msg in historico:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}],
        })

    # Add current message
    contents.append({
        "role": "user",
        "parts": [{"text": mensagem}],
    })

    payload = {
        "systemInstruction": {
            "parts": [{"text": system_prompt}],
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 512,
        },
    }

    url = f"{_GEMINI_URL}?key={api_key}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise ValueError(f"Unexpected Gemini response format: {data}") from exc


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def chat(
    mensagem: str,
    historico: List[Dict[str, str]],
    context: Dict[str, Any],
) -> tuple[str, str]:
    """
    Process a chat message and return (response_text, fonte).

    Parameters
    ----------
    mensagem : str
        User message.
    historico : list[dict]
        Conversation history with keys "role" and "content".
    context : dict
        Current live festival state (clusters, kpis, alerts, etc.).

    Returns
    -------
    (resposta, fonte) where fonte is "gemini" or "local".
    """
    settings = get_settings()

    if settings.gemini_enabled:
        try:
            resposta = await _call_gemini(
                mensagem=mensagem,
                historico=historico,
                context=context,
                api_key=settings.gemini_api_key,
            )
            return resposta, "gemini"
        except Exception as exc:
            logger.warning(
                "Gemini call failed, falling back to local: %s", exc
            )

    # Local fallback
    resposta = _local_fallback(mensagem, context)
    return resposta, "local"
