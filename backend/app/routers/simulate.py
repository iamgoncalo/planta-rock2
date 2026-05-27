"""
Simulation router — POST /api/v1/simulate/tick

Advances the simulation by one tick and broadcasts the updated state
to all connected WebSocket clients.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException

from app.schemas import SimulateTickRequest, SimulateTickResponse
from app.services.alerts import evaluate_all_clusters
from app.services.routing import get_routing_recommendations
from app.services.simulation import VALID_SCENARIOS, run_tick
from app.state import app_state

router = APIRouter(tags=["simulation"])

# Monotonically increasing tick counter
_tick_counter: int = 0


@router.post("/simulate/tick", response_model=SimulateTickResponse)
async def simulate_tick(
    req: Optional[SimulateTickRequest] = None,
) -> SimulateTickResponse:
    """
    Advance the simulation by one tick.

    Optional body:
    - scenario: override the active scenario for this tick
    - hora_simulada: force a specific hour "HH:MM"
    """
    global _tick_counter

    if req is None:
        req = SimulateTickRequest()

    # Resolve scenario
    scenario = req.scenario or app_state.simulation_scenario
    if scenario not in VALID_SCENARIOS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Cenário '{scenario}' desconhecido. "
                f"Válidos: {VALID_SCENARIOS}"
            ),
        )

    _tick_counter += 1

    updated_states, clusters_updated = run_tick(
        cluster_states=app_state.cluster_states,
        scenario_name=scenario,
        tick=_tick_counter,
        hora_simulada=req.hora_simulada,
    )

    app_state.cluster_states = updated_states
    app_state.simulation_scenario = scenario
    app_state.last_tick = time.time()

    # Recompute alerts after state update
    sensor_ts: Dict[str, float] = {}
    for cid, sr in app_state.sensor_readings.items():
        # We store per-cluster, not per-section — use cluster-level ts
        for section in app_state.cluster_states.get(cid, {}).secoes if hasattr(app_state.cluster_states.get(cid), 'secoes') else []:
            sensor_ts[f"{cid}_{section}"] = sr.ts

    new_alerts = evaluate_all_clusters(
        cluster_states=app_state.cluster_states,
        sensor_timestamps=sensor_ts,
    )
    app_state.alerts = new_alerts

    # Attach per-cluster alerts to cluster state
    from collections import defaultdict
    alerts_by_cluster: Dict[str, list] = defaultdict(list)
    for a in new_alerts:
        alerts_by_cluster[a.cluster_id].append(a)
    for cid, cs in app_state.cluster_states.items():
        cs.alertas = alerts_by_cluster.get(cid, [])

    # Update KPI-04: increment redirected count for each CRITICO alert
    from app.schemas import AlertSeveridade
    critico_count = sum(1 for a in new_alerts if a.severidade == AlertSeveridade.CRITICO)
    # Rough estimate: each CRITICO cluster diverts ~5 people/tick
    app_state.daily_redirected += critico_count * 5

    alerts_generated = len(new_alerts)

    return SimulateTickResponse(
        ts=app_state.last_tick,
        scenario=scenario,
        clusters_updated=clusters_updated,
        alerts_generated=alerts_generated,
    )
