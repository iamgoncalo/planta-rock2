"""
Cabins router — GET /api/v1/cabins/{cluster_id}

Per-cabin Reed switch sub-clustering endpoint.

Until MC-38 hardware is installed the endpoint returns DETERMINISTICALLY
SIMULATED cabin states seeded by (cluster_id + current UTC hour) so that
repeated calls within the same hour return the same distribution, but the
picture changes every hour in line with simulation occupancy shifts.

Hardware deployment note:
  When LilyGo ESP32-C3 boards are installed each board posts door-state
  bitmasks to POST /api/v1/ingest/cabins (not yet implemented).  The GET
  endpoint will then return real data and flip 'simulado' to False.
"""
from __future__ import annotations

import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException

from app.schemas_cabins import (
    CabinAnomaly,
    CabinClusterResponse,
    CabinClusterSummary,
    CabinState,
    CabinType,
)
from app.state import app_state

router = APIRouter(tags=["cabins"])

# ---------------------------------------------------------------------------
# Cabin layout data
# Sourced from engineering floor plans supplied May 2026.
#
# Format per cluster:
#   {
#     section_key: [(CabinType, count), ...]
#   }
# "calha" entries represent full urinal-trough sections (counted as one unit
# each for Reed-switch purposes — one float switch per calha).
# ---------------------------------------------------------------------------

CABIN_LAYOUT: Dict[str, Dict[str, List[Tuple[CabinType, int]]]] = {
    "WC-01": {
        "M": [
            (CabinType.ACCESSIBLE, 3),
            (CabinType.STANDARD,   8),
            (CabinType.WIDE,       3),
            (CabinType.END,        1),
        ],
        "F": [
            (CabinType.ACCESSIBLE, 2),
            (CabinType.STANDARD,  10),
            (CabinType.WIDE,       3),
            (CabinType.END,        1),
        ],
    },
    "WC-02": {
        "M": [
            (CabinType.ACCESSIBLE, 2),
            (CabinType.STANDARD,   6),
        ],
        "F": [
            (CabinType.ACCESSIBLE, 2),
            (CabinType.STANDARD,  14),
            (CabinType.WIDE,       2),
        ],
    },
    "WC-03": {
        "M": [
            (CabinType.ACCESSIBLE, 2),
            (CabinType.STANDARD,   7),
        ],
        "F": [
            (CabinType.ACCESSIBLE, 2),
            (CabinType.STANDARD,   9),
            (CabinType.END,        1),
        ],
    },
    "WC-04": {
        "M": [
            (CabinType.ACCESSIBLE, 2),
            (CabinType.STANDARD,  12),
            (CabinType.WIDE,       2),
        ],
        "F": [
            (CabinType.ACCESSIBLE, 2),
            (CabinType.STANDARD,  12),
            (CabinType.END,        2),
        ],
    },
    # WC-05 — UNISEX
    "WC-05": {
        "U": [
            (CabinType.ACCESSIBLE, 2),
            (CabinType.STANDARD,  20),
            (CabinType.WIDE,       4),
            (CabinType.END,        1),
        ],
    },
    # WC-06 — UNISEX (largest cluster; also has calha sections)
    "WC-06": {
        "U": [
            (CabinType.ACCESSIBLE, 3),
            (CabinType.STANDARD,  24),
            (CabinType.WIDE,       6),
            (CabinType.END,        1),
            (CabinType.CALHA,      6),
        ],
    },
    "WC-07": {
        "M": [
            (CabinType.ACCESSIBLE,  2),
            (CabinType.STANDARD,   15),  # 4 std_large + 11 std merged to standard
            (CabinType.END,         1),
        ],
        "F": [
            (CabinType.ACCESSIBLE,  2),
            (CabinType.STANDARD,    8),
            (CabinType.WIDE,        4),
        ],
    },
    "WC-08": {
        "M": [
            (CabinType.ACCESSIBLE, 2),
            (CabinType.STANDARD,  12),
            (CabinType.WIDE,       2),
        ],
        "F": [
            (CabinType.ACCESSIBLE, 2),
            (CabinType.STANDARD,   9),
            (CabinType.END,        1),
        ],
    },
}

# Short type abbreviations used in cabin IDs
_TYPE_ABBREV: Dict[CabinType, str] = {
    CabinType.ACCESSIBLE: "ACC",
    CabinType.STANDARD:   "STD",
    CabinType.WIDE:       "WID",
    CabinType.END:        "END",
    CabinType.CALHA:      "CAL",
}

# Long-occupation anomaly threshold (seconds)
ANOMALY_THRESHOLD_S = 600


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_cabin_list(cluster_id: str) -> List[Tuple[str, CabinType, str]]:
    """
    Return a flat list of (cabin_id, cabin_type, section) tuples for a cluster.
    The order is deterministic and matches the floor plan left-to-right layout.
    """
    layout = CABIN_LAYOUT[cluster_id]
    cabins: List[Tuple[str, CabinType, str]] = []

    for section, groups in layout.items():
        counters: Dict[CabinType, int] = {}
        for cabin_type, count in groups:
            base = counters.get(cabin_type, 0)
            for i in range(1, count + 1):
                abbrev = _TYPE_ABBREV[cabin_type]
                cabin_id = f"{cluster_id}/{section}/{abbrev}.{base + i}"
                cabins.append((cabin_id, cabin_type, section))
            counters[cabin_type] = base + count

    return cabins


def _get_section_occupancy_pct(cluster_id: str, section: str) -> float:
    """
    Return the simulated occupancy percentage (0–100) for a cluster section
    as reported by the top-level simulation engine.  Falls back to 50 % if
    the cluster is not yet initialised.
    """
    cs = app_state.cluster_states.get(cluster_id)
    if cs is None:
        return 50.0
    ss = cs.secoes.get(section)
    if ss is None:
        return 50.0
    return float(ss.ocupacao_pct)


def _simulate_cabins(
    cluster_id: str,
    cabin_list: List[Tuple[str, CabinType, str]],
    hour: int,
) -> List[CabinState]:
    """
    Deterministically simulate Reed switch states for all cabins in a cluster.

    Seed = hash(cluster_id + hour-of-day) so the picture is stable within
    a given hour but rotates as the event progresses.
    """
    seed = hash(cluster_id + str(hour)) & 0xFFFF_FFFF
    rng = random.Random(seed)

    results: List[CabinState] = []

    # Track which accessible cabins per section are "reserved" (always free)
    # — one accessible cabin per section is kept free regardless of occupancy.
    reserved_per_section: Dict[str, Optional[str]] = {}
    for (cid, ctype, sec) in cabin_list:
        if ctype == CabinType.ACCESSIBLE and sec not in reserved_per_section:
            reserved_per_section[sec] = cid  # first accessible per section

    for (cid, ctype, section) in cabin_list:
        occ_pct = _get_section_occupancy_pct(cluster_id, section)
        # Calha sections use a slightly lower threshold (people spread out)
        if ctype == CabinType.CALHA:
            threshold = occ_pct * 0.8 / 100.0
        else:
            threshold = occ_pct / 100.0

        # Reserved accessible cabin stays free always
        if reserved_per_section.get(section) == cid:
            results.append(CabinState(
                id=cid,
                type=ctype,
                section=section,
                occupied=False,
                occupied_since_s=None,
                last_occupied_s_ago=rng.randint(0, 120) if occ_pct > 20 else None,
            ))
            continue

        occupied = rng.random() < threshold

        if occupied:
            occupied_since_s = rng.randint(30, 900)  # 30 s – 15 min
            results.append(CabinState(
                id=cid,
                type=ctype,
                section=section,
                occupied=True,
                occupied_since_s=occupied_since_s,
                last_occupied_s_ago=None,
            ))
        else:
            # Some recently vacated cabins carry a last_occupied timestamp
            recently_vacated = rng.random() < 0.35
            last_occ = rng.randint(0, 120) if recently_vacated else None
            results.append(CabinState(
                id=cid,
                type=ctype,
                section=section,
                occupied=False,
                occupied_since_s=None,
                last_occupied_s_ago=last_occ,
            ))

    return results


def _build_anomalies(cabins: List[CabinState]) -> List[CabinAnomaly]:
    """Raise an anomaly for any cabin occupied beyond the threshold."""
    anomalies: List[CabinAnomaly] = []
    for c in cabins:
        if c.occupied and c.occupied_since_s is not None and c.occupied_since_s > ANOMALY_THRESHOLD_S:
            minutes = c.occupied_since_s // 60
            anomalies.append(CabinAnomaly(
                cabin_id=c.id,
                type="long_occupation",
                duration_s=c.occupied_since_s,
                message=f"Cabine ocupada há {minutes}min — verificar",
            ))
    return anomalies


def _build_summary(cabins: List[CabinState]) -> CabinClusterSummary:
    """Compute aggregate metrics from a list of CabinState objects."""
    total     = len(cabins)
    occupied  = sum(1 for c in cabins if c.occupied)
    free      = total - occupied
    acc_free  = sum(
        1 for c in cabins
        if c.type == CabinType.ACCESSIBLE and not c.occupied
    )

    occupied_times = [
        c.occupied_since_s for c in cabins
        if c.occupied and c.occupied_since_s is not None
    ]
    avg_occ = int(sum(occupied_times) / len(occupied_times)) if occupied_times else None
    longest = max(occupied_times) if occupied_times else None

    return CabinClusterSummary(
        total=total,
        occupied=occupied,
        free=free,
        accessible_free=acc_free,
        avg_occupation_time_s=avg_occ,
        longest_occupation_s=longest,
    )


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.get(
    "/cabins/{cluster_id}",
    response_model=CabinClusterResponse,
    summary="Per-cabin Reed switch state for a WC cluster",
    description=(
        "Returns the simulated (or, once hardware is live, real) occupancy state "
        "for every individual cabin in the requested cluster.  "
        "Simulation is seeded by cluster_id + UTC hour so the snapshot is stable "
        "within a given hour.  "
        "Anomalies are raised for cabins occupied longer than 10 minutes."
    ),
)
async def get_cabin_cluster(cluster_id: str) -> CabinClusterResponse:
    """GET /api/v1/cabins/{cluster_id}"""

    if cluster_id not in CABIN_LAYOUT:
        raise HTTPException(
            status_code=404,
            detail=f"Cluster '{cluster_id}' not found. Valid values: {sorted(CABIN_LAYOUT.keys())}",
        )

    now_utc   = datetime.now(tz=timezone.utc)
    ts        = int(time.time())
    hour      = now_utc.hour

    cabin_list = _build_cabin_list(cluster_id)
    cabins     = _simulate_cabins(cluster_id, cabin_list, hour)
    anomalies  = _build_anomalies(cabins)
    summary    = _build_summary(cabins)

    return CabinClusterResponse(
        cluster_id=cluster_id,
        ts=ts,
        simulado=True,
        cabins=cabins,
        anomalies=anomalies,
        summary=summary,
    )
