"""
Crowd routing recommendation service for PlantaOS × Rock in Rio Lisboa 2026.

Given a cluster under pressure, find the best available alternative cluster.

Rules:
- Avoid CRITICO clusters (ocupacao_pct > 90 %).
- Prefer lower occupancy.
- Prefer shorter queue.
- Prefer closer physical distance to the festival entrance.
- WC-05 (entry_only=True) MUST NOT be recommended as a relief destination.
- The source cluster itself is excluded from candidates.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from app.data.clusters import CLUSTERS_BY_ID, ENTRY_ONLY_CLUSTER_IDS
from app.schemas import ClusterState, RoutingRecommendation

_CRITICO_THRESHOLD = 90.0


def _section_avg_occupancy(cs: ClusterState) -> float:
    """Return average occupancy % across all sections of a cluster."""
    if not cs.secoes:
        return 0.0
    vals = [ss.ocupacao_pct for ss in cs.secoes.values()]
    return sum(vals) / len(vals)


def _section_total_queue(cs: ClusterState) -> int:
    """Return total queue across all sections of a cluster."""
    return sum(ss.fila_actual for ss in cs.secoes.values())


def recommend_routing(
    from_cluster_id: str,
    all_states: Dict[str, ClusterState],
) -> Optional[RoutingRecommendation]:
    """
    Given a cluster under pressure, recommend the best alternative cluster.

    Parameters
    ----------
    from_cluster_id : str
        The cluster that is currently under pressure (e.g. "WC-01").
    all_states : dict[str, ClusterState]
        Full runtime state for all clusters.

    Returns
    -------
    RoutingRecommendation | None
        Best routing suggestion, or None if no suitable alternative exists.
    """
    source = all_states.get(from_cluster_id)
    if source is None:
        return None

    source_meta = CLUSTERS_BY_ID.get(from_cluster_id, {})

    candidates = []
    for cid, cs in all_states.items():
        if cid == from_cluster_id:
            continue
        # Do not recommend entry-only clusters as relief destinations
        if cid in ENTRY_ONLY_CLUSTER_IDS:
            continue
        # Do not recommend CRITICO clusters
        avg_occ = _section_avg_occupancy(cs)
        if avg_occ > _CRITICO_THRESHOLD:
            continue
        candidates.append((cid, cs, avg_occ))

    if not candidates:
        return None

    # Score each candidate: lower is better
    # Score = 0.5 × avg_occupancy_pct
    #       + 0.3 × (total_queue / 50) × 100  (normalised to 0–100)
    #       + 0.2 × (dist_entrada_m / 500) × 100  (normalised to 0–100)
    def score(cid: str, cs: ClusterState, avg_occ: float) -> float:
        meta = CLUSTERS_BY_ID.get(cid, {})
        dist = meta.get("dist_entrada_m", 500)
        queue = _section_total_queue(cs)
        occ_score = avg_occ
        queue_score = min(100.0, (queue / 50.0) * 100.0)
        dist_score = min(100.0, (dist / 500.0) * 100.0)
        return 0.5 * occ_score + 0.3 * queue_score + 0.2 * dist_score

    candidates.sort(key=lambda t: score(t[0], t[1], t[2]))
    best_id, best_cs, best_occ = candidates[0]
    best_meta = CLUSTERS_BY_ID.get(best_id, {})

    reason_parts = [
        f"ocupação média {best_occ:.0f}%",
        f"fila total {_section_total_queue(best_cs)} pessoas",
        f"a {best_meta.get('dist_entrada_m', '?')}m da entrada",
    ]
    reason = f"Melhor alternativa disponível: {', '.join(reason_parts)}."

    return RoutingRecommendation(
        from_cluster_id=from_cluster_id,
        recommended_cluster_id=best_id,
        reason=reason,
        distance_m=best_meta.get("dist_entrada_m", 0),
        ocupacao_destino_pct=round(best_occ, 1),
    )


def get_routing_recommendations(
    all_states: Dict[str, ClusterState],
    pressure_threshold: float = 75.0,
) -> List[RoutingRecommendation]:
    """
    Generate routing recommendations for all clusters currently under pressure.

    Parameters
    ----------
    all_states : dict[str, ClusterState]
        Full runtime state for all clusters.
    pressure_threshold : float
        Occupancy % above which a cluster is considered under pressure.

    Returns
    -------
    list[RoutingRecommendation]
    """
    recommendations = []
    for cid, cs in all_states.items():
        avg_occ = _section_avg_occupancy(cs)
        if avg_occ > pressure_threshold:
            rec = recommend_routing(cid, all_states)
            if rec is not None:
                recommendations.append(rec)
    return recommendations
