"""
KPI calculation service for PlantaOS × Rock in Rio Lisboa 2026.

KPI Definitions
---------------
KPI-01  Flow Index (0–100)
    = 100
      - (avg_occupancy_pct × 0.4)
      - (avg_queue_pressure × 0.4)
      - (sensor_degradation × 0.2)
    Clamped to [0, 100].  Higher = better crowd flow.

KPI-02  Average occupancy %
    = mean of ocupacao_pct across all active sections.

KPI-03  Critical alert count
    = number of alerts with severidade == CRITICO.

KPI-04  Daily cumulative people redirected
    = non-negative integer, accumulated across the day.
"""
from __future__ import annotations

import datetime
from typing import Dict, List, Optional, Tuple

from app.data.shows import FESTIVAL_DAY_BY_DATE, SHOWS
from app.schemas import Alert, AlertSeveridade, ClusterState, KPIs, SectionState


def _avg_occupancy(cluster_states: Dict[str, ClusterState]) -> float:
    """Return average occupancy % across all sections of all clusters."""
    values = []
    for cs in cluster_states.values():
        for ss in cs.secoes.values():
            values.append(ss.ocupacao_pct)
    if not values:
        return 0.0
    return sum(values) / len(values)


def _avg_queue_pressure(cluster_states: Dict[str, ClusterState]) -> float:
    """
    Queue pressure: average (fila_actual / max_expected_queue) × 100, capped at 100.
    We use 50 people as the normalisation constant for max expected queue.
    """
    MAX_QUEUE = 50.0
    values = []
    for cs in cluster_states.values():
        for ss in cs.secoes.values():
            pressure = min(100.0, (ss.fila_actual / MAX_QUEUE) * 100.0)
            values.append(pressure)
    if not values:
        return 0.0
    return sum(values) / len(values)


def _sensor_degradation(cluster_states: Dict[str, ClusterState]) -> float:
    """
    Sensor degradation: average (100 - confianca_pct) across all sections.
    Higher value = worse sensors.
    """
    values = []
    for cs in cluster_states.values():
        for ss in cs.secoes.values():
            values.append(100.0 - ss.confianca_pct)
    if not values:
        return 0.0
    return sum(values) / len(values)


def calculate_kpi_01(cluster_states: Dict[str, ClusterState]) -> float:
    """
    Flow Index (0–100).  Higher = better crowd flow.
    """
    avg_occ = _avg_occupancy(cluster_states)
    avg_queue = _avg_queue_pressure(cluster_states)
    degradation = _sensor_degradation(cluster_states)

    flow_index = (
        100.0
        - avg_occ * 0.4
        - avg_queue * 0.4
        - degradation * 0.2
    )
    return max(0.0, min(100.0, flow_index))


def calculate_kpi_02(cluster_states: Dict[str, ClusterState]) -> float:
    """Average occupancy % across all active sections."""
    return _avg_occupancy(cluster_states)


def calculate_kpi_03(alerts: List[Alert]) -> int:
    """Count of CRITICO alerts currently active."""
    return sum(1 for a in alerts if a.severidade == AlertSeveridade.CRITICO)


def get_festival_context(
    now: Optional[datetime.datetime] = None,
) -> Tuple[Optional[int], Optional[str], Optional[float]]:
    """
    Derive festival day, active headliner, and minutes to next headliner.

    Returns
    -------
    (festival_day, show_activo, minutos_para_headliner)
    """
    if now is None:
        now = datetime.datetime.now()

    date_str = now.strftime("%Y-%m-%d")
    festival_day = FESTIVAL_DAY_BY_DATE.get(date_str)

    # Filter headliners for today
    today_headliners = [
        s for s in SHOWS
        if s["headliner"] and s["data"] == date_str
    ]

    show_activo: Optional[str] = None
    minutos_para_headliner: Optional[float] = None

    current_time_str = now.strftime("%H:%M")

    for show in today_headliners:
        inicio = show["inicio"]
        fim = show["fim"]

        # Parse as time objects for comparison
        h_ini, m_ini = map(int, inicio.split(":"))
        h_fim, m_fim = map(int, fim.split(":"))
        h_now, m_now = map(int, current_time_str.split(":"))

        # Handle midnight crossover
        total_ini = h_ini * 60 + m_ini
        total_fim = h_fim * 60 + m_fim
        if total_fim == 0:  # "00:00" means end of day / midnight
            total_fim = 24 * 60
        total_now = h_now * 60 + m_now

        if total_ini <= total_now < total_fim:
            show_activo = show["artista"]
            break
        elif total_now < total_ini:
            mins = float(total_ini - total_now)
            if minutos_para_headliner is None or mins < minutos_para_headliner:
                minutos_para_headliner = mins
                show_activo = None  # Not started yet

    return festival_day, show_activo, minutos_para_headliner


def calculate_all_kpis(
    cluster_states: Dict[str, ClusterState],
    alerts: List[Alert],
    daily_redirected: int,
    now: Optional[datetime.datetime] = None,
) -> KPIs:
    """
    Compute all four KPIs and attach festival context.

    Parameters
    ----------
    cluster_states : dict
        Current cluster state keyed by cluster_id.
    alerts : list[Alert]
        Currently active alerts.
    daily_redirected : int
        KPI-04 accumulator value.
    now : datetime | None
        Override for "current time" (useful in tests / simulation).

    Returns
    -------
    KPIs
    """
    kpi_01 = calculate_kpi_01(cluster_states)
    kpi_02 = calculate_kpi_02(cluster_states)
    kpi_03 = calculate_kpi_03(alerts)
    kpi_04 = max(0, daily_redirected)

    festival_day, show_activo, minutos_para_headliner = get_festival_context(now)

    return KPIs(
        kpi_01=round(kpi_01, 1),
        kpi_02=round(kpi_02, 1),
        kpi_03=kpi_03,
        kpi_04=kpi_04,
        festival_day=festival_day,
        show_activo=show_activo,
        minutos_para_headliner=minutos_para_headliner,
    )
