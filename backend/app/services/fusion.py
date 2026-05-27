"""
Sensor fusion service for PlantaOS × Rock in Rio Lisboa 2026.

Fuses IR, WiFi, and Camera readings into a single occupancy estimate.

Weights:
    IR     = 0.50
    WiFi   = 0.30
    Camera = 0.20

If a source is missing, its weight is redistributed proportionally among
the remaining available sources.

Confidence:
    Starts at 100 %, decremented by:
    - Each missing source: −20 %
    - Camera ML confidence below 1.0 contributes proportionally.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

# Base weights (must sum to 1.0)
_BASE_WEIGHTS: Dict[str, float] = {
    "IR": 0.50,
    "WiFi": 0.30,
    "Camera": 0.20,
}

# Confidence penalty per missing source
_MISSING_SOURCE_PENALTY = 20.0


def fuse(
    ir_occupancy: Optional[float] = None,
    wifi_occupancy: Optional[float] = None,
    camera_occupancy: Optional[float] = None,
    camera_ml_confidence: float = 1.0,
) -> Tuple[float, float, list]:
    """
    Fuse available occupancy readings into a single estimate.

    Parameters
    ----------
    ir_occupancy : float | None
        IR sensor occupancy estimate (0–100 %).  None = source unavailable.
    wifi_occupancy : float | None
        WiFi probe occupancy estimate (0–100 %).  None = source unavailable.
    camera_occupancy : float | None
        Camera ML occupancy estimate (0–100 %).  None = source unavailable.
    camera_ml_confidence : float
        Camera ML model confidence in [0.0, 1.0].  Used to scale camera weight.

    Returns
    -------
    occupancy_pct : float
        Fused occupancy estimate 0–100 %.
    confidence_pct : float
        Fusion confidence 0–100 %.
    active_sources : list[str]
        Names of sources that contributed to the fusion.
    """
    available: Dict[str, float] = {}
    if ir_occupancy is not None:
        available["IR"] = float(ir_occupancy)
    if wifi_occupancy is not None:
        available["WiFi"] = float(wifi_occupancy)
    if camera_occupancy is not None:
        available["Camera"] = float(camera_occupancy)

    if not available:
        return 0.0, 0.0, []

    # Build effective weights only for available sources
    raw_weights: Dict[str, float] = {}
    for source in available:
        w = _BASE_WEIGHTS[source]
        if source == "Camera":
            # Scale camera weight by its ML confidence
            w = w * max(0.0, min(1.0, camera_ml_confidence))
        raw_weights[source] = w

    total_weight = sum(raw_weights.values())
    if total_weight <= 0.0:
        # Fallback: equal weights
        total_weight = len(available)
        raw_weights = {s: 1.0 for s in available}

    # Normalise weights so they sum to 1.0
    norm_weights: Dict[str, float] = {s: w / total_weight for s, w in raw_weights.items()}

    # Weighted average
    occupancy_pct = sum(norm_weights[s] * v for s, v in available.items())
    occupancy_pct = max(0.0, min(100.0, occupancy_pct))

    # Confidence calculation
    missing_count = len(_BASE_WEIGHTS) - len(available)
    confidence_pct = 100.0 - missing_count * _MISSING_SOURCE_PENALTY

    # Additional penalty for low camera ML confidence when camera is available
    if camera_occupancy is not None:
        camera_conf_penalty = (1.0 - camera_ml_confidence) * _BASE_WEIGHTS["Camera"] * 100.0
        confidence_pct -= camera_conf_penalty

    confidence_pct = max(0.0, min(100.0, confidence_pct))

    return occupancy_pct, confidence_pct, sorted(available.keys())


def redistribute_weights(available_sources: list) -> Dict[str, float]:
    """
    Return normalised weights for the given available sources,
    redistributing the weight of missing sources proportionally.

    Parameters
    ----------
    available_sources : list[str]
        Subset of ["IR", "WiFi", "Camera"].

    Returns
    -------
    dict mapping source name -> normalised weight (sum = 1.0).
    """
    if not available_sources:
        return {}
    raw = {s: _BASE_WEIGHTS[s] for s in available_sources if s in _BASE_WEIGHTS}
    total = sum(raw.values())
    if total <= 0:
        n = len(available_sources)
        return {s: 1.0 / n for s in available_sources}
    return {s: w / total for s, w in raw.items()}
