"""
TV screen router — GET /api/v1/tv/{screen_id}

Returns the best WC recommendation for a given TV screen location,
computed via Haversine distance and queue wait time ranking.
"""
from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.state import app_state

router = APIRouter(tags=["tv"])

# ---------------------------------------------------------------------------
# Static TV screen registry
# ---------------------------------------------------------------------------

TV_SCREENS: Dict[str, Dict[str, Any]] = {
    "TV-PALCO-MUNDO-EAST": {"lat": 38.78195, "lon": -9.09200, "zone": "Palco Mundo East"},
    "TV-PALCO-MUNDO-WEST": {"lat": 38.78195, "lon": -9.09400, "zone": "Palco Mundo West"},
    "TV-MUSIC-VALLEY":     {"lat": 38.78069, "lon": -9.09300, "zone": "Music Valley"},
    "TV-SUPER-BOCK":       {"lat": 38.78150, "lon": -9.09500, "zone": "Super Bock"},
    "TV-MAIN-ENTRANCE":    {"lat": 38.78111, "lon": -9.09310, "zone": "Entrada Principal"},
    "TV-WC-05":            {"lat": 38.78150, "lon": -9.09303, "zone": "WC-05 Zone"},
    "TV-WC-06":            {"lat": 38.78010, "lon": -9.09549, "zone": "WC-06 Zone"},
}

WALKING_SPEED_MS = 1.2  # metres per second
SECONDS_PER_PERSON_IN_QUEUE = 7


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in metres."""
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _cluster_summary(cluster_id: str) -> Dict[str, Any]:
    """Derive a simple summary dict for ranking from cluster state."""
    cs = app_state.cluster_states.get(cluster_id)
    if cs is None:
        return {
            "cluster_id": cluster_id,
            "nome": cluster_id,
            "status": "livre",
            "occupancy_pct": 0.0,
            "total_queue": 0,
            "lat": 0.0,
            "lon": 0.0,
        }

    # Aggregate across all sections
    total_queue = 0
    occ_vals: List[float] = []
    worst_status = "livre"
    status_order = {"critico": 3, "cheio": 2, "moderado": 1, "livre": 0}

    for ss in cs.secoes.values():
        total_queue += ss.fila_actual
        occ_vals.append(ss.ocupacao_pct)
        sec_status = ss.status.value if hasattr(ss.status, "value") else str(ss.status)
        if status_order.get(sec_status, 0) > status_order.get(worst_status, 0):
            worst_status = sec_status

    avg_occ = sum(occ_vals) / len(occ_vals) if occ_vals else 0.0

    return {
        "cluster_id": cluster_id,
        "nome": cs.nome,
        "status": worst_status,
        "occupancy_pct": round(avg_occ, 1),
        "total_queue": total_queue,
        "lat": cs.lat,
        "lon": cs.lon,
    }


@router.get("/tv/{screen_id}")
async def get_tv_state(screen_id: str) -> Any:
    """Return best WC recommendation for a TV screen."""
    screen = TV_SCREENS.get(screen_id)
    if screen is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Unknown screen_id: {screen_id}"},
        )

    screen_lat = screen["lat"]
    screen_lon = screen["lon"]

    cluster_ids = sorted(app_state.cluster_states.keys())
    ranked: List[Dict[str, Any]] = []
    avoid: List[Dict[str, Any]] = []

    for cid in cluster_ids:
        summary = _cluster_summary(cid)
        dist_m = _haversine_m(screen_lat, screen_lon, summary["lat"], summary["lon"])
        walk_time_s = int(dist_m / WALKING_SPEED_MS)
        queue_wait_s = summary["total_queue"] * SECONDS_PER_PERSON_IN_QUEUE

        entry = {
            "cluster_id": cid,
            "nome": summary["nome"],
            "walk_time_s": walk_time_s,
            "queue_wait_s": queue_wait_s,
            "occupancy_pct": summary["occupancy_pct"],
            "fila": summary["total_queue"],
            "status": summary["status"],
            "_dist_m": dist_m,
            "_sort_key": walk_time_s + queue_wait_s,
            "_is_critico": summary["status"] == "critico",
        }
        ranked.append(entry)

    # Sort: non-critico first, then by total time
    ranked.sort(key=lambda x: (x["_is_critico"], x["_sort_key"]))

    # Collect avoid list (critico clusters)
    for entry in ranked:
        if entry["_is_critico"]:
            avoid.append({
                "cluster_id": entry["cluster_id"],
                "reason": "Cluster em estado CRÍTICO — evitar",
            })

    # Clean up internal sort keys before returning
    def _clean(e: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in e.items() if not k.startswith("_")}

    non_critico = [e for e in ranked if not e["_is_critico"]]
    best_wc = _clean(non_critico[0]) if non_critico else _clean(ranked[0])
    alternatives = [_clean(e) for e in (non_critico[1:3] if len(non_critico) > 1 else ranked[1:3])]

    return {
        "screen_id": screen_id,
        "zone": screen["zone"],
        "ts": time.time(),
        "language": "pt",
        "best_wc": best_wc,
        "alternatives": alternatives,
        "avoid": avoid,
        "simulado": True,
    }
