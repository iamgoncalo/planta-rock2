"""
Pydantic v2 schemas for PlantaOS × Rock in Rio Lisboa 2026.

Key invariants enforced here:
- SectionState occupancy_pct is always 0-100.
- Alert severidade is one of CRITICO / ALTO / MEDIO / INFO.
- Sensor payloads carry ONLY people-counts, no environmental data.
- GPS is NOT in any telemetry payload (static metadata only).
- No individual tracking — only aggregated counts.
"""
from __future__ import annotations

import time
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AlertSeveridade(str, Enum):
    CRITICO = "CRITICO"
    ALTO = "ALTO"
    MEDIO = "MEDIO"
    INFO = "INFO"


class SectionStatus(str, Enum):
    LIVRE = "livre"          # < 50 %
    MODERADO = "moderado"    # 50–74 %
    CHEIO = "cheio"          # 75–89 %
    CRITICO = "critico"      # >= 90 %


class SensorSource(str, Enum):
    IR = "IR"
    WIFI = "WiFi"
    CAMERA = "Camera"


class ClusterTipo(str, Enum):
    MISTO = "misto"
    UNISSEX = "unissex"


# ---------------------------------------------------------------------------
# Section state
# ---------------------------------------------------------------------------

class SectionState(BaseModel):
    """Live operational state for one section (M, F, or U) of a WC cluster."""

    ocupacao_pct: float = Field(0.0, ge=0.0, le=100.0,
                                description="Occupancy percentage 0–100")
    ocupacao_absoluta: int = Field(0, ge=0,
                                   description="Absolute number of people inside")
    fila_actual: int = Field(0, ge=0, description="Current queue length (people)")
    tempo_espera_min: float = Field(0.0, ge=0.0,
                                    description="Estimated wait time in minutes")
    fluxo_entrada_pmin: float = Field(0.0, ge=0.0,
                                      description="Entry flow in people/min")
    fluxo_saida_pmin: float = Field(0.0, ge=0.0,
                                    description="Exit flow in people/min")
    status: SectionStatus = SectionStatus.LIVRE
    confianca_pct: float = Field(100.0, ge=0.0, le=100.0,
                                 description="Sensor fusion confidence 0–100")
    fontes_activas: List[str] = Field(default_factory=list,
                                      description="Active sensor sources")

    @field_validator("ocupacao_pct", mode="before")
    @classmethod
    def clamp_ocupacao(cls, v: Any) -> float:
        return max(0.0, min(100.0, float(v)))

    @field_validator("confianca_pct", mode="before")
    @classmethod
    def clamp_confianca(cls, v: Any) -> float:
        return max(0.0, min(100.0, float(v)))

    def compute_status(self) -> "SectionState":
        """Return a new instance with status recalculated from occupancy."""
        if self.ocupacao_pct >= 90:
            status = SectionStatus.CRITICO
        elif self.ocupacao_pct >= 75:
            status = SectionStatus.CHEIO
        elif self.ocupacao_pct >= 50:
            status = SectionStatus.MODERADO
        else:
            status = SectionStatus.LIVRE
        return self.model_copy(update={"status": status})


# ---------------------------------------------------------------------------
# Cluster state (runtime)
# ---------------------------------------------------------------------------

class ClusterState(BaseModel):
    """Full runtime state for one WC cluster, including all sections."""

    cluster_id: str
    nome: str
    tipo: ClusterTipo
    entry_only: bool
    lat: float
    lon: float
    dist_entrada_m: int
    secoes: Dict[str, SectionState] = Field(default_factory=dict,
                                             description="Keyed by 'M','F' or 'U'")
    alertas: List["Alert"] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

class Alert(BaseModel):
    """An operational alert for a cluster section."""

    cluster_id: str
    section: str
    severidade: AlertSeveridade
    mensagem: str
    ts: float = Field(default_factory=time.time)

    @field_validator("severidade", mode="before")
    @classmethod
    def validate_severidade(cls, v: Any) -> AlertSeveridade:
        if isinstance(v, str):
            return AlertSeveridade(v.upper())
        return v


# ---------------------------------------------------------------------------
# Sensor ingest payloads
# ---------------------------------------------------------------------------

class SensorReading(BaseModel):
    """
    LilyGo IR/WiFi sensor payload.
    ONLY people counts — no GPS, no environmental data.
    """

    cluster_id: str = Field(..., description="Target WC cluster ID e.g. 'WC-01'")
    section: str = Field(..., description="Section key: 'M', 'F', or 'U'")
    source: SensorSource = Field(..., description="Sensor type: IR or WiFi")
    contagem_entrada: int = Field(0, ge=0, description="People entered since last reading")
    contagem_saida: int = Field(0, ge=0, description="People exited since last reading")
    ocupacao_absoluta: Optional[int] = Field(None, ge=0, le=10000,
                                             description="Direct occupancy count if available")
    confianca_pct: float = Field(100.0, ge=0.0, le=100.0)
    ts: float = Field(default_factory=time.time)

    @field_validator("cluster_id")
    @classmethod
    def validate_cluster_id(cls, v: str) -> str:
        valid = {"WC-01", "WC-02", "WC-03", "WC-04", "WC-05", "WC-06", "WC-07", "WC-08"}
        if v not in valid:
            raise ValueError(f"Unknown cluster_id: {v}. Must be one of {valid}")
        return v

    @field_validator("section")
    @classmethod
    def validate_section(cls, v: str) -> str:
        if v not in ("M", "F", "U"):
            raise ValueError(f"section must be 'M', 'F', or 'U', got '{v}'")
        return v


class ProsegurReading(BaseModel):
    """
    Prosegur camera ML payload.
    ONLY aggregated people counts — no GPS, no environmental data.
    """

    cluster_id: str = Field(..., description="Target WC cluster ID")
    section: str = Field(..., description="Section key: 'M', 'F', or 'U'")
    ocupacao_absoluta: int = Field(0, ge=0, le=10000, description="Camera-estimated occupancy count")
    fila_actual: int = Field(0, ge=0, description="Camera-estimated queue count")
    confianca_ml: float = Field(1.0, ge=0.0, le=1.0,
                                description="Camera ML model confidence 0.0–1.0")
    ts: float = Field(default_factory=time.time)

    @field_validator("cluster_id")
    @classmethod
    def validate_cluster_id(cls, v: str) -> str:
        valid = {"WC-01", "WC-02", "WC-03", "WC-04", "WC-05", "WC-06", "WC-07", "WC-08"}
        if v not in valid:
            raise ValueError(f"Unknown cluster_id: {v}. Must be one of {valid}")
        return v

    @field_validator("section")
    @classmethod
    def validate_section(cls, v: str) -> str:
        if v not in ("M", "F", "U"):
            raise ValueError(f"section must be 'M', 'F', or 'U', got '{v}'")
        return v


# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------

class KPIs(BaseModel):
    """Four global Key Performance Indicators."""

    kpi_01: float = Field(..., ge=0.0, le=100.0,
                          description="Flow Index 0–100 (higher = better flow)")
    kpi_02: float = Field(..., ge=0.0, le=100.0,
                          description="Average occupancy % across all active sections")
    kpi_03: int = Field(..., ge=0,
                        description="Count of CRITICO alerts currently active")
    kpi_04: int = Field(..., ge=0,
                        description="Daily cumulative people redirected (estimate)")
    festival_day: Optional[int] = Field(None, description="Current festival day 1–4, or None")
    show_activo: Optional[str] = Field(None, description="Name of currently active headliner show")
    minutos_para_headliner: Optional[float] = Field(
        None, description="Minutes until next headliner starts, or None if already on"
    )


# ---------------------------------------------------------------------------
# Shows
# ---------------------------------------------------------------------------

class ShowEntry(BaseModel):
    """A single show in the festival programme."""

    dia: int
    data: str
    tema: str
    palco: str
    palco_nome: str
    artista: str
    inicio: str
    fim: str
    headliner: bool
    activo: bool = False
    proximo: bool = False


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

class SimulateTickRequest(BaseModel):
    """Optional override for a simulation tick."""

    scenario: Optional[str] = Field(None, description="Force a specific scenario name")
    hora_simulada: Optional[str] = Field(
        None, description="Override simulated hour as 'HH:MM' (24h)"
    )


class SimulateTickResponse(BaseModel):
    """Result of one simulation tick."""

    ts: float
    scenario: str
    clusters_updated: int
    alerts_generated: int


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    mensagem: str = Field(..., min_length=1, max_length=2000, description="User message")
    historico: List[ChatMessage] = Field(default_factory=list,
                                         description="Conversation history")


class ChatResponse(BaseModel):
    resposta: str
    fonte: Literal["gemini", "local"] = "local"


# ---------------------------------------------------------------------------
# Routing recommendation
# ---------------------------------------------------------------------------

class RoutingRecommendation(BaseModel):
    """A crowd-routing recommendation."""

    from_cluster_id: str
    recommended_cluster_id: str
    reason: str
    distance_m: int
    ocupacao_destino_pct: float


# ---------------------------------------------------------------------------
# WebSocket broadcast payload
# ---------------------------------------------------------------------------

class WSClusterSection(BaseModel):
    ocupacao_pct: float
    ocupacao_absoluta: int
    fila_actual: int
    tempo_espera_min: float
    fluxo_entrada_pmin: float
    fluxo_saida_pmin: float
    status: str
    confianca_pct: float
    fontes_activas: List[str]


class WSCluster(BaseModel):
    cluster_id: str
    nome: str
    tipo: str
    entry_only: bool
    secoes: Dict[str, WSClusterSection]
    alertas: List[Dict[str, Any]]


class WSPayload(BaseModel):
    type: str = "cluster_update"
    ts: float = Field(default_factory=time.time)
    clusters: List[WSCluster]
    kpis: KPIs
    alertas_activos: int
    show_activo: Optional[str]
    minutos_para_headliner: Optional[float]
    routing_recommendations: List[RoutingRecommendation]


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str = "ok"
    ts: float = Field(default_factory=time.time)
    version: str = "1.0.0"


# Forward references
ClusterState.model_rebuild()
