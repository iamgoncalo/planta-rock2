"""
Density grid router — GET /api/v1/density-grid

Returns the current 10m × 10m crowd-density grid for Parque Tejo.

Query parameters
----------------
cell_m : int  (default 10; allowed: 5, 10, 25, 50)
    Cell edge length in metres.  Smaller = higher resolution, more cells.

Response shape: DensityGridResponse (see app/schemas_density.py)

Alert conditions
----------------
  LoS E (dense,  density ≥ 1.08 p/m²) → operational alert logged
  LoS F (jammed, density > 2.17 p/m²) → CRITICAL — stampede risk

Privacy note
------------
No individual tracking.  Only aggregate WC-cluster occupancy counts
(from app_state) are used as inputs; WiFi MAC counts are back-calculated
from estimated_people for informational display only.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from app.schemas_density import DensityGridResponse, FruinLevel
from app.services.density import generate_density_grid
from app.state import app_state

logger = logging.getLogger(__name__)

router = APIRouter(tags=["density"])

# Allowed cell resolutions
_ALLOWED_CELL_M = {5, 10, 25, 50}

# Festival baseline attendance (realistic peak for RiR Lisboa)
_FESTIVAL_PAX = 80_000


@router.get(
    "/density-grid",
    response_model=DensityGridResponse,
    summary="10m × 10m crowd-density grid (Fruin LoS)",
    description=(
        "Returns a spatial crowd-density grid for the Parque Tejo venue. "
        "Each cell carries an estimated people count, density in persons/m², "
        "a Fruin Level of Service (A–F) classification, and a density trend. "
        "Hotspots (LoS E and F) are surfaced separately for rapid triage."
    ),
)
async def get_density_grid(
    cell_m: int = Query(
        default=10,
        description="Cell edge length in metres. Allowed: 5, 10, 25, 50.",
        ge=1,
        le=100,
    ),
) -> DensityGridResponse:
    """Compute and return the current crowd-density grid."""
    if cell_m not in _ALLOWED_CELL_M:
        raise HTTPException(
            status_code=422,
            detail=f"cell_m must be one of {sorted(_ALLOWED_CELL_M)}, got {cell_m}.",
        )

    if not app_state._initialised:
        raise HTTPException(
            status_code=503,
            detail="App state not yet initialised. Retry in a moment.",
        )

    grid = generate_density_grid(
        cluster_states=app_state.cluster_states,
        cell_m=cell_m,
        festival_pax=_FESTIVAL_PAX,
    )

    # Log operational alerts
    if grid.hotspots:
        critical = [c for c in grid.hotspots if c.level == FruinLevel.F]
        alert    = [c for c in grid.hotspots if c.level == FruinLevel.E]
        if critical:
            logger.error(
                "CRITICAL density grid: %d cells at LoS F (jammed, > 2.17 p/m²) — stampede risk!",
                len(critical),
            )
        if alert:
            logger.warning(
                "Operational alert: %d cells at LoS E (dense, ≥ 1.08 p/m²).",
                len(alert),
            )

    return grid
