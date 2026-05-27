"""
PlantaOS × Rock in Rio Lisboa 2026 — FastAPI Backend

Entry point. Run with:
    uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routers import (
    cabins,
    chat,
    clusters,
    density,
    health,
    ingest,
    kpis,
    maintenance,
    ops,
    prosegur,
    shows,
    simulate,
    websocket as ws_router,
)
from app.services.alerts import evaluate_all_clusters
from app.services.simulation import run_tick
from app.state import app_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    settings = get_settings()
    logger.info("PlantaOS backend starting up…")

    # Initialise in-memory state from static cluster data
    app_state.initialise(scenario=settings.simulation_initial_scenario)
    logger.info("State initialised with scenario: %s", settings.simulation_initial_scenario)

    # Run one initial simulation tick so state has realistic values from the start
    updated, _ = run_tick(
        cluster_states=app_state.cluster_states,
        scenario_name=settings.simulation_initial_scenario,
        tick=0,
    )
    app_state.cluster_states = updated

    # Compute initial alerts (no sensor readings yet at startup — empty timestamps)
    initial_alerts = evaluate_all_clusters(app_state.cluster_states, sensor_timestamps={})
    app_state.alerts = initial_alerts

    # Attach per-cluster alerts
    from collections import defaultdict
    alerts_by_cluster = defaultdict(list)
    for a in initial_alerts:
        alerts_by_cluster[a.cluster_id].append(a)
    for cid, cs in app_state.cluster_states.items():
        cs.alertas = alerts_by_cluster.get(cid, [])

    logger.info("Initial tick complete. Alerts: %d", len(initial_alerts))

    # Start background tasks
    broadcast_task = asyncio.create_task(ws_router.broadcast_loop())
    sim_task = asyncio.create_task(_simulation_loop())

    logger.info("PlantaOS backend ready.")

    yield

    # Shutdown
    broadcast_task.cancel()
    sim_task.cancel()
    try:
        await broadcast_task
    except asyncio.CancelledError:
        pass
    try:
        await sim_task
    except asyncio.CancelledError:
        pass

    logger.info("PlantaOS backend shut down.")


async def _simulation_loop() -> None:
    """Background simulation: run a tick every N seconds."""
    from app.config import get_settings
    from app.services.simulation import run_tick
    from app.services.alerts import evaluate_all_clusters
    from app.schemas import AlertSeveridade
    from collections import defaultdict

    settings = get_settings()
    tick = 1

    while True:
        await asyncio.sleep(settings.simulation_tick_interval_seconds)
        try:
            updated, _ = run_tick(
                cluster_states=app_state.cluster_states,
                scenario_name=app_state.simulation_scenario,
                tick=tick,
            )
            app_state.cluster_states = updated

            sensor_timestamps = {k: v.ts for k, v in app_state.sensor_readings.items()}
            new_alerts = evaluate_all_clusters(app_state.cluster_states, sensor_timestamps=sensor_timestamps)
            app_state.alerts = new_alerts

            alerts_by_cluster: dict = defaultdict(list)
            for a in new_alerts:
                alerts_by_cluster[a.cluster_id].append(a)
            for cid, cs in app_state.cluster_states.items():
                cs.alertas = alerts_by_cluster.get(cid, [])

            critico_count = sum(
                1 for a in new_alerts
                if a.severidade == AlertSeveridade.CRITICO
            )
            app_state.daily_redirected += critico_count * 5
            tick += 1
        except Exception as exc:
            logger.warning("Simulation loop error: %s", exc)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="PlantaOS × Rock in Rio Lisboa 2026",
        description=(
            "Real-time WC crowd management backend for Rock in Rio Lisboa 2026. "
            "Counts people, not CO2."
        ),
        version=settings.app_version,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API v1 routers
    prefix = "/api/v1"
    app.include_router(health.router, prefix=prefix)
    app.include_router(clusters.router, prefix=prefix)
    app.include_router(kpis.router, prefix=prefix)
    app.include_router(shows.router, prefix=prefix)
    app.include_router(ingest.router, prefix=prefix)
    app.include_router(prosegur.router, prefix=prefix)
    app.include_router(simulate.router, prefix=prefix)
    app.include_router(chat.router, prefix=prefix)
    app.include_router(ops.router, prefix=prefix)
    app.include_router(cabins.router, prefix=prefix)
    app.include_router(density.router, prefix=prefix)
    app.include_router(maintenance.api_router, prefix=prefix)
    app.include_router(ws_router.router, prefix=prefix)
    # /manutencao page (no api/v1 prefix)
    app.include_router(maintenance.router)

    # Serve the dashboard HTML at /
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        dashboard = static_dir / "index.html"

        @app.get("/", include_in_schema=False)
        async def serve_dashboard() -> FileResponse:
            return FileResponse(str(dashboard), media_type="text/html")

        # Also mount any other static assets that may be added later
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    return app


app = create_app()
