"""
Clusters router — GET /api/v1/clusters

Returns the current state of all 8 WC clusters including live section data,
GPS coordinates (static metadata), and active alerts.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.state import app_state

router = APIRouter(tags=["clusters"])


def _serialise_cluster(cs) -> Dict[str, Any]:
    """Serialise a ClusterState to the API response format."""
    secoes_out: Dict[str, Any] = {}
    for sec_key, ss in cs.secoes.items():
        secoes_out[sec_key] = {
            "ocupacao_pct": ss.ocupacao_pct,
            "ocupacao_absoluta": ss.ocupacao_absoluta,
            "fila_actual": ss.fila_actual,
            "tempo_espera_min": ss.tempo_espera_min,
            "fluxo_entrada_pmin": ss.fluxo_entrada_pmin,
            "fluxo_saida_pmin": ss.fluxo_saida_pmin,
            "status": ss.status.value if hasattr(ss.status, "value") else ss.status,
            "confianca_pct": ss.confianca_pct,
            "fontes_activas": ss.fontes_activas,
        }

    alertas_out = []
    for a in cs.alertas:
        alertas_out.append({
            "cluster_id": a.cluster_id,
            "section": a.section,
            "severidade": a.severidade.value if hasattr(a.severidade, "value") else a.severidade,
            "mensagem": a.mensagem,
            "ts": a.ts,
        })

    return {
        "cluster_id": cs.cluster_id,
        "nome": cs.nome,
        "tipo": cs.tipo.value if hasattr(cs.tipo, "value") else cs.tipo,
        "entry_only": cs.entry_only,
        "lat": cs.lat,
        "lon": cs.lon,
        "dist_entrada_m": cs.dist_entrada_m,
        "secoes": secoes_out,
        "alertas": alertas_out,
    }


@router.get("/clusters/{cluster_id}")
async def get_cluster(cluster_id: str) -> Dict[str, Any]:
    """Return current state of a single WC cluster by ID."""
    cs = app_state.cluster_states.get(cluster_id)
    if cs is None:
        raise HTTPException(status_code=404, detail=f"Cluster '{cluster_id}' not found")
    return {"ts": __import__("time").time(), "cluster": _serialise_cluster(cs)}


@router.get("/clusters")
async def get_clusters() -> Dict[str, Any]:
    """Return current state of all 8 WC clusters."""
    clusters_out: List[Dict[str, Any]] = []
    for cid in sorted(app_state.cluster_states.keys()):
        cs = app_state.cluster_states[cid]
        clusters_out.append(_serialise_cluster(cs))

    return {
        "ts": time.time(),
        "clusters": clusters_out,
    }
