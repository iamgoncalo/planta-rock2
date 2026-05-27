"""
Tests for the simulation engine.
"""
from __future__ import annotations

import copy

import pytest

from app.data.clusters import CLUSTERS, get_sections_for_cluster
from app.schemas import ClusterState, ClusterTipo, SectionState
from app.services.simulation import VALID_SCENARIOS, run_tick


def _make_initial_states() -> dict:
    """Build a fresh initial state dict for all 8 clusters."""
    from app.data.clusters import CLUSTERS_BY_ID

    states = {}
    for c in CLUSTERS:
        cid = c["id"]
        sections = get_sections_for_cluster(cid)
        secoes = {
            s: SectionState(
                ocupacao_pct=0.0,
                ocupacao_absoluta=0,
                fila_actual=0,
                confianca_pct=100.0,
                fontes_activas=["IR", "WiFi", "Camera"],
            )
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


class TestSimulationTick:
    def test_tick_changes_state(self):
        """A tick should change state (not identical to before)."""
        states = _make_initial_states()
        # Deep copy occupancies before tick
        before = {
            cid: {sec: ss.ocupacao_pct for sec, ss in cs.secoes.items()}
            for cid, cs in states.items()
        }
        updated, count = run_tick(states, "normal_day", tick=1, hora_simulada="20:00")
        after = {
            cid: {sec: ss.ocupacao_pct for sec, ss in cs.secoes.items()}
            for cid, cs in updated.items()
        }
        # At least one section should have changed
        changed = any(
            before[cid][sec] != after[cid][sec]
            for cid in before
            for sec in before[cid]
        )
        assert changed, "Tick must change at least one section state"

    def test_all_8_clusters_updated(self):
        """All 8 clusters must be present after a tick."""
        states = _make_initial_states()
        updated, count = run_tick(states, "normal_day", tick=1)
        assert set(updated.keys()) == {
            "WC-01", "WC-02", "WC-03", "WC-04",
            "WC-05", "WC-06", "WC-07", "WC-08"
        }
        assert count == 8

    def test_normal_day_produces_valid_occupancy(self):
        """normal_day scenario must produce occupancy values in [0, 100]."""
        states = _make_initial_states()
        updated, _ = run_tick(states, "normal_day", tick=1, hora_simulada="20:00")
        for cid, cs in updated.items():
            for sec, ss in cs.secoes.items():
                assert 0.0 <= ss.ocupacao_pct <= 100.0, (
                    f"{cid}/{sec} occupancy out of range: {ss.ocupacao_pct}"
                )

    def test_headliner_start_higher_than_normal_day(self):
        """headliner_start scenario should produce higher occupancy than normal_day."""
        states_normal = _make_initial_states()
        states_headliner = _make_initial_states()

        updated_normal, _ = run_tick(states_normal, "normal_day", tick=1, hora_simulada="21:00")
        updated_headliner, _ = run_tick(states_headliner, "headliner_start", tick=1, hora_simulada="21:00")

        avg_normal = sum(
            ss.ocupacao_pct
            for cs in updated_normal.values()
            for ss in cs.secoes.values()
        ) / sum(len(cs.secoes) for cs in updated_normal.values())

        avg_headliner = sum(
            ss.ocupacao_pct
            for cs in updated_headliner.values()
            for ss in cs.secoes.values()
        ) / sum(len(cs.secoes) for cs in updated_headliner.values())

        assert avg_headliner > avg_normal, (
            f"headliner_start ({avg_headliner:.1f}%) should be > "
            f"normal_day ({avg_normal:.1f}%)"
        )

    def test_wc05_and_wc06_have_only_u_section(self):
        """After a tick, WC-05 and WC-06 must only have section 'U'."""
        states = _make_initial_states()
        updated, _ = run_tick(states, "normal_day", tick=1)
        assert set(updated["WC-05"].secoes.keys()) == {"U"}
        assert set(updated["WC-06"].secoes.keys()) == {"U"}

    def test_misto_clusters_have_only_m_and_f(self):
        """After a tick, misto clusters must only have M and F sections."""
        states = _make_initial_states()
        updated, _ = run_tick(states, "normal_day", tick=1)
        for cid in ["WC-01", "WC-02", "WC-03", "WC-04", "WC-07", "WC-08"]:
            sections = set(updated[cid].secoes.keys())
            assert sections == {"M", "F"}, (
                f"{cid} should have M and F, got {sections}"
            )

    def test_sensor_ir_offline_lowers_confidence(self):
        """sensor_ir_offline scenario must lower confidence below normal_day."""
        states_normal = _make_initial_states()
        states_offline = _make_initial_states()

        updated_normal, _ = run_tick(states_normal, "normal_day", tick=1, hora_simulada="20:00")
        updated_offline, _ = run_tick(states_offline, "sensor_ir_offline", tick=1, hora_simulada="20:00")

        avg_conf_normal = sum(
            ss.confianca_pct
            for cs in updated_normal.values()
            for ss in cs.secoes.values()
        ) / sum(len(cs.secoes) for cs in updated_normal.values())

        avg_conf_offline = sum(
            ss.confianca_pct
            for cs in updated_offline.values()
            for ss in cs.secoes.values()
        ) / sum(len(cs.secoes) for cs in updated_offline.values())

        assert avg_conf_offline < avg_conf_normal

    def test_recovery_scenario_lower_occupancy(self):
        """recovery_after_redirect scenario should produce lower occupancy than headliner_end_surge."""
        states_surge = _make_initial_states()
        states_recovery = _make_initial_states()

        updated_surge, _ = run_tick(states_surge, "headliner_end_surge", tick=1, hora_simulada="23:00")
        updated_recovery, _ = run_tick(states_recovery, "recovery_after_redirect", tick=1, hora_simulada="23:00")

        avg_surge = sum(
            ss.ocupacao_pct
            for cs in updated_surge.values()
            for ss in cs.secoes.values()
        ) / sum(len(cs.secoes) for cs in updated_surge.values())

        avg_recovery = sum(
            ss.ocupacao_pct
            for cs in updated_recovery.values()
            for ss in cs.secoes.values()
        ) / sum(len(cs.secoes) for cs in updated_recovery.values())

        assert avg_recovery < avg_surge

    def test_valid_scenarios_count(self):
        """There should be exactly 15 valid scenarios."""
        assert len(VALID_SCENARIOS) == 15

    def test_all_scenarios_run_without_error(self):
        """Every scenario must run a tick without raising exceptions."""
        for scenario in VALID_SCENARIOS:
            states = _make_initial_states()
            updated, count = run_tick(states, scenario, tick=1, hora_simulada="20:00")
            assert count == 8, f"Scenario {scenario} did not update all 8 clusters"

    def test_hora_simulada_override(self):
        """Simulating different hours should produce different occupancies."""
        states_morning = _make_initial_states()
        states_peak = _make_initial_states()

        updated_morning, _ = run_tick(states_morning, "normal_day", tick=1, hora_simulada="09:00")
        updated_peak, _ = run_tick(states_peak, "normal_day", tick=1, hora_simulada="22:00")

        avg_morning = sum(
            ss.ocupacao_pct
            for cs in updated_morning.values()
            for ss in cs.secoes.values()
        ) / sum(len(cs.secoes) for cs in updated_morning.values())

        avg_peak = sum(
            ss.ocupacao_pct
            for cs in updated_peak.values()
            for ss in cs.secoes.values()
        ) / sum(len(cs.secoes) for cs in updated_peak.values())

        assert avg_peak > avg_morning, (
            f"22:00 ({avg_peak:.1f}%) should be > 09:00 ({avg_morning:.1f}%)"
        )

    def test_occupancy_always_in_valid_range(self):
        """All scenarios at various hours must stay within [0, 100]."""
        hours = ["08:00", "14:00", "21:00", "23:00"]
        for scenario in ["normal_day", "headliner_start", "crowd_surge", "network_dropout"]:
            for hour in hours:
                states = _make_initial_states()
                updated, _ = run_tick(states, scenario, tick=1, hora_simulada=hour)
                for cid, cs in updated.items():
                    for sec, ss in cs.secoes.items():
                        assert 0.0 <= ss.ocupacao_pct <= 100.0, (
                            f"{scenario} @ {hour}: {cid}/{sec} = {ss.ocupacao_pct}"
                        )
