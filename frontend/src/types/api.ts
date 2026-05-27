export interface SectionState {
  ocupacao_pct: number
  ocupacao_absoluta: number
  fila_actual: number
  tempo_espera_min: number
  fluxo_entrada_pmin: number
  fluxo_saida_pmin: number
  status: 'livre' | 'moderado' | 'cheio' | 'critico'
  confianca_pct: number
  fontes_activas: string[]
}

export interface ClusterSections {
  M?: SectionState
  F?: SectionState
  U?: SectionState
}

export interface AlertItem {
  cluster_id: string
  section: string
  severidade: 'CRITICO' | 'ALTO' | 'MEDIO' | 'INFO'
  mensagem: string
  ts: number
}

export interface Cluster {
  cluster_id: string
  nome: string
  tipo: 'misto' | 'unissex'
  entry_only: boolean
  secoes: ClusterSections
  alertas: AlertItem[]
}

export interface GlobalKPIs {
  kpi_01: number
  kpi_02: number
  kpi_03: number
  kpi_04: number
  festival_day: number | null
  show_activo: string | null
  minutos_para_headliner: number | null
}

export interface WSPayload {
  type: string
  ts: number
  clusters: Cluster[]
  kpis: GlobalKPIs
  alertas_activos: number
  show_activo: string | null
  minutos_para_headliner: number | null
  routing_recommendations: RoutingRecommendation[]
}

export interface RoutingRecommendation {
  from_cluster_id: string
  recommended_cluster_id: string
  reason: string
  distance_m: number
  ocupacao_destino_pct: number
}

export interface RouteOption {
  cluster_id: string
  nome: string
  walk_time_min: number
  queue_wait_min: number
  total_cost_min: number
  reason: string
  ocupacao_pct: number
  confianca_pct: number
}

export interface BathroomRouteDecision {
  options: RouteOption[]
  chosen: RouteOption | null
  avoid: string[]
  confidence: number
  expires_at: number
}

export interface DeviceStatus {
  status: 'online' | 'degraded' | 'offline'
  last_seen_s: number
  confidence_pct: number
}

export interface SensorHealth {
  cluster_id: string
  lilygo: DeviceStatus
  ir_entry: DeviceStatus
  ir_exit: DeviceStatus
  wifi_aggregate: DeviceStatus
  camera_ml: DeviceStatus
  lorawan: DeviceStatus
  overall_confidence: number
  issues: string[]
  simulado: boolean
}

export interface ShowEntry {
  dia: number
  data: string
  tema: string
  palco: string
  palco_nome: string
  artista: string
  inicio: string
  fim: string
  headliner: boolean
  activo: boolean
  proximo: boolean
}

export interface TVClusterEntry {
  cluster_id: string
  nome: string
  walk_time_s: number
  queue_wait_s: number
  occupancy_pct: number
  fila: number
  status: string
  direction?: string
}

export interface TVAvoidEntry {
  cluster_id: string
  reason: string
}

export interface TVScreenState {
  screen_id: string
  zone: string
  language: string
  simulado: boolean
  best_wc: TVClusterEntry | null
  alternatives: TVClusterEntry[]
  avoid: TVAvoidEntry[]
  critical_override?: string | null
  ts: number
}
