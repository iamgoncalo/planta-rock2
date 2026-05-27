"""
KPIs router — GET /api/v1/kpis

Returns the four global Key Performance Indicators with festival context.
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from app.services.kpis import calculate_all_kpis
from app.state import app_state

router = APIRouter(tags=["kpis"])


@router.get("/kpis")
async def get_kpis() -> Dict[str, Any]:
    """Return all four global KPIs."""
    kpis = calculate_all_kpis(
        cluster_states=app_state.cluster_states,
        alerts=app_state.alerts,
        daily_redirected=app_state.daily_redirected,
    )
    return kpis.model_dump()
