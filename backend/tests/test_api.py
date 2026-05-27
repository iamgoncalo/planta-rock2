"""
Integration tests for the FastAPI endpoints.

Uses httpx.AsyncClient with the ASGI transport to test the full
request/response cycle without a live server.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client():
    """Async HTTP client connected to the FastAPI app (with lifespan running)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        # Manually trigger lifespan startup so in-memory state is initialised
        from app.state import app_state
        if not app_state._initialised:
            from app.config import get_settings
            from app.services.alerts import evaluate_all_clusters
            from app.services.simulation import run_tick
            from collections import defaultdict

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
        yield ac


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class TestHealth:
    async def test_get_health_returns_200(self, client):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200

    async def test_health_body(self, client):
        resp = await client.get("/api/v1/health")
        data = resp.json()
        assert data["status"] == "ok"
        assert "ts" in data
        assert "version" in data

    async def test_health_version_is_string(self, client):
        resp = await client.get("/api/v1/health")
        assert isinstance(resp.json()["version"], str)


# ---------------------------------------------------------------------------
# Clusters
# ---------------------------------------------------------------------------

class TestClusters:
    async def test_get_clusters_returns_200(self, client):
        resp = await client.get("/api/v1/clusters")
        assert resp.status_code == 200

    async def test_get_clusters_returns_8(self, client):
        resp = await client.get("/api/v1/clusters")
        data = resp.json()
        assert "clusters" in data
        assert len(data["clusters"]) == 8

    async def test_clusters_have_required_fields(self, client):
        resp = await client.get("/api/v1/clusters")
        for c in resp.json()["clusters"]:
            assert "cluster_id" in c
            assert "nome" in c
            assert "tipo" in c
            assert "entry_only" in c
            assert "secoes" in c
            assert "lat" in c
            assert "lon" in c

    async def test_wc05_has_only_u_section(self, client):
        resp = await client.get("/api/v1/clusters")
        clusters = {c["cluster_id"]: c for c in resp.json()["clusters"]}
        wc05 = clusters["WC-05"]
        assert set(wc05["secoes"].keys()) == {"U"}

    async def test_wc06_has_only_u_section(self, client):
        resp = await client.get("/api/v1/clusters")
        clusters = {c["cluster_id"]: c for c in resp.json()["clusters"]}
        wc06 = clusters["WC-06"]
        assert set(wc06["secoes"].keys()) == {"U"}

    async def test_wc01_has_m_and_f_sections(self, client):
        resp = await client.get("/api/v1/clusters")
        clusters = {c["cluster_id"]: c for c in resp.json()["clusters"]}
        wc01 = clusters["WC-01"]
        assert "M" in wc01["secoes"]
        assert "F" in wc01["secoes"]
        assert "U" not in wc01["secoes"]

    async def test_clusters_have_ts(self, client):
        resp = await client.get("/api/v1/clusters")
        assert "ts" in resp.json()

    async def test_section_fields_present(self, client):
        resp = await client.get("/api/v1/clusters")
        clusters = {c["cluster_id"]: c for c in resp.json()["clusters"]}
        wc01_m = clusters["WC-01"]["secoes"]["M"]
        for field in [
            "ocupacao_pct", "ocupacao_absoluta", "fila_actual",
            "tempo_espera_min", "fluxo_entrada_pmin", "fluxo_saida_pmin",
            "status", "confianca_pct", "fontes_activas",
        ]:
            assert field in wc01_m, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------

class TestKPIs:
    async def test_get_kpis_returns_200(self, client):
        resp = await client.get("/api/v1/kpis")
        assert resp.status_code == 200

    async def test_kpis_has_all_four(self, client):
        resp = await client.get("/api/v1/kpis")
        data = resp.json()
        assert "kpi_01" in data
        assert "kpi_02" in data
        assert "kpi_03" in data
        assert "kpi_04" in data

    async def test_kpi_01_in_range(self, client):
        data = (await client.get("/api/v1/kpis")).json()
        assert 0 <= data["kpi_01"] <= 100

    async def test_kpi_02_in_range(self, client):
        data = (await client.get("/api/v1/kpis")).json()
        assert 0 <= data["kpi_02"] <= 100

    async def test_kpi_03_non_negative(self, client):
        data = (await client.get("/api/v1/kpis")).json()
        assert data["kpi_03"] >= 0

    async def test_kpi_04_non_negative(self, client):
        data = (await client.get("/api/v1/kpis")).json()
        assert data["kpi_04"] >= 0


# ---------------------------------------------------------------------------
# Shows
# ---------------------------------------------------------------------------

class TestShows:
    async def test_get_shows_returns_200(self, client):
        resp = await client.get("/api/v1/shows")
        assert resp.status_code == 200

    async def test_shows_is_list(self, client):
        resp = await client.get("/api/v1/shows")
        data = resp.json()
        assert "shows" in data
        assert isinstance(data["shows"], list)

    async def test_shows_has_all_four_days(self, client):
        resp = await client.get("/api/v1/shows")
        days = {s["dia"] for s in resp.json()["shows"]}
        assert days == {1, 2, 3, 4}

    async def test_shows_filter_by_day(self, client):
        resp = await client.get("/api/v1/shows?dia=1")
        shows = resp.json()["shows"]
        assert all(s["dia"] == 1 for s in shows)

    async def test_headliners_only_filter(self, client):
        resp = await client.get("/api/v1/shows?headliners_only=true")
        shows = resp.json()["shows"]
        assert all(s["headliner"] for s in shows)

    async def test_shows_include_katy_perry(self, client):
        resp = await client.get("/api/v1/shows")
        artistas = [s["artista"] for s in resp.json()["shows"]]
        assert "Katy Perry" in artistas

    async def test_shows_include_linkin_park(self, client):
        resp = await client.get("/api/v1/shows")
        artistas = [s["artista"] for s in resp.json()["shows"]]
        assert "Linkin Park" in artistas

    async def test_show_entries_have_required_fields(self, client):
        resp = await client.get("/api/v1/shows")
        for s in resp.json()["shows"]:
            for field in ["dia", "data", "artista", "inicio", "fim", "headliner", "activo", "proximo"]:
                assert field in s, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# Sensor ingest
# ---------------------------------------------------------------------------

class TestSensorIngest:
    async def test_post_sensor_valid_returns_200(self, client):
        payload = {
            "cluster_id": "WC-01",
            "section": "M",
            "source": "IR",
            "contagem_entrada": 10,
            "contagem_saida": 5,
        }
        resp = await client.post("/api/v1/sensor", json=payload)
        assert resp.status_code == 200

    async def test_post_sensor_response_has_ok(self, client):
        payload = {
            "cluster_id": "WC-01",
            "section": "M",
            "source": "IR",
            "contagem_entrada": 5,
            "contagem_saida": 2,
        }
        resp = await client.post("/api/v1/sensor", json=payload)
        assert resp.json()["ok"] is True

    async def test_post_sensor_wifi_source(self, client):
        payload = {
            "cluster_id": "WC-02",
            "section": "F",
            "source": "WiFi",
            "contagem_entrada": 3,
            "contagem_saida": 1,
        }
        resp = await client.post("/api/v1/sensor", json=payload)
        assert resp.status_code == 200

    async def test_post_sensor_wc05_unisex_u(self, client):
        """WC-05 must accept section 'U'."""
        payload = {
            "cluster_id": "WC-05",
            "section": "U",
            "source": "IR",
            "contagem_entrada": 10,
            "contagem_saida": 8,
        }
        resp = await client.post("/api/v1/sensor", json=payload)
        assert resp.status_code == 200

    async def test_post_sensor_wc05_rejects_m(self, client):
        """WC-05 must reject section 'M' (it's unisex)."""
        payload = {
            "cluster_id": "WC-05",
            "section": "M",
            "source": "IR",
            "contagem_entrada": 10,
            "contagem_saida": 8,
        }
        resp = await client.post("/api/v1/sensor", json=payload)
        assert resp.status_code == 422

    async def test_post_sensor_invalid_cluster_returns_422(self, client):
        payload = {
            "cluster_id": "WC-99",
            "section": "M",
            "source": "IR",
            "contagem_entrada": 0,
            "contagem_saida": 0,
        }
        resp = await client.post("/api/v1/sensor", json=payload)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Prosegur ingest
# ---------------------------------------------------------------------------

class TestProsegurIngest:
    async def test_post_prosegur_valid_returns_200(self, client):
        payload = {
            "cluster_id": "WC-01",
            "section": "M",
            "ocupacao_absoluta": 45,
            "fila_actual": 8,
            "confianca_ml": 0.92,
        }
        resp = await client.post("/api/v1/prosegur", json=payload)
        assert resp.status_code == 200

    async def test_post_prosegur_wc06_unisex(self, client):
        payload = {
            "cluster_id": "WC-06",
            "section": "U",
            "ocupacao_absoluta": 100,
            "fila_actual": 15,
            "confianca_ml": 0.88,
        }
        resp = await client.post("/api/v1/prosegur", json=payload)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

class TestSimulation:
    async def test_post_simulate_tick_returns_200(self, client):
        resp = await client.post("/api/v1/simulate/tick")
        assert resp.status_code == 200

    async def test_simulate_tick_response_fields(self, client):
        resp = await client.post("/api/v1/simulate/tick")
        data = resp.json()
        assert "ts" in data
        assert "scenario" in data
        assert "clusters_updated" in data
        assert "alerts_generated" in data

    async def test_simulate_tick_with_scenario(self, client):
        resp = await client.post("/api/v1/simulate/tick", json={"scenario": "headliner_start"})
        assert resp.status_code == 200
        assert resp.json()["scenario"] == "headliner_start"

    async def test_simulate_tick_invalid_scenario(self, client):
        resp = await client.post("/api/v1/simulate/tick", json={"scenario": "nonexistent_scenario"})
        assert resp.status_code == 422

    async def test_simulate_tick_updates_8_clusters(self, client):
        resp = await client.post("/api/v1/simulate/tick")
        assert resp.json()["clusters_updated"] == 8

    async def test_simulate_tick_with_hora_simulada(self, client):
        resp = await client.post(
            "/api/v1/simulate/tick",
            json={"scenario": "normal_day", "hora_simulada": "21:00"},
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class TestChat:
    async def test_post_chat_returns_200(self, client):
        resp = await client.post(
            "/api/v1/chat",
            json={"mensagem": "Qual é o WC mais livre?"},
        )
        assert resp.status_code == 200

    async def test_chat_response_has_resposta(self, client):
        resp = await client.post(
            "/api/v1/chat",
            json={"mensagem": "Qual é o WC mais livre?"},
        )
        data = resp.json()
        assert "resposta" in data
        assert isinstance(data["resposta"], str)
        assert len(data["resposta"]) > 0

    async def test_chat_response_has_fonte(self, client):
        resp = await client.post(
            "/api/v1/chat",
            json={"mensagem": "test"},
        )
        data = resp.json()
        assert "fonte" in data
        assert data["fonte"] in ("gemini", "local")

    async def test_chat_fonte_is_local_without_key(self, client):
        """Without GEMINI_API_KEY, fonte must be 'local'."""
        from app.config import get_settings
        settings = get_settings()
        if not settings.gemini_enabled:
            resp = await client.post(
                "/api/v1/chat",
                json={"mensagem": "alertas críticos"},
            )
            assert resp.json()["fonte"] == "local"

    async def test_chat_with_history(self, client):
        resp = await client.post(
            "/api/v1/chat",
            json={
                "mensagem": "E os alertas?",
                "historico": [
                    {"role": "user", "content": "Qual é o WC mais livre?"},
                    {"role": "assistant", "content": "O WC mais livre é WC-08."},
                ],
            },
        )
        assert resp.status_code == 200
        assert len(resp.json()["resposta"]) > 0

    async def test_chat_active_show(self, client):
        resp = await client.post(
            "/api/v1/chat",
            json={"mensagem": "show activo"},
        )
        assert resp.status_code == 200

    async def test_chat_redirect_wc05(self, client):
        resp = await client.post(
            "/api/v1/chat",
            json={"mensagem": "redirecionar de wc-05"},
        )
        assert resp.status_code == 200
