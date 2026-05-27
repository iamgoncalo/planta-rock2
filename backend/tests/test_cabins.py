"""
Tests for the per-cabin Reed switch endpoint.

GET /api/v1/cabins/{cluster_id}

NOTE: The cabins router is tested by importing it directly into a minimal
FastAPI app so that main.py is NOT modified.  The integration line that
must be added to main.py is documented in the track_06 audit report.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI

from app.routers import cabins as cabins_router
from app.state import app_state


# ---------------------------------------------------------------------------
# Test app fixture — minimal FastAPI with only the cabins router mounted.
# This avoids any modification to app/main.py.
# ---------------------------------------------------------------------------

def _make_test_app() -> FastAPI:
    """Build a minimal FastAPI app that includes only the cabins router."""
    from app.config import get_settings
    from app.services.simulation import run_tick
    from app.services.alerts import evaluate_all_clusters
    from collections import defaultdict

    # Ensure app_state is initialised (idempotent)
    if not app_state._initialised:
        settings = get_settings()
        app_state.initialise(scenario=settings.simulation_initial_scenario)
        updated, _ = run_tick(
            cluster_states=app_state.cluster_states,
            scenario_name=settings.simulation_initial_scenario,
            tick=0,
        )
        app_state.cluster_states = updated
        initial_alerts = evaluate_all_clusters(app_state.cluster_states)
        app_state.alerts = initial_alerts
        alerts_by_cluster: dict = defaultdict(list)
        for a in initial_alerts:
            alerts_by_cluster[a.cluster_id].append(a)
        for cid, cs in app_state.cluster_states.items():
            cs.alertas = alerts_by_cluster.get(cid, [])

    test_app = FastAPI()
    test_app.include_router(cabins_router.router, prefix="/api/v1")
    return test_app


@pytest_asyncio.fixture
async def client():
    """Async HTTP client wired to the minimal cabins test app."""
    app = _make_test_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Test 1 — WC-01 returns 200 and the correct cabin count
#          Layout: M = 3+8+3+1=15, F = 2+10+3+1=16  → total 31
# ---------------------------------------------------------------------------

class TestWC01CabinCount:
    async def test_wc01_returns_200(self, client):
        resp = await client.get("/api/v1/cabins/WC-01")
        assert resp.status_code == 200

    async def test_wc01_cabin_count(self, client):
        data = (await client.get("/api/v1/cabins/WC-01")).json()
        assert data["cluster_id"] == "WC-01"
        assert len(data["cabins"]) == 31  # 15 M + 16 F

    async def test_wc01_has_simulado_flag(self, client):
        data = (await client.get("/api/v1/cabins/WC-01")).json()
        assert data["simulado"] is True


# ---------------------------------------------------------------------------
# Test 2 — WC-05 (unissex) only has section "U" cabins
#          Layout: U = 2+20+4+1=27
# ---------------------------------------------------------------------------

class TestWC05Unissex:
    async def test_wc05_returns_200(self, client):
        resp = await client.get("/api/v1/cabins/WC-05")
        assert resp.status_code == 200

    async def test_wc05_only_u_section(self, client):
        data = (await client.get("/api/v1/cabins/WC-05")).json()
        sections = {c["section"] for c in data["cabins"]}
        assert sections == {"U"}, f"Expected only 'U' section, got: {sections}"

    async def test_wc05_cabin_count(self, client):
        data = (await client.get("/api/v1/cabins/WC-05")).json()
        assert len(data["cabins"]) == 27  # 2+20+4+1


# ---------------------------------------------------------------------------
# Test 3 — WC-06 has 34 cabin positions (accessible + standard + wide + end)
#          Layout: U = 3+24+6+1=34 cabins + 6 calha → total 40
#          NOTE: The task specifies 34 "cabin positions" (door-equipped units),
#                but the router counts calha entries too (total 40 in our model).
#                Test matches the router implementation (40) and documents why.
# ---------------------------------------------------------------------------

class TestWC06CabinCount:
    async def test_wc06_returns_200(self, client):
        resp = await client.get("/api/v1/cabins/WC-06")
        assert resp.status_code == 200

    async def test_wc06_cabin_total_matches_layout(self, client):
        """
        WC-06 layout: 3 acc + 24 std + 6 wide + 1 end + 6 calha = 40 total units.
        The task brief states 34 'cabin positions' excluding calha — both are tested.
        """
        data = (await client.get("/api/v1/cabins/WC-06")).json()
        all_cabins = data["cabins"]
        # Enclosed cabin count (no calha)
        enclosed = [c for c in all_cabins if c["type"] != "calha"]
        calha    = [c for c in all_cabins if c["type"] == "calha"]
        assert len(enclosed) == 34, f"Expected 34 enclosed cabin positions, got {len(enclosed)}"
        assert len(calha)    == 6,  f"Expected 6 calha sections, got {len(calha)}"

    async def test_wc06_summary_total_is_40(self, client):
        data = (await client.get("/api/v1/cabins/WC-06")).json()
        assert data["summary"]["total"] == 40


# ---------------------------------------------------------------------------
# Test 4 — WC-99 returns 404
# ---------------------------------------------------------------------------

class TestUnknownCluster:
    async def test_wc99_returns_404(self, client):
        resp = await client.get("/api/v1/cabins/WC-99")
        assert resp.status_code == 404

    async def test_wc99_detail_message(self, client):
        resp = await client.get("/api/v1/cabins/WC-99")
        assert "not found" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Test 5 — Invariant: occupied + free == total for every cluster
# ---------------------------------------------------------------------------

class TestOccupancyInvariant:
    @pytest.mark.parametrize("cid", [
        "WC-01", "WC-02", "WC-03", "WC-04",
        "WC-05", "WC-06", "WC-07", "WC-08",
    ])
    async def test_occupied_plus_free_equals_total(self, client, cid):
        data = (await client.get(f"/api/v1/cabins/{cid}")).json()
        s = data["summary"]
        assert s["occupied"] + s["free"] == s["total"], (
            f"{cid}: occupied({s['occupied']}) + free({s['free']}) "
            f"!= total({s['total']})"
        )


# ---------------------------------------------------------------------------
# Test 6 — (Skipped per task spec — accessibility guarantee not required)
# ---------------------------------------------------------------------------
# The task brief explicitly instructs to remove the "no accessible cabin is
# occupied" test, so it is omitted here.


# ---------------------------------------------------------------------------
# Test 7 — All cabin IDs are unique within a cluster
# ---------------------------------------------------------------------------

class TestCabinIdUniqueness:
    @pytest.mark.parametrize("cid", [
        "WC-01", "WC-02", "WC-03", "WC-04",
        "WC-05", "WC-06", "WC-07", "WC-08",
    ])
    async def test_cabin_ids_unique(self, client, cid):
        data = (await client.get(f"/api/v1/cabins/{cid}")).json()
        ids = [c["id"] for c in data["cabins"]]
        assert len(ids) == len(set(ids)), (
            f"{cid}: duplicate cabin IDs detected — {[i for i in ids if ids.count(i) > 1]}"
        )


# ---------------------------------------------------------------------------
# Test 8 — Response schema completeness
# ---------------------------------------------------------------------------

class TestResponseSchema:
    async def test_required_top_level_fields(self, client):
        data = (await client.get("/api/v1/cabins/WC-03")).json()
        for field in ("cluster_id", "ts", "simulado", "cabins", "anomalies", "summary"):
            assert field in data, f"Missing top-level field: {field}"

    async def test_cabin_fields(self, client):
        data = (await client.get("/api/v1/cabins/WC-03")).json()
        cabin = data["cabins"][0]
        for field in ("id", "type", "section", "occupied", "occupied_since_s", "last_occupied_s_ago"):
            assert field in cabin, f"Missing cabin field: {field}"

    async def test_summary_fields(self, client):
        data = (await client.get("/api/v1/cabins/WC-03")).json()
        s = data["summary"]
        for field in ("total", "occupied", "free", "accessible_free",
                      "avg_occupation_time_s", "longest_occupation_s"):
            assert field in s, f"Missing summary field: {field}"

    async def test_ts_is_integer(self, client):
        data = (await client.get("/api/v1/cabins/WC-01")).json()
        assert isinstance(data["ts"], int)

    async def test_anomaly_fields_when_present(self, client):
        """If anomalies exist they must carry the correct fields."""
        for cid in ("WC-01", "WC-02", "WC-03", "WC-04",
                    "WC-05", "WC-06", "WC-07", "WC-08"):
            data = (await client.get(f"/api/v1/cabins/{cid}")).json()
            for a in data["anomalies"]:
                for f in ("cabin_id", "type", "duration_s", "message"):
                    assert f in a, f"Anomaly missing field '{f}' in {cid}"
