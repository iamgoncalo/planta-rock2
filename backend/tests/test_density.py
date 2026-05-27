"""
Tests for the crowd-density grid endpoint and service.

Track 07 — PlantaOS × Rock in Rio Lisboa 2026 quality audit.

Tests
-----
1. GET /api/v1/density-grid returns 200
2. Grid dimensions: cell_m=10 → 53×38; cell_m=25 → 21×15 (ceil-based)
3. All density_pm2 values are non-negative
4. total_estimated_people > 0 at normal_day scenario
5. Fruin level classification spot-check: density=1.5 p/m² → level E
6. GET /api/v1/density-grid?cell_m=5 uses smaller cells (more cols/rows)
7. Hotspots list only contains cells with level E or F
8. Invalid cell_m returns 422
9. gaussian_weight is monotonically decreasing with distance
10. FruinLevel enum covers A–F
"""
from __future__ import annotations

import math
from collections import defaultdict

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas_density import FruinLevel
from app.services.density import (
    VENUE_HEIGHT_M,
    VENUE_WIDTH_M,
    gaussian_weight,
    generate_density_grid,
    _fruin_level,
)


# ---------------------------------------------------------------------------
# Test client fixture (mirrors test_api.py approach)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client():
    """Async HTTP client with app_state initialised."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        from app.state import app_state
        if not app_state._initialised:
            from app.config import get_settings
            from app.services.alerts import evaluate_all_clusters
            from app.services.simulation import run_tick

            settings = get_settings()
            app_state.initialise(scenario=settings.simulation_initial_scenario)
            updated, _ = run_tick(
                cluster_states=app_state.cluster_states,
                scenario_name=settings.simulation_initial_scenario,
                tick=0,
            )
            app_state.cluster_states = updated
            alerts = evaluate_all_clusters(app_state.cluster_states)
            app_state.alerts = alerts
            alerts_by_cluster: dict = defaultdict(list)
            for a in alerts:
                alerts_by_cluster[a.cluster_id].append(a)
            for cid, cs in app_state.cluster_states.items():
                cs.alertas = alerts_by_cluster.get(cid, [])
        yield ac


# ---------------------------------------------------------------------------
# 1. Endpoint returns 200
# ---------------------------------------------------------------------------

class TestDensityGridEndpoint:
    async def test_returns_200(self, client):
        resp = await client.get("/api/v1/density-grid")
        assert resp.status_code == 200, resp.text

    async def test_response_has_required_keys(self, client):
        data = (await client.get("/api/v1/density-grid")).json()
        for key in ("ts", "cell_m", "grid_cols", "grid_rows",
                    "total_estimated_people", "cells", "hotspots"):
            assert key in data, f"Missing key: {key}"

    # -----------------------------------------------------------------------
    # 2. Grid dimensions
    # -----------------------------------------------------------------------

    async def test_grid_dims_10m(self, client):
        data = (await client.get("/api/v1/density-grid?cell_m=10")).json()
        expected_cols = math.ceil(VENUE_WIDTH_M / 10)   # 53
        expected_rows = math.ceil(VENUE_HEIGHT_M / 10)  # 38
        assert data["cell_m"] == 10
        assert data["grid_cols"] == expected_cols
        assert data["grid_rows"] == expected_rows

    async def test_grid_dims_25m(self, client):
        data = (await client.get("/api/v1/density-grid?cell_m=25")).json()
        expected_cols = math.ceil(VENUE_WIDTH_M / 25)   # ceil(530/25)=22
        expected_rows = math.ceil(VENUE_HEIGHT_M / 25)  # ceil(380/25)=16
        assert data["cell_m"] == 25
        assert data["grid_cols"] == expected_cols, (
            f"Expected {expected_cols} cols, got {data['grid_cols']}"
        )
        assert data["grid_rows"] == expected_rows, (
            f"Expected {expected_rows} rows, got {data['grid_rows']}"
        )

    # -----------------------------------------------------------------------
    # 3. All density values are non-negative
    # -----------------------------------------------------------------------

    async def test_all_densities_non_negative(self, client):
        data = (await client.get("/api/v1/density-grid")).json()
        for cell in data["cells"]:
            assert cell["density_pm2"] >= 0.0, (
                f"Negative density at ({cell['cell_x']}, {cell['cell_y']}): "
                f"{cell['density_pm2']}"
            )

    # -----------------------------------------------------------------------
    # 4. total_estimated_people > 0
    # -----------------------------------------------------------------------

    async def test_total_estimated_people_positive(self, client):
        data = (await client.get("/api/v1/density-grid")).json()
        assert data["total_estimated_people"] > 0.0

    # -----------------------------------------------------------------------
    # 6. cell_m=5 returns smaller cells (more rows and cols than 10m)
    # -----------------------------------------------------------------------

    async def test_cell_m_5_has_more_cells(self, client):
        data_10 = (await client.get("/api/v1/density-grid?cell_m=10")).json()
        data_5  = (await client.get("/api/v1/density-grid?cell_m=5")).json()
        assert data_5["grid_cols"] > data_10["grid_cols"]
        assert data_5["grid_rows"] > data_10["grid_rows"]

    async def test_cell_m_5_returns_200(self, client):
        resp = await client.get("/api/v1/density-grid?cell_m=5")
        assert resp.status_code == 200

    # -----------------------------------------------------------------------
    # 7. Hotspots only contain LoS E or F
    # -----------------------------------------------------------------------

    async def test_hotspots_only_e_or_f(self, client):
        data = (await client.get("/api/v1/density-grid")).json()
        for cell in data["hotspots"]:
            assert cell["level"] in ("E", "F"), (
                f"Hotspot has unexpected level: {cell['level']}"
            )

    async def test_hotspots_subset_of_cells(self, client):
        data = (await client.get("/api/v1/density-grid")).json()
        cell_keys = {(c["cell_x"], c["cell_y"]) for c in data["cells"]}
        for hs in data["hotspots"]:
            assert (hs["cell_x"], hs["cell_y"]) in cell_keys

    # -----------------------------------------------------------------------
    # 8. Invalid cell_m returns 422
    # -----------------------------------------------------------------------

    async def test_invalid_cell_m_returns_422(self, client):
        resp = await client.get("/api/v1/density-grid?cell_m=7")
        assert resp.status_code == 422

    async def test_cell_m_50_returns_200(self, client):
        resp = await client.get("/api/v1/density-grid?cell_m=50")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Service-layer unit tests (no HTTP)
# ---------------------------------------------------------------------------

class TestFruinClassification:
    """5. Fruin level classification spot-checks."""

    def test_density_1_5_is_level_e(self):
        """density = 1.5 p/m² is in [1.08, 2.17) → LoS E."""
        assert _fruin_level(1.5) == FruinLevel.E

    def test_density_below_0_27_is_level_a(self):
        assert _fruin_level(0.10) == FruinLevel.A

    def test_density_0_30_is_level_b(self):
        assert _fruin_level(0.30) == FruinLevel.B

    def test_density_0_50_is_level_c(self):
        assert _fruin_level(0.50) == FruinLevel.C

    def test_density_0_80_is_level_d(self):
        assert _fruin_level(0.80) == FruinLevel.D

    def test_density_above_2_17_is_level_f(self):
        assert _fruin_level(2.50) == FruinLevel.F

    def test_exact_boundary_0_27_is_b(self):
        """Lower boundary is inclusive: 0.27 → B."""
        assert _fruin_level(0.27) == FruinLevel.B

    def test_exact_boundary_1_08_is_e(self):
        assert _fruin_level(1.08) == FruinLevel.E


class TestGaussianWeight:
    """9. gaussian_weight is monotonically decreasing with distance."""

    def test_weight_at_zero_is_one(self):
        assert gaussian_weight(0.0) == pytest.approx(1.0, abs=1e-9)

    def test_weight_decreases_with_distance(self):
        d0 = gaussian_weight(0.0)
        d10 = gaussian_weight(10.0)
        d30 = gaussian_weight(30.0)
        d100 = gaussian_weight(100.0)
        assert d0 > d10 > d30 > d100

    def test_weight_at_sigma_is_exp_minus_half(self):
        """At d = σ, weight = exp(-0.5) ≈ 0.6065."""
        expected = math.exp(-0.5)
        assert gaussian_weight(30.0, sigma_m=30.0) == pytest.approx(expected, rel=1e-6)

    def test_weight_is_non_negative(self):
        for d in [0, 5, 10, 50, 200]:
            assert gaussian_weight(float(d)) >= 0.0


class TestFruinLevelEnum:
    """10. FruinLevel enum covers A–F."""

    def test_all_levels_present(self):
        levels = {lv.value for lv in FruinLevel}
        assert levels == {"A", "B", "C", "D", "E", "F"}


class TestGenerateDensityGrid:
    """Service-layer grid generation tests."""

    def _make_minimal_cluster_states(self):
        """
        Build a minimal dict of ClusterState-like objects for testing.
        Uses the real state if already initialised, otherwise bootstraps it.
        """
        from app.state import app_state
        if not app_state._initialised:
            from app.config import get_settings
            from app.services.simulation import run_tick
            settings = get_settings()
            app_state.initialise(scenario=settings.simulation_initial_scenario)
            updated, _ = run_tick(
                cluster_states=app_state.cluster_states,
                scenario_name=settings.simulation_initial_scenario,
                tick=0,
            )
            app_state.cluster_states = updated
        return app_state.cluster_states

    def test_grid_has_correct_col_row_count_10m(self):
        cs = self._make_minimal_cluster_states()
        grid = generate_density_grid(cs, cell_m=10)
        assert grid.grid_cols == math.ceil(VENUE_WIDTH_M / 10)
        assert grid.grid_rows == math.ceil(VENUE_HEIGHT_M / 10)

    def test_total_people_close_to_festival_pax(self):
        """total_estimated_people should be close to festival_pax (baseline only test)."""
        cs = self._make_minimal_cluster_states()
        grid = generate_density_grid(cs, cell_m=25, festival_pax=80_000)
        # At least the baseline 80 % of 80k should be distributed
        assert grid.total_estimated_people >= 60_000

    def test_all_cells_non_negative_density(self):
        cs = self._make_minimal_cluster_states()
        grid = generate_density_grid(cs, cell_m=25)
        for cell in grid.cells:
            assert cell.density_pm2 >= 0.0

    def test_hotspots_are_subset_of_cells(self):
        cs = self._make_minimal_cluster_states()
        grid = generate_density_grid(cs, cell_m=10)
        cell_set = {(c.cell_x, c.cell_y) for c in grid.cells}
        for hs in grid.hotspots:
            assert (hs.cell_x, hs.cell_y) in cell_set

    def test_alert_flag_set_for_e_and_f(self):
        cs = self._make_minimal_cluster_states()
        grid = generate_density_grid(cs, cell_m=10)
        for cell in grid.cells:
            if cell.level in (FruinLevel.E, FruinLevel.F):
                assert cell.alert is True
            else:
                assert cell.alert is False
