"""
WebSocket router — WS /api/v1/ws

Behaviour:
- On client connect: immediately send full state snapshot.
- Background task: broadcast updated state every 5 seconds to all clients.
- On disconnect: client is removed from the broadcast set.
- Auto-reconnect is handled by the frontend.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.alerts import evaluate_all_clusters
from app.services.kpis import calculate_all_kpis
from app.services.routing import get_routing_recommendations
from app.state import app_state

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


def _build_ws_payload() -> Dict[str, Any]:
    """Build the full state snapshot for WebSocket broadcast."""
    from app.routers.clusters import _serialise_cluster

    clusters_out = []
    for cid in sorted(app_state.cluster_states.keys()):
        cs = app_state.cluster_states[cid]
        clusters_out.append(_serialise_cluster(cs))

    kpis = calculate_all_kpis(
        cluster_states=app_state.cluster_states,
        alerts=app_state.alerts,
        daily_redirected=app_state.daily_redirected,
    )

    routing_recs = get_routing_recommendations(app_state.cluster_states)

    return {
        "type": "cluster_update",
        "ts": time.time(),
        "clusters": clusters_out,
        "kpis": kpis.model_dump(),
        "alertas_activos": len(app_state.alerts),
        "show_activo": kpis.show_activo,
        "minutos_para_headliner": kpis.minutos_para_headliner,
        "routing_recommendations": [r.model_dump() for r in routing_recs],
    }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint.  Sends full state on connect, then broadcasts
    every 5 seconds.
    """
    await websocket.accept()
    queue = app_state.add_ws_client()
    logger.info("WebSocket client connected. Total clients: %d", len(app_state.ws_clients))

    try:
        # Send immediate snapshot on connect
        payload = _build_ws_payload()
        await websocket.send_text(json.dumps(payload, default=str))

        while True:
            # Wait for a queued broadcast or a client message (for keep-alive)
            try:
                queued = await asyncio.wait_for(queue.get(), timeout=1.0)
                await websocket.send_text(json.dumps(queued, default=str))
            except asyncio.TimeoutError:
                # Check if client sent anything (ping/pong)
                try:
                    _ = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                except asyncio.TimeoutError:
                    pass
                except WebSocketDisconnect:
                    break

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as exc:
        logger.warning("WebSocket error: %s", exc)
    finally:
        app_state.remove_ws_client(queue)
        logger.info("WebSocket client removed. Total clients: %d", len(app_state.ws_clients))


async def broadcast_loop() -> None:
    """
    Background task: broadcast full state to all connected WebSocket clients
    every 5 seconds.  Runs for the lifetime of the application.
    """
    from app.config import get_settings
    settings = get_settings()
    interval = settings.simulation_tick_interval_seconds

    while True:
        await asyncio.sleep(interval)
        if app_state.ws_clients:
            try:
                payload = _build_ws_payload()
                app_state.broadcast(payload)
            except Exception as exc:
                logger.warning("broadcast_loop error: %s", exc)
