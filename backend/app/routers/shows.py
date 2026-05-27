"""
Shows router — GET /api/v1/shows

Returns the full 4-day festival programme with current/next show flags.
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Query

from app.data.shows import FESTIVAL_DAY_BY_DATE, SHOWS

router = APIRouter(tags=["shows"])


def _is_active(show: Dict[str, Any], now: datetime.datetime) -> bool:
    """True if the show is currently on stage."""
    if show["data"] != now.strftime("%Y-%m-%d"):
        return False
    h_now = now.hour * 60 + now.minute
    h_ini = _hhmm_to_minutes(show["inicio"])
    h_fim = _hhmm_to_minutes(show["fim"])
    if h_fim == 0:  # midnight
        h_fim = 24 * 60
    return h_ini <= h_now < h_fim


def _hhmm_to_minutes(hhmm: str) -> int:
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m


def _find_next_show(shows: List[Dict[str, Any]], now: datetime.datetime) -> int:
    """Return index of the next upcoming show today, or -1."""
    date_str = now.strftime("%Y-%m-%d")
    h_now = now.hour * 60 + now.minute
    best_idx = -1
    best_start = 99999
    for i, s in enumerate(shows):
        if s["data"] != date_str:
            continue
        h_ini = _hhmm_to_minutes(s["inicio"])
        if h_ini > h_now and h_ini < best_start:
            best_start = h_ini
            best_idx = i
    return best_idx


@router.get("/shows")
async def get_shows(
    dia: int = Query(None, description="Filter by festival day (1–4)"),
    headliners_only: bool = Query(False, description="Return only headliners"),
) -> Dict[str, Any]:
    """
    Return the full show programme with current/next flags.

    Optional filters:
    - dia=1..4  : filter by festival day
    - headliners_only=true : return only headliner acts
    """
    now = datetime.datetime.now()

    shows = SHOWS
    if dia is not None:
        shows = [s for s in shows if s["dia"] == dia]
    if headliners_only:
        shows = [s for s in shows if s["headliner"]]

    next_idx = _find_next_show(shows, now)

    output: List[Dict[str, Any]] = []
    for i, s in enumerate(shows):
        entry = {**s}
        entry["activo"] = _is_active(s, now)
        entry["proximo"] = (i == next_idx)
        output.append(entry)

    # Festival context
    date_str = now.strftime("%Y-%m-%d")
    festival_day = FESTIVAL_DAY_BY_DATE.get(date_str)
    show_activo = next((s["artista"] for s in output if s["activo"]), None)

    return {
        "festival_day": festival_day,
        "show_activo": show_activo,
        "total": len(output),
        "shows": output,
    }
