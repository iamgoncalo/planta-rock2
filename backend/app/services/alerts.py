"""
Alert generation service for PlantaOS × Rock in Rio Lisboa 2026.

Alert rules:
    CRITICO : ocupacao_pct > 90
    ALTO    : ocupacao_pct > 75 AND fila_actual > 20
    MEDIO   : confianca_pct < 40
    INFO    : sensor offline > 5 minutes  (handled separately via sensor timestamps)

Only the most-severe alert per section is raised (CRITICO > ALTO > MEDIO > INFO).
Multiple alerts can coexist across different sections/clusters.
"""
from __future__ import annotations

import time
from typing import Dict, List, Optional

from app.schemas import Alert, AlertSeveridade, SectionState

# Thresholds
CRITICO_OCUPACAO_THRESHOLD = 90.0
ALTO_OCUPACAO_THRESHOLD = 75.0
ALTO_FILA_THRESHOLD = 20
MEDIO_CONFIANCA_THRESHOLD = 40.0
SENSOR_OFFLINE_SECONDS = 300  # 5 minutes


def evaluate_section(
    cluster_id: str,
    section: str,
    state: SectionState,
    last_sensor_ts: Optional[float] = None,
) -> List[Alert]:
    """
    Evaluate alert conditions for a single section.

    Parameters
    ----------
    cluster_id : str
        Cluster identifier (e.g. "WC-01").
    section : str
        Section key ("M", "F", or "U").
    state : SectionState
        Current live state for the section.
    last_sensor_ts : float | None
        Unix timestamp of the most recent sensor reading for this section.
        If None, the INFO/offline check is skipped.

    Returns
    -------
    list[Alert]
        Zero or more alerts raised, ordered by severity descending.
    """
    alerts: List[Alert] = []
    now = time.time()

    # CRITICO: high occupancy
    if state.ocupacao_pct > CRITICO_OCUPACAO_THRESHOLD:
        alerts.append(Alert(
            cluster_id=cluster_id,
            section=section,
            severidade=AlertSeveridade.CRITICO,
            mensagem=(
                f"{cluster_id}/{section}: ocupação crítica — "
                f"{state.ocupacao_pct:.0f}% (limite: {CRITICO_OCUPACAO_THRESHOLD:.0f}%)"
            ),
            ts=now,
        ))

    # ALTO: high occupancy + long queue
    if (
        state.ocupacao_pct > ALTO_OCUPACAO_THRESHOLD
        and state.fila_actual > ALTO_FILA_THRESHOLD
    ):
        alerts.append(Alert(
            cluster_id=cluster_id,
            section=section,
            severidade=AlertSeveridade.ALTO,
            mensagem=(
                f"{cluster_id}/{section}: ocupação elevada — "
                f"{state.ocupacao_pct:.0f}% com fila de {state.fila_actual} pessoas"
            ),
            ts=now,
        ))

    # MEDIO: low sensor confidence
    if state.confianca_pct < MEDIO_CONFIANCA_THRESHOLD:
        alerts.append(Alert(
            cluster_id=cluster_id,
            section=section,
            severidade=AlertSeveridade.MEDIO,
            mensagem=(
                f"{cluster_id}/{section}: confiança dos sensores baixa — "
                f"{state.confianca_pct:.0f}% (mínimo: {MEDIO_CONFIANCA_THRESHOLD:.0f}%)"
            ),
            ts=now,
        ))

    # INFO: sensor offline
    if last_sensor_ts is not None:
        elapsed = now - last_sensor_ts
        if elapsed > SENSOR_OFFLINE_SECONDS:
            minutes_offline = elapsed / 60
            alerts.append(Alert(
                cluster_id=cluster_id,
                section=section,
                severidade=AlertSeveridade.INFO,
                mensagem=(
                    f"{cluster_id}/{section}: sensor sem dados há "
                    f"{minutes_offline:.0f} minutos"
                ),
                ts=now,
            ))

    return alerts


def evaluate_all_clusters(
    cluster_states: dict,
    sensor_timestamps: Optional[Dict[str, float]] = None,
) -> List[Alert]:
    """
    Evaluate alert conditions for all clusters and sections.

    Parameters
    ----------
    cluster_states : dict[str, ClusterState]
        Full runtime cluster state keyed by cluster_id.
    sensor_timestamps : dict[str, float] | None
        Last sensor timestamp keyed by "{cluster_id}_{section}".

    Returns
    -------
    list[Alert]
        All currently active alerts, sorted by severity then cluster.
    """
    if sensor_timestamps is None:
        sensor_timestamps = {}

    all_alerts: List[Alert] = []
    severity_order = {
        AlertSeveridade.CRITICO: 0,
        AlertSeveridade.ALTO: 1,
        AlertSeveridade.MEDIO: 2,
        AlertSeveridade.INFO: 3,
    }

    for cluster_id, cs in cluster_states.items():
        for section, ss in cs.secoes.items():
            ts_key = f"{cluster_id}_{section}"
            last_ts = sensor_timestamps.get(ts_key)
            section_alerts = evaluate_section(cluster_id, section, ss, last_ts)
            all_alerts.extend(section_alerts)

    # Sort: most severe first, then by cluster ID
    all_alerts.sort(
        key=lambda a: (severity_order[a.severidade], a.cluster_id)
    )
    return all_alerts


def count_critico(alerts: List[Alert]) -> int:
    """Count only CRITICO-severity alerts."""
    return sum(1 for a in alerts if a.severidade == AlertSeveridade.CRITICO)
