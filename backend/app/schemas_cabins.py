"""
Per-cabin Reed switch schemas for PlantaOS × Rock in Rio Lisboa 2026.

Defines the Pydantic v2 models for cabin-level sub-clustering.
These schemas are intentionally kept in a separate file so that
app/schemas.py is not modified.

Hardware target: MC-38 Reed magnetic contact switches wired to LilyGo
ESP32-C3 boards, one board per WC cluster.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CabinType(str, Enum):
    ACCESSIBLE = "accessible"   # PMR — accessible cabin
    STANDARD   = "standard"     # Standard cabin
    WIDE       = "wide"         # Wide cabin (slightly larger)
    END        = "end"          # End-of-row cabin
    CALHA      = "calha"        # Open urinal trough section (unidade)


# ---------------------------------------------------------------------------
# Individual cabin state
# ---------------------------------------------------------------------------

class CabinState(BaseModel):
    """Live state for a single cabin unit as read from a Reed switch."""

    id: str = Field(
        ...,
        description="Unique cabin identifier — format: <cluster>/<section>/<type>.<n>  "
                    "e.g. 'WC-06/U/STD.3'",
    )
    type: CabinType = Field(..., description="Cabin fixture type")
    section: str = Field(
        ...,
        description="Section letter: 'M' (male), 'F' (female), or 'U' (unisex)",
    )
    occupied: bool = Field(..., description="True while door Reed switch is closed (latch engaged)")
    occupied_since_s: Optional[int] = Field(
        None,
        ge=0,
        description="Seconds since cabin became occupied. None if currently free.",
    )
    last_occupied_s_ago: Optional[int] = Field(
        None,
        ge=0,
        description="Seconds since cabin was last vacated. None if currently occupied.",
    )


# ---------------------------------------------------------------------------
# Anomaly
# ---------------------------------------------------------------------------

class CabinAnomaly(BaseModel):
    """Anomaly raised when a cabin has been occupied for longer than expected."""

    cabin_id: str
    type: str = Field("long_occupation", description="Anomaly type tag")
    duration_s: int = Field(..., ge=0, description="How long the cabin has been occupied (s)")
    message: str = Field(..., description="Human-readable alert message in Portuguese")


# ---------------------------------------------------------------------------
# Summary for a full cluster
# ---------------------------------------------------------------------------

class CabinClusterSummary(BaseModel):
    """Aggregate metrics across all cabins in a cluster."""

    total: int = Field(..., ge=0, description="Total number of cabin positions in this cluster")
    occupied: int = Field(..., ge=0, description="Number of cabins currently occupied")
    free: int = Field(..., ge=0, description="Number of cabins currently free")
    accessible_free: int = Field(
        ..., ge=0,
        description="Number of accessible (PMR) cabins currently free",
    )
    avg_occupation_time_s: Optional[int] = Field(
        None,
        description="Average occupation duration (s) across currently occupied cabins; "
                    "null when no cabins are occupied",
    )
    longest_occupation_s: Optional[int] = Field(
        None,
        description="Longest individual occupation duration (s); null when no cabins are occupied",
    )


# ---------------------------------------------------------------------------
# Full cluster response
# ---------------------------------------------------------------------------

class CabinClusterResponse(BaseModel):
    """
    Response body for GET /api/v1/cabins/{cluster_id}.

    The 'simulado' flag will be set to False once real hardware is deployed.
    """

    cluster_id: str = Field(..., description="Cluster identifier e.g. 'WC-06'")
    ts: int = Field(..., description="Unix timestamp (integer seconds) when snapshot was taken")
    simulado: bool = Field(
        True,
        description="True while Reed hardware is not yet installed — "
                    "values are deterministically simulated",
    )
    cabins: List[CabinState] = Field(default_factory=list)
    anomalies: List[CabinAnomaly] = Field(default_factory=list)
    summary: CabinClusterSummary
