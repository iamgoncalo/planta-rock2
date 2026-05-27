"""
Deterministic simulation engine for PlantaOS × Rock in Rio Lisboa 2026.

The engine drives realistic WC cluster occupancy for the four festival days.
It uses seeded random to ensure reproducibility:
    seed = hash(cluster_id + section + str(hour_of_day)) & 0xFFFFFFFF

State transitions are governed by:
  1. Time of day (festival hours: 14:00–00:00)
  2. Currently active show (headliner start / end surge)
  3. The active scenario modifier

15 Supported scenarios
-----------------------
normal_day            : baseline festival operation
headliner_start       : headliner just started, crowd surges to WCs
headliner_end_surge   : headliner ended, mass egress to WCs
wc05_overcrowded      : WC-05 near capacity
wc06_relief           : WC-06 absorbing overflow, elevated but not critical
sensor_ir_offline     : IR sensors offline on all clusters (confidence drops)
wifi_offline          : WiFi probes offline (confidence drops)
camera_offline        : Prosegur cameras offline (confidence drops)
all_sensors_degraded  : all sensor types degraded simultaneously
prosegur_disagreement : Camera disagrees strongly with IR/WiFi
entry_only_pressure   : WC-05 (entry only) under extreme pressure
rain_surge            : sudden rain drives everyone to covered WCs
crowd_surge           : general crowd surge across all clusters
network_dropout       : all sensors go offline briefly
recovery_after_redirect : occupancy normalising post-redirect
"""
from __future__ import annotations

import datetime
import math
import random
import time
from typing import Any, Dict, List, Optional, Tuple

from app.data.clusters import (
    CLUSTERS,
    CLUSTERS_BY_ID,
    get_capacity_for_section,
    get_sections_for_cluster,
)
from app.schemas import SectionState, SectionStatus

# ---------------------------------------------------------------------------
# Scenario definitions
# Each entry: (occupancy_multiplier, queue_multiplier, confidence_modifier)
# Modifiers are additive adjustments on top of the base time-of-day values.
# ---------------------------------------------------------------------------
SCENARIOS: Dict[str, Dict[str, Any]] = {
    "normal_day": {
        "occ_mult": 1.0,
        "queue_mult": 1.0,
        "conf_mod": 0.0,
        "description": "Operação normal do festival.",
    },
    "headliner_start": {
        "occ_mult": 1.45,
        "queue_mult": 2.5,
        "conf_mod": -5.0,
        "description": "Headliner acabou de começar — afluência elevada.",
    },
    "headliner_end_surge": {
        "occ_mult": 1.6,
        "queue_mult": 3.2,
        "conf_mod": -5.0,
        "description": "Fim do headliner — pico de saída em massa.",
    },
    "wc05_overcrowded": {
        "occ_mult": 1.0,
        "queue_mult": 1.0,
        "conf_mod": 0.0,
        "cluster_overrides": {
            "WC-05": {"occ_mult": 1.9, "queue_mult": 4.0},
        },
        "description": "WC-05 (ENTRY ONLY) perto da capacidade máxima.",
    },
    "wc06_relief": {
        "occ_mult": 1.0,
        "queue_mult": 1.0,
        "conf_mod": 0.0,
        "cluster_overrides": {
            "WC-06": {"occ_mult": 1.4, "queue_mult": 2.0},
        },
        "description": "WC-06 a absorver excesso de outros clusters.",
    },
    "sensor_ir_offline": {
        "occ_mult": 1.0,
        "queue_mult": 1.0,
        "conf_mod": -30.0,
        "sources_offline": ["IR"],
        "description": "Sensores IR offline — confiança reduzida.",
    },
    "wifi_offline": {
        "occ_mult": 1.0,
        "queue_mult": 1.0,
        "conf_mod": -20.0,
        "sources_offline": ["WiFi"],
        "description": "Sondas WiFi offline — confiança reduzida.",
    },
    "camera_offline": {
        "occ_mult": 1.0,
        "queue_mult": 1.0,
        "conf_mod": -10.0,
        "sources_offline": ["Camera"],
        "description": "Câmaras Prosegur offline — confiança reduzida.",
    },
    "all_sensors_degraded": {
        "occ_mult": 1.0,
        "queue_mult": 1.0,
        "conf_mod": -55.0,
        "sources_offline": ["IR", "WiFi", "Camera"],
        "description": "Todos os sensores degradados.",
    },
    "prosegur_disagreement": {
        "occ_mult": 1.0,
        "queue_mult": 1.0,
        "conf_mod": -15.0,
        "description": "Câmara discorda dos sensores IR/WiFi — fusão incerta.",
    },
    "entry_only_pressure": {
        "occ_mult": 1.1,
        "queue_mult": 1.5,
        "conf_mod": 0.0,
        "cluster_overrides": {
            "WC-05": {"occ_mult": 1.95, "queue_mult": 5.0},
        },
        "description": "WC-05 (ENTRY ONLY) sob pressão extrema.",
    },
    "rain_surge": {
        "occ_mult": 1.35,
        "queue_mult": 2.0,
        "conf_mod": -8.0,
        "description": "Chuva repentina — afluência a WCs cobertos.",
    },
    "crowd_surge": {
        "occ_mult": 1.5,
        "queue_mult": 2.8,
        "conf_mod": -5.0,
        "description": "Pico geral de afluência.",
    },
    "network_dropout": {
        "occ_mult": 1.0,
        "queue_mult": 1.0,
        "conf_mod": -70.0,
        "sources_offline": ["IR", "WiFi", "Camera"],
        "description": "Falha de rede — todos os sensores offline.",
    },
    "recovery_after_redirect": {
        "occ_mult": 0.65,
        "queue_mult": 0.4,
        "conf_mod": 5.0,
        "description": "Recuperação após redirecionamento — ocupação a normalizar.",
    },
}

VALID_SCENARIOS = list(SCENARIOS.keys())

# ---------------------------------------------------------------------------
# Time-of-day base occupancy curve (hour -> base occupancy %)
# Festival is 14:00–00:00.  Outside hours = very low.
# ---------------------------------------------------------------------------
_HOUR_OCCUPANCY: Dict[int, float] = {
    0: 15.0,   # midnight — winding down
    1: 5.0,
    2: 2.0,
    3: 2.0,
    4: 2.0,
    5: 2.0,
    6: 2.0,
    7: 2.0,
    8: 2.0,
    9: 5.0,
    10: 8.0,
    11: 10.0,
    12: 12.0,
    13: 20.0,
    14: 35.0,  # gates open
    15: 45.0,
    16: 52.0,
    17: 58.0,
    18: 65.0,
    19: 70.0,
    20: 72.0,
    21: 78.0,  # headliner build-up
    22: 85.0,  # headliner peak
    23: 62.0,  # post-headliner flush
}


def _base_occupancy(hour: int) -> float:
    return _HOUR_OCCUPANCY.get(hour % 24, 30.0)


def _cluster_section_seed(cluster_id: str, section: str, hour: int) -> int:
    """Deterministic seed from cluster + section + hour."""
    raw = f"{cluster_id}{section}{hour}"
    return hash(raw) & 0xFFFFFFFF


def _noise(seed: int, tick: int, amplitude: float = 0.05) -> float:
    """
    Return a small deterministic noise value in [-amplitude, +amplitude].
    Uses the sine of a hash-derived phase, ensuring smooth variation.
    """
    rng = random.Random(seed ^ (tick * 0x9E3779B9))
    return rng.uniform(-amplitude, amplitude)


def _compute_section_state(
    cluster_id: str,
    section: str,
    base_occ: float,
    occ_mult: float,
    queue_mult: float,
    conf_mod: float,
    sources_offline: List[str],
    tick: int,
    capacity: int,
) -> SectionState:
    """
    Compute SectionState for one section given scenario parameters.
    """
    hour = datetime.datetime.now().hour
    if hour < 14:
        hour = 20  # outside festival hours → default to lively demo hour
    seed = _cluster_section_seed(cluster_id, section, hour)

    # Base occupancy with scenario multiplier and small noise
    occ_pct = base_occ * occ_mult
    occ_pct += _noise(seed, tick) * 100.0  # ±5% of full scale
    occ_pct = max(0.0, min(100.0, occ_pct))

    # Absolute count from percentage
    occ_abs = int(round(occ_pct * capacity / 100.0))

    # Flow rates — proportional to occupancy (must be computed before queue wait)
    fluxo_entrada = max(0.0, occ_pct * 0.25 + _noise(seed ^ 0x2, tick) * 20)
    fluxo_saida = max(0.0, fluxo_entrada * 0.9 + _noise(seed ^ 0x3, tick) * 5)

    # Queue: proportional to how full the section is, scaled by scenario
    base_queue = max(0.0, (occ_pct - 60.0) * 0.8)  # queue starts above 60%
    fila = int(round(base_queue * queue_mult + _noise(seed ^ 0x1, tick) * 10))
    fila = max(0, fila)

    # Wait time: L/λ (Little's Law) — uses inflow as throughput proxy
    tempo_espera = fila / fluxo_entrada if (fila > 0 and fluxo_entrada > 0) else 0.0

    # Confidence — affected by scenario and offline sources
    all_sources = ["IR", "WiFi", "Camera"]
    active_sources = [s for s in all_sources if s not in sources_offline]
    base_conf = 100.0 - (len(sources_offline) * 20.0)
    conf_pct = max(0.0, min(100.0, base_conf + conf_mod))

    # Determine status
    if occ_pct >= 90:
        status = SectionStatus.CRITICO
    elif occ_pct >= 75:
        status = SectionStatus.CHEIO
    elif occ_pct >= 50:
        status = SectionStatus.MODERADO
    else:
        status = SectionStatus.LIVRE

    return SectionState(
        ocupacao_pct=round(occ_pct, 1),
        ocupacao_absoluta=occ_abs,
        fila_actual=fila,
        tempo_espera_min=round(tempo_espera, 1),
        fluxo_entrada_pmin=round(fluxo_entrada, 1),
        fluxo_saida_pmin=round(fluxo_saida, 1),
        status=status,
        confianca_pct=round(conf_pct, 1),
        fontes_activas=active_sources,
    )


def run_tick(
    cluster_states: dict,
    scenario_name: str,
    tick: int,
    hora_simulada: Optional[str] = None,
) -> Tuple[dict, int]:
    """
    Advance simulation by one tick.

    Parameters
    ----------
    cluster_states : dict[str, ClusterState]
        Current state, will be mutated in place.
    scenario_name : str
        Active scenario name from VALID_SCENARIOS.
    tick : int
        Monotonically increasing tick counter (used for noise seeding).
    hora_simulada : str | None
        Optional override for current hour as "HH:MM".

    Returns
    -------
    (updated_cluster_states, clusters_updated_count)
    """
    if hora_simulada:
        h, m = map(int, hora_simulada.split(":"))
    else:
        now = datetime.datetime.now()
        h = now.hour
        # Outside festival hours (14:00–00:00): use a lively demo hour
        if h < 14:
            h = 20  # 8 PM — typical busy headliner build-up hour

    scenario = SCENARIOS.get(scenario_name, SCENARIOS["normal_day"])
    global_occ_mult = scenario.get("occ_mult", 1.0)
    global_queue_mult = scenario.get("queue_mult", 1.0)
    global_conf_mod = scenario.get("conf_mod", 0.0)
    sources_offline = scenario.get("sources_offline", [])
    cluster_overrides = scenario.get("cluster_overrides", {})

    base_occ = _base_occupancy(h)
    clusters_updated = 0

    for cluster_id, cs in cluster_states.items():
        override = cluster_overrides.get(cluster_id, {})
        occ_mult = override.get("occ_mult", global_occ_mult)
        queue_mult = override.get("queue_mult", global_queue_mult)
        conf_mod = override.get("conf_mod", global_conf_mod)

        sections = get_sections_for_cluster(cluster_id)
        new_secoes = {}
        for section in sections:
            capacity = get_capacity_for_section(cluster_id, section)
            if capacity <= 0:
                capacity = 100  # fallback

            state = _compute_section_state(
                cluster_id=cluster_id,
                section=section,
                base_occ=base_occ,
                occ_mult=occ_mult,
                queue_mult=queue_mult,
                conf_mod=conf_mod,
                sources_offline=sources_offline,
                tick=tick,
                capacity=capacity,
            )
            new_secoes[section] = state

        cs.secoes = new_secoes
        cluster_states[cluster_id] = cs
        clusters_updated += 1

    return cluster_states, clusters_updated
