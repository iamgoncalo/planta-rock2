"""
Tests for Pydantic schema invariants.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.data.clusters import (
    CLUSTERS_BY_ID,
    UNISEX_CLUSTER_IDS,
    MISTO_CLUSTER_IDS,
    get_sections_for_cluster,
)
from app.schemas import (
    Alert,
    AlertSeveridade,
    ClusterTipo,
    SectionState,
    SensorReading,
)


# ---------------------------------------------------------------------------
# Cluster section invariants
# ---------------------------------------------------------------------------

class TestClusterSections:
    def test_wc05_is_unisex(self):
        """WC-05 must be unisex — sections are U only."""
        sections = get_sections_for_cluster("WC-05")
        assert sections == ["U"], f"Expected ['U'], got {sections}"

    def test_wc06_is_unisex(self):
        """WC-06 must be unisex — sections are U only."""
        sections = get_sections_for_cluster("WC-06")
        assert sections == ["U"], f"Expected ['U'], got {sections}"

    def test_wc01_has_m_and_f(self):
        """WC-01 is mixed — must have M and F sections."""
        sections = get_sections_for_cluster("WC-01")
        assert "M" in sections
        assert "F" in sections
        assert "U" not in sections

    def test_wc02_has_m_and_f(self):
        sections = get_sections_for_cluster("WC-02")
        assert "M" in sections and "F" in sections

    def test_wc03_has_m_and_f(self):
        sections = get_sections_for_cluster("WC-03")
        assert "M" in sections and "F" in sections

    def test_wc04_has_m_and_f(self):
        sections = get_sections_for_cluster("WC-04")
        assert "M" in sections and "F" in sections

    def test_wc07_has_m_and_f(self):
        sections = get_sections_for_cluster("WC-07")
        assert "M" in sections and "F" in sections

    def test_wc08_has_m_and_f(self):
        sections = get_sections_for_cluster("WC-08")
        assert "M" in sections and "F" in sections

    def test_unisex_clusters_have_no_m_or_f(self):
        """WC-05 and WC-06 must never have M or F sections."""
        for cid in UNISEX_CLUSTER_IDS:
            sections = get_sections_for_cluster(cid)
            assert "M" not in sections, f"{cid} should not have M section"
            assert "F" not in sections, f"{cid} should not have F section"

    def test_misto_clusters_have_no_u(self):
        """Mixed clusters must never have a U section."""
        for cid in MISTO_CLUSTER_IDS:
            sections = get_sections_for_cluster(cid)
            assert "U" not in sections, f"{cid} should not have U section"

    def test_all_8_clusters_present(self):
        """All 8 clusters must be present in static data."""
        expected = {"WC-01", "WC-02", "WC-03", "WC-04", "WC-05", "WC-06", "WC-07", "WC-08"}
        assert set(CLUSTERS_BY_ID.keys()) == expected

    def test_wc05_tipo_is_unissex(self):
        assert CLUSTERS_BY_ID["WC-05"]["tipo"] == "unissex"

    def test_wc06_tipo_is_unissex(self):
        assert CLUSTERS_BY_ID["WC-06"]["tipo"] == "unissex"

    def test_wc01_tipo_is_misto(self):
        assert CLUSTERS_BY_ID["WC-01"]["tipo"] == "misto"

    def test_wc05_is_entry_only(self):
        assert CLUSTERS_BY_ID["WC-05"]["entry_only"] is True

    def test_wc06_is_not_entry_only(self):
        assert CLUSTERS_BY_ID["WC-06"]["entry_only"] is False


# ---------------------------------------------------------------------------
# SectionState invariants
# ---------------------------------------------------------------------------

class TestSectionState:
    def test_valid_occupancy_range(self):
        """occupancy_pct must be accepted in [0, 100]."""
        s = SectionState(ocupacao_pct=55.0)
        assert 0.0 <= s.ocupacao_pct <= 100.0

    def test_occupancy_clamped_above_100(self):
        """Values above 100 must be clamped to 100."""
        s = SectionState(ocupacao_pct=150.0)
        assert s.ocupacao_pct == 100.0

    def test_occupancy_clamped_below_0(self):
        """Values below 0 must be clamped to 0."""
        s = SectionState(ocupacao_pct=-10.0)
        assert s.ocupacao_pct == 0.0

    def test_confidence_clamped(self):
        s = SectionState(confianca_pct=120.0)
        assert s.confianca_pct == 100.0

    def test_default_values(self):
        s = SectionState()
        assert s.ocupacao_pct == 0.0
        assert s.fila_actual == 0
        assert s.confianca_pct == 100.0

    def test_compute_status_livre(self):
        s = SectionState(ocupacao_pct=30.0)
        updated = s.compute_status()
        assert updated.status.value == "livre"

    def test_compute_status_moderado(self):
        s = SectionState(ocupacao_pct=60.0)
        updated = s.compute_status()
        assert updated.status.value == "moderado"

    def test_compute_status_cheio(self):
        s = SectionState(ocupacao_pct=80.0)
        updated = s.compute_status()
        assert updated.status.value == "cheio"

    def test_compute_status_critico(self):
        s = SectionState(ocupacao_pct=95.0)
        updated = s.compute_status()
        assert updated.status.value == "critico"


# ---------------------------------------------------------------------------
# Alert invariants
# ---------------------------------------------------------------------------

class TestAlertSchema:
    def test_valid_severidades(self):
        """Alert severidade must be one of CRITICO/ALTO/MEDIO/INFO."""
        for sev in ["CRITICO", "ALTO", "MEDIO", "INFO"]:
            a = Alert(
                cluster_id="WC-01",
                section="M",
                severidade=sev,
                mensagem="test",
            )
            assert a.severidade.value == sev

    def test_invalid_severidade_raises(self):
        with pytest.raises((ValidationError, ValueError)):
            Alert(
                cluster_id="WC-01",
                section="M",
                severidade="INVALID",
                mensagem="test",
            )

    def test_alert_critico_value(self):
        a = Alert(
            cluster_id="WC-01", section="M",
            severidade=AlertSeveridade.CRITICO, mensagem="test"
        )
        assert a.severidade == AlertSeveridade.CRITICO

    def test_alert_info_value(self):
        a = Alert(
            cluster_id="WC-01", section="M",
            severidade=AlertSeveridade.INFO, mensagem="test"
        )
        assert a.severidade == AlertSeveridade.INFO


# ---------------------------------------------------------------------------
# SensorReading invariants
# ---------------------------------------------------------------------------

class TestSensorReading:
    def test_valid_payload(self):
        r = SensorReading(
            cluster_id="WC-01",
            section="M",
            source="IR",
            contagem_entrada=10,
            contagem_saida=5,
        )
        assert r.cluster_id == "WC-01"
        assert r.section == "M"

    def test_invalid_cluster_id_raises(self):
        with pytest.raises(ValidationError):
            SensorReading(
                cluster_id="WC-99",
                section="M",
                source="IR",
                contagem_entrada=0,
                contagem_saida=0,
            )

    def test_invalid_section_raises(self):
        with pytest.raises(ValidationError):
            SensorReading(
                cluster_id="WC-01",
                section="X",
                source="IR",
                contagem_entrada=0,
                contagem_saida=0,
            )

    def test_no_gps_in_payload(self):
        """SensorReading must NOT have lat/lon fields."""
        r = SensorReading(
            cluster_id="WC-01", section="M", source="IR",
            contagem_entrada=0, contagem_saida=0,
        )
        assert not hasattr(r, "lat")
        assert not hasattr(r, "lon")
