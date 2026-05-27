"""
Static cluster metadata for the 8 WC clusters at Rock in Rio Lisboa 2026.

RULES:
- WC-05 and WC-06 are UNISEX ONLY (tipo="unissex") — never M/F split.
- WC-01,02,03,04,07,08 are MIXED (tipo="misto") — have M and F sections.
- GPS coordinates are static metadata only, NOT in telemetry payloads.
- No individual tracking — only aggregated counts.
"""
from __future__ import annotations

from typing import Dict, List, Any

CLUSTERS: List[Dict[str, Any]] = [
    {
        "id": "WC-01",
        "nome": "V34 — Near P1",
        "tipo": "misto",
        "entry_only": False,
        "lat": 38.78230,
        "lon": -9.09371,
        "elevacao_m": 0,
        "capacidade_m": 72,
        "capacidade_f": 63,
        "capacidade_unissex": 0,
        "dist_entrada_m": 220,
        "zona": "Near P1",
        "notas": "",
    },
    {
        "id": "WC-02",
        "nome": "V35 — Female Dominant",
        "tipo": "misto",
        "entry_only": False,
        "lat": 38.78193,
        "lon": -9.09323,
        "elevacao_m": 0,
        "capacidade_m": 54,
        "capacidade_f": 72,
        "capacidade_unissex": 0,
        "dist_entrada_m": 180,
        "zona": "V35",
        "notas": "",
    },
    {
        "id": "WC-03",
        "nome": "S36 — Entrada Principal",
        "tipo": "misto",
        "entry_only": False,
        "lat": 38.78111,
        "lon": -9.09310,
        "elevacao_m": 0,
        "capacidade_m": 54,
        "capacidade_f": 48,
        "capacidade_unissex": 0,
        "dist_entrada_m": 33,
        "zona": "Entrada Principal",
        "notas": "",
    },
    {
        "id": "WC-04",
        "nome": "S37 — Summit +20m",
        "tipo": "misto",
        "entry_only": False,
        "lat": 38.78195,
        "lon": -9.09275,
        "elevacao_m": 20,
        "capacidade_m": 84,
        "capacidade_f": 66,
        "capacidade_unissex": 0,
        "dist_entrada_m": 95,
        "zona": "Summit",
        "notas": "",
    },
    {
        "id": "WC-05",
        "nome": "M38 — ENTRY ONLY",
        "tipo": "unissex",
        "entry_only": True,
        "lat": 38.78150,
        "lon": -9.09303,
        "elevacao_m": 0,
        "capacidade_m": 0,
        "capacidade_f": 0,
        "capacidade_unissex": 133,
        "dist_entrada_m": 45,
        "zona": "M38",
        "notas": "ENTRY ONLY · sem saídas emergência",
    },
    {
        "id": "WC-06",
        "nome": "W39/S39 — Maior cluster",
        "tipo": "unissex",
        "entry_only": False,
        "lat": 38.78010,
        "lon": -9.09549,
        "elevacao_m": 0,
        "capacidade_m": 0,
        "capacidade_f": 0,
        "capacidade_unissex": 208,
        "dist_entrada_m": 267,
        "zona": "W39/S39",
        "notas": "Maior cluster",
    },
    {
        "id": "WC-07",
        "nome": "M40 — Lockers",
        "tipo": "misto",
        "entry_only": False,
        "lat": 38.78069,
        "lon": -9.09356,
        "elevacao_m": 0,
        "capacidade_m": 84,
        "capacidade_f": 54,
        "capacidade_unissex": 0,
        "dist_entrada_m": 310,
        "zona": "M40 Lockers",
        "notas": "",
    },
    {
        "id": "WC-08",
        "nome": "V41 — Produção",
        "tipo": "misto",
        "entry_only": False,
        "lat": 38.77936,
        "lon": -9.09619,
        "elevacao_m": 0,
        "capacidade_m": 84,
        "capacidade_f": 61,
        "capacidade_unissex": 0,
        "dist_entrada_m": 420,
        "zona": "V41 Produção",
        "notas": "",
    },
]

# Index by cluster ID for fast lookup
CLUSTERS_BY_ID: Dict[str, Dict[str, Any]] = {c["id"]: c for c in CLUSTERS}

# IDs of unisex clusters
UNISEX_CLUSTER_IDS = {"WC-05", "WC-06"}

# IDs of mixed (misto) clusters
MISTO_CLUSTER_IDS = {"WC-01", "WC-02", "WC-03", "WC-04", "WC-07", "WC-08"}

# Entry-only clusters (cannot be recommended as relief destination)
ENTRY_ONLY_CLUSTER_IDS = {"WC-05"}


def get_sections_for_cluster(cluster_id: str) -> List[str]:
    """
    Return the section keys for a given cluster.
    Unisex clusters return ["U"], mixed clusters return ["M", "F"].
    """
    if cluster_id in UNISEX_CLUSTER_IDS:
        return ["U"]
    return ["M", "F"]


def get_capacity_for_section(cluster_id: str, section: str) -> int:
    """
    Return the capacity for a specific section of a cluster.
    """
    cluster = CLUSTERS_BY_ID[cluster_id]
    if section == "U":
        return cluster["capacidade_unissex"]
    elif section == "M":
        return cluster["capacidade_m"]
    elif section == "F":
        return cluster["capacidade_f"]
    return 0
