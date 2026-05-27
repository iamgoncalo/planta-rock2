"""
Crowd-density grid service for PlantaOS × Rock in Rio Lisboa 2026.

Computes a configurable-resolution spatial grid over the Parque Tejo venue
and fills each cell with an estimated crowd density (persons / m²) derived
from:

  1. Gaussian spread of occupants from each of the 8 WC clusters
     (people congregate around WC areas; σ = 30 m)
  2. Baseline festival crowd uniformly distributed over the venue
     (80 % of festival_pax over the full footprint)

Fruin Level of Service thresholds are then applied to classify each cell.

WiFi-to-people conversion:
    estimated_people = wifi_macs_distinct × 2.5
    (≈40 % of attendees emit WiFi probes per minute)

Privacy note: NO individual location data is used; only aggregate WC
occupancy counts from app_state are consumed.

Grid geometry (at default 10 m cell size):
    Venue:  530 m (E-W) × 380 m (N-S) = 201 400 m²
    SW origin: lat=38.7783, lon=-9.0987   (Parque Tejo, approximate)
    Cols: ceil(530 / 10) = 53
    Rows: ceil(380 / 10) = 38
    Cells: 53 × 38 = 2 014
"""
from __future__ import annotations

import math
import time
from typing import Dict, List, Optional, Tuple

from app.schemas_density import DensityCell, DensityGridResponse, DensityTrend, FruinLevel

# ---------------------------------------------------------------------------
# Venue constants
# ---------------------------------------------------------------------------

VENUE_SW_LAT: float = 38.7783   # SW corner latitude
VENUE_SW_LON: float = -9.0987   # SW corner longitude
VENUE_WIDTH_M: float = 530.0    # east-west extent in metres
VENUE_HEIGHT_M: float = 380.0   # north-south extent in metres

# Approximate metres per degree at this latitude (Parque Tejo, ~38.78 °N)
M_PER_DEG_LAT: float = 111_320.0
M_PER_DEG_LON: float = 111_320.0 * math.cos(math.radians(38.78))

# Gaussian spread sigma (people spread within σ m of a WC cluster)
GAUSSIAN_SIGMA_M: float = 30.0

# WC cluster positions (lat, lon) — from static cluster metadata
WC_POSITIONS: Dict[str, Tuple[float, float]] = {
    "WC-01": (38.78230, -9.09371),
    "WC-02": (38.78193, -9.09323),
    "WC-03": (38.78111, -9.09310),
    "WC-04": (38.78195, -9.09275),
    "WC-05": (38.78150, -9.09303),
    "WC-06": (38.78010, -9.09549),
    "WC-07": (38.78069, -9.09356),
    "WC-08": (38.77936, -9.09619),
}

# Fruin LoS density boundaries (persons / m²)
_FRUIN_BOUNDS: List[Tuple[float, FruinLevel]] = [
    (0.27,  FruinLevel.A),
    (0.43,  FruinLevel.B),
    (0.65,  FruinLevel.C),
    (1.08,  FruinLevel.D),
    (2.17,  FruinLevel.E),
    (math.inf, FruinLevel.F),
]

# Previous grid snapshot keyed by cell_m for trend computation
_prev_density: Dict[int, Dict[Tuple[int, int], float]] = {}

# Gaussian cut-off: skip cells beyond 3σ (negligible contribution)
_CUTOFF_SIGMA: float = 3.0


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def gaussian_weight(distance_m: float, sigma_m: float = GAUSSIAN_SIGMA_M) -> float:
    """Return Gaussian weight for a given distance and spread sigma."""
    return math.exp(-(distance_m ** 2) / (2.0 * sigma_m ** 2))


def _fruin_level(density: float) -> FruinLevel:
    """Classify a density (persons / m²) into a Fruin LoS level."""
    for threshold, level in _FRUIN_BOUNDS:
        if density < threshold:
            return level
    return FruinLevel.F


def _cell_to_latlon(
    col: int,
    row: int,
    cell_m: int,
) -> Tuple[float, float]:
    """Return the (lat, lon) of a cell centre given its (col, row) index."""
    x_m = (col + 0.5) * cell_m   # metres east of SW corner
    y_m = (row + 0.5) * cell_m   # metres north of SW corner
    lat = VENUE_SW_LAT + y_m / M_PER_DEG_LAT
    lon = VENUE_SW_LON + x_m / M_PER_DEG_LON
    return lat, lon


def _latlon_to_cell(
    lat: float,
    lon: float,
    cell_m: int,
    grid_cols: int,
    grid_rows: int,
) -> Tuple[int, int]:
    """Convert a (lat, lon) position to the nearest (col, row) cell index."""
    x_m = (lon - VENUE_SW_LON) * M_PER_DEG_LON
    y_m = (lat - VENUE_SW_LAT) * M_PER_DEG_LAT
    col = int(x_m / cell_m)
    row = int(y_m / cell_m)
    col = max(0, min(grid_cols - 1, col))
    row = max(0, min(grid_rows - 1, row))
    return col, row


def _distance_m(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Euclidean distance in metres between two (lat, lon) points."""
    dx = (lon2 - lon1) * M_PER_DEG_LON
    dy = (lat2 - lat1) * M_PER_DEG_LAT
    return math.sqrt(dx * dx + dy * dy)


def _cluster_total_people(cluster_state) -> float:
    """
    Return the estimated total number of people at a cluster
    (occupied inside + queue outside).
    """
    total = 0.0
    for ss in cluster_state.secoes.values():
        total += ss.ocupacao_absoluta + ss.fila_actual
    return total


# ---------------------------------------------------------------------------
# Main grid computation
# ---------------------------------------------------------------------------

def generate_density_grid(
    cluster_states: dict,
    cell_m: int = 10,
    festival_pax: int = 80_000,
) -> DensityGridResponse:
    """
    Build a crowd-density grid over the Parque Tejo venue.

    Parameters
    ----------
    cluster_states : dict[str, ClusterState]
        Current WC cluster states from app_state.
    cell_m : int
        Cell edge length in metres.  Allowed: 5, 10, 25, 50.
    festival_pax : int
        Estimated total festival attendance for baseline crowd calculation.

    Returns
    -------
    DensityGridResponse
    """
    ts_now = time.time()
    cell_area = float(cell_m * cell_m)

    grid_cols = math.ceil(VENUE_WIDTH_M / cell_m)
    grid_rows = math.ceil(VENUE_HEIGHT_M / cell_m)

    # 2-D accumulator: people count per cell
    grid: List[List[float]] = [
        [0.0] * grid_cols for _ in range(grid_rows)
    ]

    # ------------------------------------------------------------------
    # 1. Baseline crowd: 80 % of festival_pax uniformly over all cells
    # ------------------------------------------------------------------
    total_cells = grid_cols * grid_rows
    baseline_people_per_cell = (festival_pax * 0.8) / total_cells
    for row in range(grid_rows):
        for col in range(grid_cols):
            grid[row][col] += baseline_people_per_cell

    # ------------------------------------------------------------------
    # 2. Gaussian spread from each WC cluster
    # ------------------------------------------------------------------
    cutoff_m = _CUTOFF_SIGMA * GAUSSIAN_SIGMA_M  # only process cells within 3σ

    for cluster_id, cs in cluster_states.items():
        wc_lat, wc_lon = WC_POSITIONS.get(cluster_id, (cs.lat, cs.lon))

        people_at_cluster = _cluster_total_people(cs)
        if people_at_cluster <= 0:
            continue

        # Determine which cells are within the cutoff range
        center_col, center_row = _latlon_to_cell(wc_lat, wc_lon, cell_m, grid_cols, grid_rows)
        delta_cells = int(math.ceil(cutoff_m / cell_m)) + 1

        col_lo = max(0, center_col - delta_cells)
        col_hi = min(grid_cols - 1, center_col + delta_cells)
        row_lo = max(0, center_row - delta_cells)
        row_hi = min(grid_rows - 1, center_row + delta_cells)

        # Compute raw weights for the window
        weights: List[List[float]] = []
        weight_sum = 0.0
        for row in range(row_lo, row_hi + 1):
            row_weights = []
            for col in range(col_lo, col_hi + 1):
                cell_lat, cell_lon = _cell_to_latlon(col, row, cell_m)
                dist = _distance_m(wc_lat, wc_lon, cell_lat, cell_lon)
                if dist > cutoff_m:
                    w = 0.0
                else:
                    w = gaussian_weight(dist)
                row_weights.append(w)
                weight_sum += w
            weights.append(row_weights)

        if weight_sum <= 0:
            # Fallback: dump all people into the centre cell
            grid[center_row][center_col] += people_at_cluster
            continue

        # Distribute people proportionally to weights
        for ri, row in enumerate(range(row_lo, row_hi + 1)):
            for ci, col in enumerate(range(col_lo, col_hi + 1)):
                fraction = weights[ri][ci] / weight_sum
                grid[row][col] += people_at_cluster * fraction

    # ------------------------------------------------------------------
    # 3. Retrieve previous snapshot for trend computation
    # ------------------------------------------------------------------
    prev: Dict[Tuple[int, int], float] = _prev_density.get(cell_m, {})
    new_prev: Dict[Tuple[int, int], float] = {}

    # ------------------------------------------------------------------
    # 4. Build DensityCell list
    # ------------------------------------------------------------------
    TREND_THRESHOLD = 0.05  # persons/m² change to qualify as growing/declining

    cells: List[DensityCell] = []
    total_people = 0.0

    for row in range(grid_rows):
        for col in range(grid_cols):
            ppl = grid[row][col]
            density = ppl / cell_area
            level = _fruin_level(density)
            is_alert = level in (FruinLevel.E, FruinLevel.F)

            # Trend
            prev_density = prev.get((col, row), 0.0)
            delta = density - prev_density
            if delta > TREND_THRESHOLD:
                trend = DensityTrend.GROWING
            elif delta < -TREND_THRESHOLD:
                trend = DensityTrend.DECLINING
            else:
                trend = DensityTrend.STABLE

            new_prev[(col, row)] = density
            total_people += ppl

            if ppl > 0:
                cell_lat, cell_lon = _cell_to_latlon(col, row, cell_m)
                cells.append(
                    DensityCell(
                        ts=ts_now,
                        cell_x=col,
                        cell_y=row,
                        center_lat=round(cell_lat, 6),
                        center_lon=round(cell_lon, 6),
                        wifi_macs_distinct=max(0, int(ppl / 2.5)),
                        estimated_people=round(ppl, 2),
                        density_pm2=round(density, 4),
                        trend=trend,
                        level=level,
                        alert=is_alert,
                    )
                )

    # ------------------------------------------------------------------
    # 5. Sparse representation: drop zero-density cells at fine resolution
    # ------------------------------------------------------------------
    if len(cells) > 500:
        cells = [c for c in cells if c.estimated_people > 0]

    # ------------------------------------------------------------------
    # 6. Hotspots: level E or F
    # ------------------------------------------------------------------
    hotspots = [c for c in cells if c.level in (FruinLevel.E, FruinLevel.F)]

    # ------------------------------------------------------------------
    # 7. Update cache for next tick's trend computation
    # ------------------------------------------------------------------
    _prev_density[cell_m] = new_prev

    return DensityGridResponse(
        ts=ts_now,
        cell_m=cell_m,
        grid_cols=grid_cols,
        grid_rows=grid_rows,
        total_estimated_people=round(total_people, 1),
        cells=cells,
        hotspots=hotspots,
    )
