"""
Sensor ingest router — POST /api/v1/sensor

Receives LilyGo IR/WiFi sensor readings, fuses them with existing state,
and updates the in-memory cluster state.
"""
from __future__ import annotations

import time
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.data.clusters import UNISEX_CLUSTER_IDS, MISTO_CLUSTER_IDS
from app.schemas import SectionState, SensorReading
from app.services.fusion import fuse
from app.state import app_state

router = APIRouter(tags=["ingest"])


def _validate_section_for_cluster(cluster_id: str, section: str) -> None:
    """
    Enforce the invariant:
    - UNISEX clusters (WC-05, WC-06): only section "U" is valid.
    - MISTO clusters (all others): only sections "M" and "F" are valid.
    """
    if cluster_id in UNISEX_CLUSTER_IDS and section != "U":
        raise HTTPException(
            status_code=422,
            detail=(
                f"Cluster {cluster_id} é UNISSEX — apenas a secção 'U' é válida. "
                f"Recebido: '{section}'."
            ),
        )
    if cluster_id in MISTO_CLUSTER_IDS and section not in ("M", "F"):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Cluster {cluster_id} é MISTO — secções válidas são 'M' e 'F'. "
                f"Recebido: '{section}'."
            ),
        )


@router.post("/sensor", status_code=200)
async def receive_sensor(reading: SensorReading) -> Dict[str, Any]:
    """
    Ingest a LilyGo IR or WiFi sensor reading.

    The reading is fused with any existing Camera/Prosegur data for the
    same cluster section and the in-memory state is updated immediately.
    """
    _validate_section_for_cluster(reading.cluster_id, reading.section)

    cs = app_state.cluster_states.get(reading.cluster_id)
    if cs is None:
        raise HTTPException(
            status_code=404,
            detail=f"Cluster '{reading.cluster_id}' não encontrado.",
        )

    existing_section: SectionState = cs.secoes.get(reading.section, SectionState())

    # Retrieve existing Prosegur reading for this cluster if available
    prosegur = app_state.prosegur_readings.get(reading.cluster_id)
    camera_occupancy = None
    camera_conf = 1.0
    if prosegur and prosegur.section == reading.section:
        cap = _get_capacity(reading.cluster_id, reading.section)
        camera_occupancy = (prosegur.ocupacao_absoluta / cap * 100.0) if cap > 0 else 0.0
        camera_conf = prosegur.confianca_ml

    # Determine occupancy from reading
    cap = _get_capacity(reading.cluster_id, reading.section)
    if reading.ocupacao_absoluta is not None and cap > 0:
        reading_occ_pct = reading.ocupacao_absoluta / cap * 100.0
    elif cap > 0:
        # Estimate from delta counts applied to existing occupancy
        delta = reading.contagem_entrada - reading.contagem_saida
        current_abs = existing_section.ocupacao_absoluta + delta
        current_abs = max(0, min(cap, current_abs))
        reading_occ_pct = current_abs / cap * 100.0
    else:
        reading_occ_pct = existing_section.ocupacao_pct

    # Fuse: assign to IR or WiFi slot
    ir_occ = reading_occ_pct if reading.source.value == "IR" else None
    wifi_occ = reading_occ_pct if reading.source.value == "WiFi" else None

    # Preserve existing IR/WiFi values from section state (use section confianca as proxy)
    # If we already have a Prosegur reading, include camera
    fused_occ, fused_conf, active_sources = fuse(
        ir_occupancy=ir_occ,
        wifi_occupancy=wifi_occ,
        camera_occupancy=camera_occupancy,
        camera_ml_confidence=camera_conf,
    )

    # Build updated section state
    abs_count = int(round(fused_occ * cap / 100.0)) if cap > 0 else 0
    new_state = existing_section.model_copy(update={
        "ocupacao_pct": round(fused_occ, 1),
        "ocupacao_absoluta": abs_count,
        "confianca_pct": round(fused_conf, 1),
        "fontes_activas": active_sources,
    })

    app_state.update_section(reading.cluster_id, reading.section, new_state)

    # Record timestamp for offline detection, keyed per-section
    ts_key = f"{reading.cluster_id}_{reading.section}"
    app_state.sensor_readings[ts_key] = reading

    return {
        "ok": True,
        "cluster_id": reading.cluster_id,
        "section": reading.section,
        "ocupacao_pct": round(fused_occ, 1),
        "confianca_pct": round(fused_conf, 1),
        "fontes_activas": active_sources,
        "ts": time.time(),
    }


def _get_capacity(cluster_id: str, section: str) -> int:
    from app.data.clusters import get_capacity_for_section
    return get_capacity_for_section(cluster_id, section)
