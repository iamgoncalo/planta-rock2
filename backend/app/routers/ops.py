"""
Operations router — alerts, routing, nearest-wc, publish.

Routes
------
GET  /api/v1/alerts                      — active alert list
GET  /api/v1/routing/recommend           — routing recommendation
GET  /api/v1/nearest-wc                  — nearest WC for visitor GPS
POST /api/v1/publish                     — manual SCOR push trigger
"""
from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from app.data.clusters import CLUSTERS_BY_ID
from app.services.routing import recommend_routing, _section_avg_occupancy, _section_total_queue
from app.state import app_state

router = APIRouter(tags=["ops"])


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

@router.get("/alerts")
async def get_alerts(active: bool = Query(True, description="Return only active alerts")) -> Dict[str, Any]:
    """Return the current list of operational alerts."""
    alerts_out: List[Dict[str, Any]] = []
    for a in app_state.alerts:
        alerts_out.append({
            "cluster_id": a.cluster_id,
            "section": a.section,
            "severidade": a.severidade.value if hasattr(a.severidade, "value") else a.severidade,
            "mensagem": a.mensagem,
            "ts": a.ts,
        })
    return {
        "ts": time.time(),
        "count": len(alerts_out),
        "alerts": alerts_out,
    }


# ---------------------------------------------------------------------------
# Routing recommendation
# ---------------------------------------------------------------------------

@router.get("/routing/recommend")
async def routing_recommend(
    source: Optional[str] = Query(None, alias="from", description="Cluster under pressure e.g. WC-01"),
) -> Dict[str, Any]:
    """
    Return a crowd-routing recommendation.

    If `from` is provided, return the best alternative for that specific cluster.
    Otherwise return all active recommendations for all clusters under pressure.
    """
    if source:
        rec = recommend_routing(source, app_state.cluster_states)
        if rec is None:
            return {
                "ts": time.time(),
                "count": 0,
                "recommendations": [],
                "note": f"No viable alternative found for {source} or cluster not under pressure.",
            }
        return {
            "ts": time.time(),
            "count": 1,
            "recommendations": [rec.model_dump()],
        }

    # All clusters
    from app.services.routing import get_routing_recommendations
    recs = get_routing_recommendations(app_state.cluster_states)
    return {
        "ts": time.time(),
        "count": len(recs),
        "recommendations": [r.model_dump() for r in recs],
    }


# ---------------------------------------------------------------------------
# Nearest WC (visitor app)
# ---------------------------------------------------------------------------

def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in metres between two GPS points."""
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.get("/nearest-wc")
async def nearest_wc(
    lat: float = Query(..., description="Visitor latitude"),
    lon: float = Query(..., description="Visitor longitude"),
    max_results: int = Query(3, ge=1, le=8, description="Number of alternatives to return"),
) -> Dict[str, Any]:
    """
    Return the nearest available WC clusters, ordered by composite score
    (distance + occupancy + queue).
    """
    WALK_SPEED_MS = 1.2  # metres per second, festival crowd pace

    ranked = []
    for cid, cs in app_state.cluster_states.items():
        meta = CLUSTERS_BY_ID.get(cid, {})
        cluster_lat = meta.get("lat", 0.0)
        cluster_lon = meta.get("lon", 0.0)
        dist_m = _haversine_m(lat, lon, cluster_lat, cluster_lon)
        walking_s = int(dist_m / WALK_SPEED_MS)

        avg_occ = _section_avg_occupancy(cs)
        total_queue = _section_total_queue(cs)

        # Wait estimate: queue / (8 pax/min throughput per cluster)
        throughput_pmin = max(1.0, len(cs.secoes) * 8.0)
        queue_wait_s = int((total_queue / throughput_pmin) * 60)

        total_time_s = walking_s + queue_wait_s

        # Pick best status across sections
        statuses = [ss.status.value if hasattr(ss.status, "value") else ss.status for ss in cs.secoes.values()]
        overall_status = "critico" if "critico" in statuses else (
            "cheio" if "cheio" in statuses else (
                "moderado" if "moderado" in statuses else "livre"
            )
        )

        ranked.append({
            "cluster_id": cid,
            "nome": meta.get("nome", cid),
            "distance_m": int(dist_m),
            "walking_time_s": walking_s,
            "queue_wait_s": queue_wait_s,
            "total_time_s": total_time_s,
            "occupancy_pct": round(avg_occ, 1),
            "fila_atual": total_queue,
            "status": overall_status,
            "is_unissex": cs.tipo.value == "unissex" if hasattr(cs.tipo, "value") else cs.tipo == "unissex",
            "entry_only": cs.entry_only,
            "gps": {"lat": cluster_lat, "lon": cluster_lon},
        })

    # Sort by total time (walk + queue); exclude CRITICO
    ranked.sort(key=lambda x: (x["status"] == "critico", x["total_time_s"]))

    recommended = ranked[0] if ranked else None
    alternatives = ranked[1:max_results] if len(ranked) > 1 else []

    return {
        "ts": time.time(),
        "found": recommended is not None,
        "user_gps": {"lat": lat, "lon": lon},
        "recommended": recommended,
        "alternatives": alternatives,
    }


# ---------------------------------------------------------------------------
# Manual SCOR publish
# ---------------------------------------------------------------------------

@router.post("/publish")
async def publish_to_scor() -> Dict[str, Any]:
    """
    Trigger a manual push of current state to SCOR Sensaway.
    If SCOR credentials are not configured, returns a no-op success.
    """
    import logging
    from app.config import get_settings

    settings = get_settings()
    logger = logging.getLogger(__name__)

    if not settings.scor_token_kpi:
        logger.info("SCOR publish requested but no credentials configured — skipping")
        return {
            "ts": time.time(),
            "status": "skipped",
            "reason": "SCOR credentials not configured (set SCOR_TOKEN_KPI in .env)",
            "clusters_pushed": 0,
        }

    # Attempt actual SCOR push
    try:
        import httpx
        from app.routers.websocket import _build_ws_payload

        payload = _build_ws_payload()
        kpis = payload.get("kpis", {})

        headers = {"Authorization": f"Bearer {settings.scor_token_kpi}"}
        base_url = "https://scor.sensaway.com/api/v1"

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{base_url}/ingest",
                json={"kpis": kpis, "ts": time.time()},
                headers=headers,
            )
            resp.raise_for_status()

        logger.info("SCOR manual push succeeded: HTTP %d", resp.status_code)
        return {
            "ts": time.time(),
            "status": "ok",
            "scor_http_status": resp.status_code,
            "clusters_pushed": len(app_state.cluster_states),
        }
    except Exception as exc:
        logger.warning("SCOR manual push failed: %s", exc)
        return {
            "ts": time.time(),
            "status": "error",
            "error": str(exc),
            "clusters_pushed": 0,
        }
