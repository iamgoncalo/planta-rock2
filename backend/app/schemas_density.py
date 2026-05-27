"""
Pydantic v2 schemas for the 10m × 10m crowd-density grid.

Crowd density is computed from WiFi MAC sightings using the Fruin Level of
Service model — no individual tracking, only aggregate spatial statistics.

Fruin LoS thresholds (persons / m²):
  A  free        < 0.27
  B  impeded     0.27 – 0.43
  C  constrained 0.43 – 0.65
  D  congested   0.65 – 1.08   ← operational watch
  E  dense       1.08 – 2.17   ← operational alert
  F  jammed      > 2.17        ← CRITICAL, stampede risk
"""
from __future__ import annotations

import time
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class FruinLevel(str, Enum):
    A = "A"   # free         < 0.27 p/m²
    B = "B"   # impeded      0.27–0.43
    C = "C"   # constrained  0.43–0.65
    D = "D"   # congested    0.65–1.08  — operational watch
    E = "E"   # dense        1.08–2.17  — operational alert
    F = "F"   # jammed       > 2.17     — CRITICAL / stampede risk


class DensityTrend(str, Enum):
    GROWING   = "growing"
    STABLE    = "stable"
    DECLINING = "declining"


# ---------------------------------------------------------------------------
# Individual grid cell
# ---------------------------------------------------------------------------

class DensityCell(BaseModel):
    """State of one 10m × 10m (configurable) grid cell."""

    ts: float = Field(default_factory=time.time,
                      description="Unix timestamp when this cell was computed")
    cell_x: int = Field(..., ge=0, description="Column index (0-based, west → east)")
    cell_y: int = Field(..., ge=0, description="Row index (0-based, south → north)")
    center_lat: float = Field(..., description="Latitude of cell centre")
    center_lon: float = Field(..., description="Longitude of cell centre")
    wifi_macs_distinct: int = Field(
        0, ge=0,
        description="Distinct WiFi MAC addresses observed in this cell this minute",
    )
    estimated_people: float = Field(
        0.0, ge=0.0,
        description="Estimated people count (wifi_macs_distinct × 2.5 + spread contributions)",
    )
    density_pm2: float = Field(
        0.0, ge=0.0,
        description="Crowd density in persons / m²",
    )
    trend: DensityTrend = Field(
        DensityTrend.STABLE,
        description="Density trend compared to previous tick",
    )
    level: FruinLevel = Field(
        FruinLevel.A,
        description="Fruin Level of Service classification",
    )
    alert: bool = Field(
        False,
        description="True when level is E (dense) or F (jammed)",
    )


# ---------------------------------------------------------------------------
# Full grid response
# ---------------------------------------------------------------------------

class DensityGridResponse(BaseModel):
    """
    Complete density grid snapshot for one moment in time.

    The 'cells' list uses a sparse representation: cells with
    estimated_people == 0 are omitted when the total cell count would
    exceed 500.  At 10m resolution the full grid has 2 014 cells;
    at 25m resolution it has 315 cells (always returned in full).
    """

    ts: float = Field(default_factory=time.time,
                      description="Unix timestamp of this snapshot")
    cell_m: int = Field(
        10,
        description="Cell edge length in metres (5 / 10 / 25 / 50)",
    )
    grid_cols: int = Field(..., ge=1, description="Number of columns (west–east)")
    grid_rows: int = Field(..., ge=1, description="Number of rows (south–north)")
    total_estimated_people: float = Field(
        0.0, ge=0.0,
        description="Sum of estimated_people across all cells",
    )
    cells: List[DensityCell] = Field(
        default_factory=list,
        description="Populated (non-zero) grid cells — sparse at 10m resolution",
    )
    hotspots: List[DensityCell] = Field(
        default_factory=list,
        description="Subset of cells where level is E (dense) or F (jammed)",
    )
