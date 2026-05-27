"""
Chat router — POST /api/v1/chat

Answers operational questions about the festival in European Portuguese.
Uses Gemini 2.5 Flash if GEMINI_API_KEY is set, otherwise uses the
local deterministic fallback.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List

from fastapi import APIRouter

from app.schemas import ChatRequest, ChatResponse
from app.services.chat import chat
from app.services.kpis import calculate_all_kpis
from app.services.routing import get_routing_recommendations
from app.state import app_state

router = APIRouter(tags=["chat"])


def _build_context() -> Dict[str, Any]:
    """Build the live context dict to inject into the chat system prompt."""
    from app.routers.clusters import _serialise_cluster

    clusters_out = []
    for cid in sorted(app_state.cluster_states.keys()):
        cs = app_state.cluster_states[cid]
        clusters_out.append(_serialise_cluster(cs))

    kpis = calculate_all_kpis(
        cluster_states=app_state.cluster_states,
        alerts=app_state.alerts,
        daily_redirected=app_state.daily_redirected,
    )

    routing_recs = get_routing_recommendations(app_state.cluster_states)
    routing_out = [r.model_dump() for r in routing_recs]

    from app.schemas import AlertSeveridade
    critico_count = sum(
        1 for a in app_state.alerts
        if a.severidade == AlertSeveridade.CRITICO
    )

    return {
        "ts": time.time(),
        "clusters": clusters_out,
        "kpis": kpis.model_dump(),
        "alertas_activos": len(app_state.alerts),
        "alertas_criticos": critico_count,
        "show_activo": kpis.show_activo,
        "minutos_para_headliner": kpis.minutos_para_headliner,
        "routing_recommendations": routing_out,
        "scenario": app_state.simulation_scenario,
    }


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest) -> ChatResponse:
    """
    Answer an operational question about the festival.

    Responds in European Portuguese.
    Uses Gemini 2.5 Flash if GEMINI_API_KEY is configured, otherwise
    uses the local deterministic fallback.
    """
    context = _build_context()

    historico = [
        {"role": msg.role, "content": msg.content}
        for msg in req.historico
    ]

    resposta, fonte = await chat(
        mensagem=req.mensagem,
        historico=historico,
        context=context,
    )

    return ChatResponse(resposta=resposta, fonte=fonte)  # type: ignore[arg-type]
