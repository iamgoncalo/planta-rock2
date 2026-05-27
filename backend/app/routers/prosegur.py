"""
Prosegur camera ingest router — POST /api/v1/prosegur

Receives Prosegur camera ML readings, fuses them with existing IR/WiFi
sensor data, and updates the in-memory cluster state.
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.data.clusters import UNISEX_CLUSTER_IDS, MISTO_CLUSTER_IDS
from app.schemas import ProsegurReading, SectionState
from app.services.fusion import fuse
from app.state import app_state

router = APIRouter(tags=["prosegur"])

FORBIDDEN_FIELDS = {
    "co2", "temperature", "temperatura", "humidity", "humidade",
    "temp", "hum", "deucalion", "mac", "raw_mac", "face_vector",
    "person_id", "lat", "lon", "gps",
}


def _validate_section_for_cluster(cluster_id: str, section: str) -> None:
    """Enforce WC-05/06 = U only; all others = M or F only."""
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


@router.post("/prosegur", status_code=200)
async def receive_prosegur(request: Request) -> Dict[str, Any]:
    """
    Ingest a Prosegur camera ML occupancy reading.

    Fuses with existing IR/WiFi data for the same section and
    updates in-memory state immediately.
    """
    # Read raw body first so we can check for forbidden fields before parsing
    raw = await request.body()
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid JSON body")

    body_keys = {k.lower() for k in payload.keys()}
    forbidden_found: List[str] = sorted(body_keys & FORBIDDEN_FIELDS)
    if forbidden_found:
        return JSONResponse(
            status_code=400,
            content={"error": "Forbidden field in payload", "forbidden_fields": forbidden_found},
        )

    # Now parse with Pydantic
    try:
        reading = ProsegurReading.model_validate(payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    _validate_section_for_cluster(reading.cluster_id, reading.section)

    cs = app_state.cluster_states.get(reading.cluster_id)
    if cs is None:
        raise HTTPException(
            status_code=404,
            detail=f"Cluster '{reading.cluster_id}' não encontrado.",
        )

    existing_section: SectionState = cs.secoes.get(reading.section, SectionState())

    # Store the Prosegur reading for fusion by the sensor router
    app_state.prosegur_readings[reading.cluster_id] = reading

    # Compute camera occupancy percentage
    cap = _get_capacity(reading.cluster_id, reading.section)
    camera_occupancy = (reading.ocupacao_absoluta / cap * 100.0) if cap > 0 else 0.0

    # We only have the camera source here — fuse with camera weight only
    fused_occ, fused_conf, active_sources = fuse(
        ir_occupancy=None,
        wifi_occupancy=None,
        camera_occupancy=camera_occupancy,
        camera_ml_confidence=reading.confianca_ml,
    )

    abs_count = int(round(fused_occ * cap / 100.0)) if cap > 0 else reading.ocupacao_absoluta

    new_state = existing_section.model_copy(update={
        "ocupacao_pct": round(fused_occ, 1),
        "ocupacao_absoluta": abs_count,
        "fila_actual": reading.fila_actual,
        "confianca_pct": round(fused_conf, 1),
        "fontes_activas": active_sources,
    })

    app_state.update_section(reading.cluster_id, reading.section, new_state)

    return {
        "ok": True,
        "cluster_id": reading.cluster_id,
        "section": reading.section,
        "ocupacao_pct": round(fused_occ, 1),
        "confianca_pct": round(fused_conf, 1),
        "fontes_activas": active_sources,
        "fila_actual": reading.fila_actual,
        "ts": time.time(),
    }


def _get_capacity(cluster_id: str, section: str) -> int:
    from app.data.clusters import get_capacity_for_section
    return get_capacity_for_section(cluster_id, section)
