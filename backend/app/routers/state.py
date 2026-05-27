"""
Festival state router — GET /api/v1/state

Returns a consolidated snapshot of the full festival state including
clusters, KPIs, alerts, current show, and next headliner.
"""
from __future__ import annotations

import datetime
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter

from app.data.shows import FESTIVAL_DAY_BY_DATE, SHOWS
from app.routers.clusters import _serialise_cluster
from app.services.alerts import evaluate_all_clusters
from app.services.kpis import calculate_all_kpis
from app.state import app_state

router = APIRouter(tags=["state"])

FESTIVAL_DAYS_MAP = {
    "2026-06-20": 1,
    "2026-06-21": 2,
    "2026-06-27": 3,
    "2026-06-28": 4,
}


def _hhmm_to_minutes(hhmm: str) -> int:
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m


def _get_festival_day(now: datetime.datetime) -> Optional[int]:
    date_str = now.strftime("%Y-%m-%d")
    return FESTIVAL_DAYS_MAP.get(date_str)


def _get_current_show(now: datetime.datetime) -> Optional[Dict[str, Any]]:
    date_str = now.strftime("%Y-%m-%d")
    now_mins = now.hour * 60 + now.minute
    for show in SHOWS:
        if show["data"] != date_str:
            continue
        ini = _hhmm_to_minutes(show["inicio"])
        fim = _hhmm_to_minutes(show["fim"])
        if fim == 0:
            fim = 24 * 60
        if ini <= now_mins < fim:
            return {
                "artista": show["artista"],
                "palco": show["palco_nome"],
                "inicio": show["inicio"],
                "fim": show["fim"],
            }
    return None


def _get_next_headliner(now: datetime.datetime) -> Optional[Dict[str, Any]]:
    date_str = now.strftime("%Y-%m-%d")
    now_mins = now.hour * 60 + now.minute
    best: Optional[Dict[str, Any]] = None
    best_mins: Optional[int] = None
    for show in SHOWS:
        if not show["headliner"]:
            continue
        if show["data"] != date_str:
            continue
        ini = _hhmm_to_minutes(show["inicio"])
        if ini > now_mins:
            if best_mins is None or ini < best_mins:
                best_mins = ini
                best = show
    if best is None:
        return None
    return {
        "artista": best["artista"],
        "palco": best["palco_nome"],
        "inicio": best["inicio"],
        "mins_until": float(best_mins - now_mins),  # type: ignore[operator]
    }


@router.get("/state")
async def get_state() -> Dict[str, Any]:
    """Return consolidated festival state snapshot."""
    now = datetime.datetime.now()

    festival_day = _get_festival_day(now)
    current_show = _get_current_show(now)
    next_headliner = _get_next_headliner(now)

    clusters_out: List[Dict[str, Any]] = []
    for cid in sorted(app_state.cluster_states.keys()):
        cs = app_state.cluster_states[cid]
        clusters_out.append(_serialise_cluster(cs))

    kpis = calculate_all_kpis(
        cluster_states=app_state.cluster_states,
        alerts=app_state.alerts,
        daily_redirected=app_state.daily_redirected,
        now=now,
    )

    alerts_out = []
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
        "simulado": True,
        "festival_day": festival_day,
        "current_show": current_show,
        "next_headliner": next_headliner,
        "clusters": clusters_out,
        "kpis": kpis.model_dump(),
        "alerts": alerts_out,
        "any_simulated": True,
    }
