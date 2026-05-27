"""
Tests for the alert generation service.
"""
from __future__ import annotations

import time

import pytest

from app.schemas import Alert, AlertSeveridade, SectionState
from app.services.alerts import (
    CRITICO_OCUPACAO_THRESHOLD,
    ALTO_OCUPACAO_THRESHOLD,
    ALTO_FILA_THRESHOLD,
    MEDIO_CONFIANCA_THRESHOLD,
    SENSOR_OFFLINE_SECONDS,
    count_critico,
    evaluate_all_clusters,
    evaluate_section,
)


class TestEvaluateSection:
    def test_critico_when_occupancy_above_90(self):
        """occupancy > 90 must trigger CRITICO."""
        state = SectionState(ocupacao_pct=91.0, fila_actual=0, confianca_pct=100.0)
        alerts = evaluate_section("WC-01", "M", state)
        severidades = [a.severidade for a in alerts]
        assert AlertSeveridade.CRITICO in severidades

    def test_critico_at_threshold_boundary(self):
        """Exactly 90 % should NOT trigger CRITICO (must be strictly > 90)."""
        state = SectionState(ocupacao_pct=90.0, fila_actual=0, confianca_pct=100.0)
        alerts = evaluate_section("WC-01", "M", state)
        severidades = [a.severidade for a in alerts]
        assert AlertSeveridade.CRITICO not in severidades

    def test_no_critico_below_90(self):
        """occupancy <= 90 must NOT trigger CRITICO."""
        state = SectionState(ocupacao_pct=89.9, fila_actual=0, confianca_pct=100.0)
        alerts = evaluate_section("WC-01", "M", state)
        severidades = [a.severidade for a in alerts]
        assert AlertSeveridade.CRITICO not in severidades

    def test_alto_when_occupancy_above_75_and_queue_above_20(self):
        """occupancy > 75 AND queue > 20 must trigger ALTO."""
        state = SectionState(ocupacao_pct=80.0, fila_actual=25, confianca_pct=100.0)
        alerts = evaluate_section("WC-01", "M", state)
        severidades = [a.severidade for a in alerts]
        assert AlertSeveridade.ALTO in severidades

    def test_no_alto_when_queue_not_above_20(self):
        """occupancy > 75 but queue <= 20 must NOT trigger ALTO."""
        state = SectionState(ocupacao_pct=80.0, fila_actual=20, confianca_pct=100.0)
        alerts = evaluate_section("WC-01", "M", state)
        severidades = [a.severidade for a in alerts]
        assert AlertSeveridade.ALTO not in severidades

    def test_no_alto_when_occupancy_not_above_75(self):
        """queue > 20 but occupancy <= 75 must NOT trigger ALTO."""
        state = SectionState(ocupacao_pct=75.0, fila_actual=30, confianca_pct=100.0)
        alerts = evaluate_section("WC-01", "M", state)
        severidades = [a.severidade for a in alerts]
        assert AlertSeveridade.ALTO not in severidades

    def test_medio_when_confidence_below_40(self):
        """confianca_pct < 40 must trigger MEDIO."""
        state = SectionState(ocupacao_pct=50.0, fila_actual=0, confianca_pct=35.0)
        alerts = evaluate_section("WC-01", "M", state)
        severidades = [a.severidade for a in alerts]
        assert AlertSeveridade.MEDIO in severidades

    def test_no_medio_when_confidence_at_40(self):
        """confianca_pct == 40 must NOT trigger MEDIO (must be strictly < 40)."""
        state = SectionState(ocupacao_pct=50.0, fila_actual=0, confianca_pct=40.0)
        alerts = evaluate_section("WC-01", "M", state)
        severidades = [a.severidade for a in alerts]
        assert AlertSeveridade.MEDIO not in severidades

    def test_info_when_sensor_offline_over_5_minutes(self):
        """Sensor offline > 5 min must trigger INFO."""
        old_ts = time.time() - (SENSOR_OFFLINE_SECONDS + 60)
        state = SectionState(ocupacao_pct=50.0, confianca_pct=100.0)
        alerts = evaluate_section("WC-01", "M", state, last_sensor_ts=old_ts)
        severidades = [a.severidade for a in alerts]
        assert AlertSeveridade.INFO in severidades

    def test_no_info_when_sensor_recently_seen(self):
        """Recent sensor reading must NOT trigger INFO."""
        recent_ts = time.time() - 10
        state = SectionState(ocupacao_pct=50.0, confianca_pct=100.0)
        alerts = evaluate_section("WC-01", "M", state, last_sensor_ts=recent_ts)
        severidades = [a.severidade for a in alerts]
        assert AlertSeveridade.INFO not in severidades

    def test_no_alerts_for_normal_state(self):
        """Normal operating conditions should produce no alerts."""
        state = SectionState(ocupacao_pct=45.0, fila_actual=5, confianca_pct=95.0)
        alerts = evaluate_section("WC-01", "M", state)
        assert len(alerts) == 0

    def test_multiple_alerts_can_coexist(self):
        """Both CRITICO (occupancy) and MEDIO (confidence) can be raised simultaneously."""
        state = SectionState(ocupacao_pct=95.0, fila_actual=0, confianca_pct=20.0)
        alerts = evaluate_section("WC-01", "M", state)
        severidades = {a.severidade for a in alerts}
        assert AlertSeveridade.CRITICO in severidades
        assert AlertSeveridade.MEDIO in severidades

    def test_alert_contains_cluster_and_section(self):
        """Alerts must reference the correct cluster and section."""
        state = SectionState(ocupacao_pct=95.0, confianca_pct=100.0)
        alerts = evaluate_section("WC-05", "U", state)
        for a in alerts:
            assert a.cluster_id == "WC-05"
            assert a.section == "U"


class TestEvaluateAllClusters:
    def _build_states(self):
        """Build minimal cluster states for testing."""
        from app.data.clusters import CLUSTERS, get_sections_for_cluster
        from app.schemas import ClusterState, ClusterTipo
        from app.data.clusters import CLUSTERS_BY_ID

        states = {}
        for c in CLUSTERS:
            cid = c["id"]
            sections = get_sections_for_cluster(cid)
            secoes = {
                s: SectionState(ocupacao_pct=50.0, confianca_pct=100.0)
                for s in sections
            }
            states[cid] = ClusterState(
                cluster_id=cid,
                nome=c["nome"],
                tipo=ClusterTipo(c["tipo"]),
                entry_only=c["entry_only"],
                lat=c["lat"],
                lon=c["lon"],
                dist_entrada_m=c["dist_entrada_m"],
                secoes=secoes,
            )
        return states

    def test_no_alerts_normal_state(self):
        states = self._build_states()
        alerts = evaluate_all_clusters(states)
        assert len(alerts) == 0

    def test_critico_detected_across_clusters(self):
        states = self._build_states()
        # Force WC-01/M to critical
        states["WC-01"].secoes["M"] = SectionState(
            ocupacao_pct=95.0, confianca_pct=100.0
        )
        alerts = evaluate_all_clusters(states)
        critico_alerts = [a for a in alerts if a.severidade == AlertSeveridade.CRITICO]
        assert len(critico_alerts) >= 1
        assert any(a.cluster_id == "WC-01" and a.section == "M" for a in critico_alerts)


class TestCountCritico:
    def test_count_critico(self):
        alerts = [
            Alert(cluster_id="WC-01", section="M",
                  severidade=AlertSeveridade.CRITICO, mensagem="a"),
            Alert(cluster_id="WC-01", section="F",
                  severidade=AlertSeveridade.ALTO, mensagem="b"),
            Alert(cluster_id="WC-02", section="M",
                  severidade=AlertSeveridade.CRITICO, mensagem="c"),
        ]
        assert count_critico(alerts) == 2

    def test_no_critico(self):
        alerts = [
            Alert(cluster_id="WC-01", section="M",
                  severidade=AlertSeveridade.MEDIO, mensagem="a"),
        ]
        assert count_critico(alerts) == 0
