"""
Tests for the KPI calculation service.
"""
from __future__ import annotations

import datetime
from typing import Dict

import pytest

from app.data.clusters import CLUSTERS, get_sections_for_cluster
from app.schemas import Alert, AlertSeveridade, ClusterState, ClusterTipo, SectionState
from app.services.kpis import (
    calculate_all_kpis,
    calculate_kpi_01,
    calculate_kpi_02,
    calculate_kpi_03,
    get_festival_context,
)


def _make_cluster_state(
    cluster_id: str,
    occupancies: Dict[str, float],
    queues: Dict[str, int] = None,
    confidences: Dict[str, float] = None,
) -> ClusterState:
    """Helper to build a ClusterState with given section occupancies."""
    from app.data.clusters import CLUSTERS_BY_ID
    meta = CLUSTERS_BY_ID[cluster_id]
    sections = get_sections_for_cluster(cluster_id)
    secoes = {}
    for sec in sections:
        occ = occupancies.get(sec, 50.0)
        queue = (queues or {}).get(sec, 0)
        conf = (confidences or {}).get(sec, 100.0)
        secoes[sec] = SectionState(
            ocupacao_pct=occ,
            fila_actual=queue,
            confianca_pct=conf,
        )
    return ClusterState(
        cluster_id=cluster_id,
        nome=meta["nome"],
        tipo=ClusterTipo(meta["tipo"]),
        entry_only=meta["entry_only"],
        lat=meta["lat"],
        lon=meta["lon"],
        dist_entrada_m=meta["dist_entrada_m"],
        secoes=secoes,
    )


def _make_all_clusters(base_occ: float = 50.0) -> Dict[str, ClusterState]:
    states = {}
    for c in CLUSTERS:
        cid = c["id"]
        sections = get_sections_for_cluster(cid)
        states[cid] = _make_cluster_state(
            cid, {s: base_occ for s in sections}
        )
    return states


class TestKPI01:
    def test_in_range(self):
        """KPI-01 must always be between 0 and 100."""
        states = _make_all_clusters(50.0)
        kpi = calculate_kpi_01(states)
        assert 0.0 <= kpi <= 100.0

    def test_high_occupancy_lowers_flow(self):
        """Higher occupancy should lower the flow index."""
        states_low = _make_all_clusters(20.0)
        states_high = _make_all_clusters(90.0)
        assert calculate_kpi_01(states_low) > calculate_kpi_01(states_high)

    def test_all_zero_occupancy_gives_high_flow(self):
        """Zero occupancy, zero queue, full confidence → high flow index."""
        states = _make_all_clusters(0.0)
        kpi = calculate_kpi_01(states)
        assert kpi >= 90.0

    def test_full_occupancy_gives_low_flow(self):
        """Full occupancy → low flow index."""
        states = _make_all_clusters(100.0)
        kpi = calculate_kpi_01(states)
        assert kpi <= 60.0

    def test_low_confidence_lowers_flow(self):
        """Low confidence (degraded sensors) should lower KPI-01."""
        states_good = _make_all_clusters(50.0)
        states_bad = {}
        for cid, cs in states_good.items():
            sections = get_sections_for_cluster(cid)
            states_bad[cid] = _make_cluster_state(
                cid,
                {s: 50.0 for s in sections},
                confidences={s: 10.0 for s in sections},
            )
        assert calculate_kpi_01(states_good) > calculate_kpi_01(states_bad)


class TestKPI02:
    def test_is_average_of_section_occupancies(self):
        """KPI-02 must be the mean of all section occupancies."""
        # All clusters at 60 % → KPI-02 should be 60.
        states = _make_all_clusters(60.0)
        kpi = calculate_kpi_02(states)
        assert abs(kpi - 60.0) < 0.5

    def test_in_range(self):
        states = _make_all_clusters(75.0)
        kpi = calculate_kpi_02(states)
        assert 0.0 <= kpi <= 100.0

    def test_empty_returns_zero(self):
        kpi = calculate_kpi_02({})
        assert kpi == 0.0


class TestKPI03:
    def test_counts_only_critico(self):
        """KPI-03 must count only CRITICO alerts."""
        alerts = [
            Alert(cluster_id="WC-01", section="M",
                  severidade=AlertSeveridade.CRITICO, mensagem="test"),
            Alert(cluster_id="WC-01", section="F",
                  severidade=AlertSeveridade.ALTO, mensagem="test"),
            Alert(cluster_id="WC-02", section="M",
                  severidade=AlertSeveridade.CRITICO, mensagem="test"),
            Alert(cluster_id="WC-02", section="F",
                  severidade=AlertSeveridade.INFO, mensagem="test"),
        ]
        kpi = calculate_kpi_03(alerts)
        assert kpi == 2

    def test_no_critico_alerts(self):
        alerts = [
            Alert(cluster_id="WC-01", section="M",
                  severidade=AlertSeveridade.ALTO, mensagem="test"),
        ]
        assert calculate_kpi_03(alerts) == 0

    def test_empty_alerts(self):
        assert calculate_kpi_03([]) == 0


class TestKPI04:
    def test_non_negative(self):
        states = _make_all_clusters(50.0)
        kpis = calculate_all_kpis(states, [], 0)
        assert kpis.kpi_04 >= 0

    def test_accumulates_from_input(self):
        states = _make_all_clusters(50.0)
        kpis = calculate_all_kpis(states, [], daily_redirected=250)
        assert kpis.kpi_04 == 250


class TestCalculateAllKPIs:
    def test_returns_kpis_object(self):
        states = _make_all_clusters(50.0)
        kpis = calculate_all_kpis(states, [], 0)
        assert hasattr(kpis, "kpi_01")
        assert hasattr(kpis, "kpi_02")
        assert hasattr(kpis, "kpi_03")
        assert hasattr(kpis, "kpi_04")

    def test_all_in_range(self):
        states = _make_all_clusters(55.0)
        kpis = calculate_all_kpis(states, [], 100)
        assert 0.0 <= kpis.kpi_01 <= 100.0
        assert 0.0 <= kpis.kpi_02 <= 100.0
        assert kpis.kpi_03 >= 0
        assert kpis.kpi_04 >= 0

    def test_festival_day_on_festival_date(self):
        """On a festival date, festival_day should be set."""
        states = _make_all_clusters(50.0)
        now = datetime.datetime(2026, 6, 20, 20, 0, 0)
        kpis = calculate_all_kpis(states, [], 0, now=now)
        assert kpis.festival_day == 1

    def test_show_activo_katy_perry(self):
        """On Day 1 at 21:30, Katy Perry headliner should be active."""
        states = _make_all_clusters(50.0)
        now = datetime.datetime(2026, 6, 20, 21, 30, 0)
        kpis = calculate_all_kpis(states, [], 0, now=now)
        assert kpis.show_activo == "Katy Perry"

    def test_no_show_outside_festival(self):
        """On a non-festival date, show_activo should be None."""
        states = _make_all_clusters(50.0)
        now = datetime.datetime(2026, 1, 1, 12, 0, 0)
        kpis = calculate_all_kpis(states, [], 0, now=now)
        assert kpis.show_activo is None
