"""
In-memory application state singleton for PlantaOS × Rock in Rio Lisboa 2026.

This module holds ALL runtime state. There is no external database required.
The state is populated on startup by the simulation engine and updated by:
  - Sensor ingest (POST /sensor)
  - Prosegur camera ingest (POST /prosegur)
  - Simulation ticks (POST /simulate/tick or background task)
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional, Set

from app.data.clusters import CLUSTERS, CLUSTERS_BY_ID
from app.schemas import (
    Alert,
    ClusterState,
    ClusterTipo,
    ProsegurReading,
    SectionState,
    SensorReading,
)


class AppState:
    """
    Singleton holding all mutable runtime state.

    Attributes
    ----------
    cluster_states : dict[str, ClusterState]
        Full state for each cluster, keyed by cluster_id (e.g. "WC-01").
    alerts : list[Alert]
        Currently active alerts (cleared and recalculated each tick).
    sensor_readings : dict[str, SensorReading]
        Most recent sensor reading per cluster, keyed by cluster_id.
    prosegur_readings : dict[str, ProsegurReading]
        Most recent Prosegur camera reading per cluster, keyed by cluster_id.
    daily_redirected : int
        KPI-04 accumulator — daily cumulative people redirected.
    simulation_scenario : str
        Name of the currently active simulation scenario.
    ws_clients : set[asyncio.Queue]
        One asyncio.Queue per connected WebSocket client.
        The WebSocket router pushes payloads into each queue.
    last_tick : float
        Unix timestamp of the last simulation tick.
    """

    def __init__(self) -> None:
        self.cluster_states: Dict[str, ClusterState] = {}
        self.alerts: List[Alert] = []
        self.sensor_readings: Dict[str, SensorReading] = {}
        self.prosegur_readings: Dict[str, ProsegurReading] = {}
        self.daily_redirected: int = 0
        self.simulation_scenario: str = "normal_day"
        self.ws_clients: Set[asyncio.Queue] = set()  # type: ignore[type-arg]
        self.last_tick: float = 0.0
        self._initialised: bool = False

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def initialise(self, scenario: str = "normal_day") -> None:
        """
        Build the initial cluster_states from static metadata.
        Called once on application startup.
        """
        from app.data.clusters import get_sections_for_cluster, get_capacity_for_section

        self.cluster_states = {}
        for cluster in CLUSTERS:
            cid = cluster["id"]
            sections = get_sections_for_cluster(cid)
            secoes: Dict[str, SectionState] = {}
            for sec in sections:
                cap = get_capacity_for_section(cid, sec)
                secoes[sec] = SectionState(
                    ocupacao_pct=0.0,
                    ocupacao_absoluta=0,
                    fila_actual=0,
                    tempo_espera_min=0.0,
                    fluxo_entrada_pmin=0.0,
                    fluxo_saida_pmin=0.0,
                    confianca_pct=100.0,
                    fontes_activas=["IR", "WiFi", "Camera"],
                )

            tipo = ClusterTipo(cluster["tipo"])
            self.cluster_states[cid] = ClusterState(
                cluster_id=cid,
                nome=cluster["nome"],
                tipo=tipo,
                entry_only=cluster["entry_only"],
                lat=cluster["lat"],
                lon=cluster["lon"],
                dist_entrada_m=cluster["dist_entrada_m"],
                secoes=secoes,
                alertas=[],
            )

        self.alerts = []
        self.sensor_readings = {}
        self.prosegur_readings = {}
        self.daily_redirected = 0
        self.simulation_scenario = scenario
        self.last_tick = time.time()
        self._initialised = True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_all_section_states(self) -> List[tuple[str, str, SectionState]]:
        """
        Yield (cluster_id, section_key, SectionState) for every section.
        """
        result = []
        for cid, cs in self.cluster_states.items():
            for sec, ss in cs.secoes.items():
                result.append((cid, sec, ss))
        return result

    def update_section(
        self,
        cluster_id: str,
        section: str,
        state: SectionState,
    ) -> None:
        """Update a single section state and recompute its status."""
        if cluster_id in self.cluster_states:
            updated = state.compute_status()
            self.cluster_states[cluster_id].secoes[section] = updated

    def broadcast(self, payload: Any) -> None:
        """Push a payload dict to all connected WebSocket queues."""
        dead: Set[asyncio.Queue] = set()  # type: ignore[type-arg]
        for q in self.ws_clients:
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                dead.add(q)
        for q in dead:
            self.ws_clients.discard(q)

    def add_ws_client(self) -> "asyncio.Queue[Any]":
        """Register a new WebSocket client; return its queue."""
        q: asyncio.Queue[Any] = asyncio.Queue(maxsize=10)
        self.ws_clients.add(q)
        return q

    def remove_ws_client(self, q: "asyncio.Queue[Any]") -> None:
        """Deregister a WebSocket client."""
        self.ws_clients.discard(q)


# ---------------------------------------------------------------------------
# Module-level singleton — import this everywhere
# ---------------------------------------------------------------------------
app_state = AppState()
