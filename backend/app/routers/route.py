"""
Route recommendation router — POST /api/v1/route

Computes optimal WC routing for a festival-goer given their current location
and preference (fastest / least_crowded / safest / accessible).
"""
from __future__ import annotations

import json
import math
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.data.clusters import ENTRY_ONLY_CLUSTER_IDS
from app.state import app_state

router = APIRouter(tags=["route"])

# Forbidden fields (shared with ingest)
FORBIDDEN_FIELDS = {
    "co2", "temperature", "temperatura", "humidity", "humidade",
    "temp", "hum", "deucalion", "mac", "raw_mac", "face_vector",
    "person_id", "gps",
}

# Clusters with accessible cabins (from cabin layout data)
ACCESSIBLE_CLUSTER_IDS = {"WC-01", "WC-03", "WC-06", "WC-07"}

# LOS congestion penalty in minutes
LOS_PENALTY: Dict[str, float] = {
    "A": 0.0, "B": 0.0, "C": 0.0, "D": 0.5, "E": 1.5, "F": 3.0,
}

WALKING_SPEED_MS = 1.2  # m/s
DEFAULT_LOS = "B"


class RouteRequest(BaseModel):
    lat: float = Field(..., description="User latitude")
    lon: float = Field(..., description="User longitude")
    preference: str = Field("fastest", description="fastest|least_crowded|safest|accessible")


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _is_show_active() -> bool:
    """True if any show is currently active (simulated time = real time)."""
    import datetime
    from app.data.shows import SHOWS
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    now_mins = now.hour * 60 + now.minute
    for show in SHOWS:
        if show["data"] != date_str:
            continue
        h_ini, m_ini = map(int, show["inicio"].split(":"))
        h_fim, m_fim = map(int, show["fim"].split(":"))
        ini = h_ini * 60 + m_ini
        fim = h_fim * 60 + m_fim
        if fim == 0:
            fim = 24 * 60
        if ini <= now_mins < fim:
            return True
    return False


def _reason_for(
    walk_min: float,
    queue_min: float,
    avg_occ: float,
    total_cost: float,
    entry_only: bool,
    preference: str,
) -> str:
    if entry_only:
        return "Entrada temporária — capacidade limitada"
    if queue_min < 0.5 and avg_occ < 50:
        return "Mais próxima · fila reduzida"
    if queue_min < 1.0:
        return "Boa opção · fila pequena"
    if avg_occ < 60:
        return "Pouco lotado"
    if walk_min < 2.0:
        return "Perto · vale a pena"
    return "Opção disponível"


@router.post("/route")
async def get_route(request: Request, body: RouteRequest) -> Dict[str, Any]:
    """Compute optimal WC route for a festival-goer."""

    # Forbidden-field check (note: lat/lon ARE allowed in route body)
    try:
        raw = await request.body()
        body_keys = {k.lower() for k in json.loads(raw).keys()} if raw else set()
    except Exception:
        body_keys = set()
    forbidden_found: List[str] = sorted(body_keys & FORBIDDEN_FIELDS)
    if forbidden_found:
        return JSONResponse(
            status_code=400,
            content={"error": "Forbidden field in payload", "forbidden_fields": forbidden_found},
        )

    user_lat = body.lat
    user_lon = body.lon
    preference = body.preference

    show_active = _is_show_active()
    cluster_ids = sorted(app_state.cluster_states.keys())

    options: List[Dict[str, Any]] = []

    for cid in cluster_ids:
        cs = app_state.cluster_states.get(cid)
        if cs is None:
            continue

        # Accessible filter
        if preference == "accessible" and cid not in ACCESSIBLE_CLUSTER_IDS:
            # Still include, but will be ranked lower — or skip non-accessible
            # Task says "filter to only clusters with accessible cabins"
            continue

        # Compute metrics
        dist_m = _haversine_m(user_lat, user_lon, cs.lat, cs.lon)
        walk_time_min = dist_m / (WALKING_SPEED_MS * 60.0)

        # Aggregate section data
        occ_vals: List[float] = []
        total_queue = 0
        conf_vals: List[float] = []
        worst_status = "livre"
        status_order = {"critico": 3, "cheio": 2, "moderado": 1, "livre": 0}

        for ss in cs.secoes.values():
            occ_vals.append(ss.ocupacao_pct)
            total_queue += ss.fila_actual
            conf_vals.append(ss.confianca_pct)
            sec_status = ss.status.value if hasattr(ss.status, "value") else str(ss.status)
            if status_order.get(sec_status, 0) > status_order.get(worst_status, 0):
                worst_status = sec_status

        avg_occ = sum(occ_vals) / len(occ_vals) if occ_vals else 0.0
        avg_conf = sum(conf_vals) / len(conf_vals) if conf_vals else 100.0
        num_sections = len(cs.secoes)

        throughput_pmin = max(1.0, num_sections * 8.0)
        queue_wait_min = total_queue / throughput_pmin

        congestion_penalty_min = LOS_PENALTY.get(DEFAULT_LOS, 0.0)

        show_surge_penalty_min = 2.0 if (show_active and avg_occ > 80) else 0.0

        low_confidence_penalty_min = 1.0 if avg_conf < 50 else 0.0

        safety_penalty_min = 0.5 if cs.entry_only else 0.0

        # Preference modifiers
        qw_factor = 1.0
        if preference == "least_crowded":
            qw_factor = 2.0
        elif preference == "safest":
            safety_penalty_min = 0.0
            congestion_penalty_min = congestion_penalty_min * 1.5

        effective_queue_wait = queue_wait_min * qw_factor

        total_cost_min = (
            walk_time_min
            + effective_queue_wait
            + congestion_penalty_min
            + show_surge_penalty_min
            + low_confidence_penalty_min
            + safety_penalty_min
        )

        is_critico = worst_status == "critico"

        options.append({
            "cluster_id": cid,
            "nome": cs.nome,
            "walk_time_min": round(walk_time_min, 2),
            "queue_wait_min": round(effective_queue_wait, 2),
            "congestion_penalty_min": round(congestion_penalty_min, 2),
            "show_surge_penalty_min": round(show_surge_penalty_min, 2),
            "low_confidence_penalty_min": round(low_confidence_penalty_min, 2),
            "safety_penalty_min": round(safety_penalty_min, 2),
            "total_cost_min": round(total_cost_min, 2),
            "density_avg_los": DEFAULT_LOS,
            "density_worst_los": DEFAULT_LOS,
            "reason": _reason_for(walk_time_min, effective_queue_wait, avg_occ, total_cost_min, cs.entry_only, preference),
            "avoid": is_critico,
            "simulado": True,
            "_is_critico": is_critico,
            "_total_cost": total_cost_min,
        })

    # Sort: non-critico first, then by total_cost_min ascending
    options.sort(key=lambda x: (x["_is_critico"], x["_total_cost"]))

    # Strip internal keys and return top 3
    def _clean(o: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in o.items() if not k.startswith("_")}

    top3 = [_clean(o) for o in options[:3]]

    return {
        "preference": preference,
        "ts": time.time(),
        "options": top3,
        "simulado": True,
    }
