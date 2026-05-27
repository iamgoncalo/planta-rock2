export type ClusterStatus = "livre" | "moderado" | "cheio" | "critico" | "offline";
export type SectionKey = "M" | "F" | "U";
export type AlertSeverity = "CRITICO" | "ALTO" | "MEDIO" | "INFO";
export type AlertSection = "M" | "F" | "U" | "GLOBAL";
export type StageCode = "PM" | "PMV" | "PSB" | "PBP";

export interface SectionState {
  ocupacao_pct: number;
  ocupacao_absoluta: number;
  fila_actual: number;
  tempo_espera_min: number;
  fluxo_entrada_pmin: number;
  fluxo_saida_pmin: number;
  status: ClusterStatus;
  confianca_pct: number;
  fontes_activas: string[];
}

export interface Alert {
  id: string;
  cluster_id: string;
  secao: AlertSection;
  severidade: AlertSeverity;
  tipo: string;
  mensagem: string;
  ts_inicio: number;
  ts_fim: number | null;
  resolvido: boolean;
}

export interface ClusterData {
  cluster_id: string;
  nome: string;
  tipo: "misto" | "unissex";
  entry_only: boolean;
  lat: number;
  lon: number;
  dist_entrada_m: number;
  secoes: {
    M?: SectionState;
    F?: SectionState;
    U?: SectionState;
  };
  alertas: Alert[];
}

export interface ClusterResponse {
  clusters: ClusterData[];
  ts: number;
}

export interface GlobalKPIs {
  ts: number;
  kpi_01: number;
  kpi_02: number;
  kpi_03: number;
  kpi_04: number;
  festival_day: number | null;
  show_activo: string | null;
  minutos_para_headliner: number | null;
}

export interface Show {
  id: string;
  data: string;
  hora_inicio: string;
  hora_fim: string;
  artista: string;
  palco: StageCode;
  headliner: boolean;
  genero: string;
  surge_esperado_30min_apos: boolean;
  clusters_afectados: string[];
}

export interface ShowsResponse {
  shows: Show[];
}

export interface RoutingRecommendation {
  from_cluster: string;
  to_cluster: string;
  reason: string;
  distance_m: number;
}

export interface WebSocketPayload {
  type: "cluster_update";
  ts: number;
  clusters: ClusterData[];
  kpis: GlobalKPIs;
  alertas_activos: number;
  show_activo: string | null;
  minutos_para_headliner: number | null;
  routing_recommendations: RoutingRecommendation[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  message: string;
  context?: string;
}

export interface ChatResponse {
  reply: string;
  ts: number;
}

export interface HealthResponse {
  status: string;
  ts: number;
  version: string;
}

// Static cluster metadata shape
export interface ClusterMeta {
  nome: string;
  tipo: "misto" | "unissex";
  dist_entrada_m: number;
  capacidadeM?: number;
  capacidadeF?: number;
  capacidadeU?: number;
  entry_only?: boolean;
}
