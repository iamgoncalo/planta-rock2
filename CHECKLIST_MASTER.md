# PlantaOS × Rock in Rio Lisboa 2026 — Checklist Master

**Status as of:** 2026-05-27

---

## AGENT 01 — Repo Auditor ✅

- [x] Inspect folder structure
- [x] Identify current frontend framework → Next.js 15 (created)
- [x] Identify current backend framework → FastAPI (created)
- [x] Identify broken imports → N/A (cold build)
- [x] Identify missing pages → all 7 created
- [x] Identify whether frontend calls backend → YES, via WS + REST
- [x] Output: AUDIT_SUMMARY.md

---

## AGENT 02 — Data Contract Architect ✅

- [x] Cluster type with all fields
- [x] SectionState type (ocupacao_pct, fila_actual, tempo_espera_min, fluxo, confianca, fontes_activas, status)
- [x] ClusterState / ClusterData type
- [x] SensorReading type (no GPS fields)
- [x] ProsegurReading type
- [x] Alert type with severidade enum CRITICO/ALTO/MEDIO/INFO
- [x] GlobalKPIs type with kpi_01–04
- [x] Show type with all fields
- [x] WebSocketPayload type
- [x] WC-05/WC-06 only have section "U" — enforced in schema validator
- [x] WC-01–04, 07–08 have "M" and "F" — enforced in schema validator
- [x] Output: backend/app/schemas.py
- [x] Output: frontend/src/types/index.ts

---

## AGENT 03 — Static Database Agent ✅

- [x] 8 WC clusters with ID, name, tipo, entry_only, lat, lon, capacities, dist_entrada_m
- [x] WC-05: capacidade_unissex=133, entry_only=True, tipo=unissex
- [x] WC-06: capacidade_unissex=208, entry_only=False, tipo=unissex
- [x] GPS coordinates as fixed metadata only
- [x] 4-day show programme with 39 shows
- [x] Headliners: Katy Perry, Alok, Linkin Park, Tara Perdida, Rod Stewart, The Wailers, 21 Savage, Lola Índigo
- [x] surge_esperado_30min_apos on headliners
- [x] Output: backend/app/data/clusters.py
- [x] Output: backend/app/data/shows.py
- [x] Output: frontend/src/lib/clusters.ts
- [x] Output: frontend/src/lib/shows.ts

---

## AGENT 04 — Simulation Engine Agent ✅

- [x] Deterministic simulation with seeded noise
- [x] Inputs: current time, active show, post-show surge, sensor failure scenario
- [x] Outputs per section: ocupacao_pct, ocupacao_absoluta, fila_actual, tempo_espera_min, fluxo_entrada_pmin, fluxo_saida_pmin, confianca_pct, fontes_activas, status, alertas
- [x] Scenario: normal_day
- [x] Scenario: headliner_start
- [x] Scenario: headliner_end_surge
- [x] Scenario: wc05_overcrowded
- [x] Scenario: wc06_relief
- [x] Scenario: sensor_ir_offline
- [x] Scenario: wifi_offline
- [x] Scenario: camera_offline
- [x] Scenario: all_sensors_degraded
- [x] Scenario: prosegur_disagreement
- [x] Scenario: entry_only_pressure
- [x] Scenario: rain_surge
- [x] Scenario: crowd_surge
- [x] Scenario: network_dropout
- [x] Scenario: recovery_after_redirect
- [x] Output: backend/app/services/simulation.py

---

## AGENT 05 — Sensor Fusion Agent ✅

- [x] IR weight = 0.50
- [x] WiFi weight = 0.30
- [x] Camera weight = 0.20
- [x] Redistribute weights proportionally if source missing
- [x] Never divide by zero when all sources missing (uses last known value)
- [x] Confidence depends on number of active sources + camera ML confidence
- [x] Test: all 3 sources → correct weighted average
- [x] Test: missing camera → IR 0.625, WiFi 0.375
- [x] Test: only IR → weight 1.0
- [x] Output: backend/app/services/fusion.py

---

## AGENT 06 — KPI Agent ✅

- [x] KPI 01: Flow Index 0–100 (high = fluid, low = congested)
- [x] KPI 02: Average WC Occupancy % across all active sections
- [x] KPI 03: Count of CRITICO alerts
- [x] KPI 04: Daily people redirected (accumulator, resets at midnight)
- [x] All KPIs clamped to valid ranges (0–100 for 01/02, non-negative for 03/04)
- [x] festival_day field (1–4 or null outside festival dates)
- [x] show_activo field
- [x] minutos_para_headliner field
- [x] Output: backend/app/services/kpis.py

---

## AGENT 07 — Alert Agent ✅

- [x] CRITICO: ocupacao_pct > 90
- [x] ALTO: ocupacao_pct > 75 AND fila_actual > 20
- [x] MEDIO: confianca_pct < 40
- [x] INFO: sensor offline > 5 minutes
- [x] Alerts have id, cluster_id, secao, severidade, tipo, mensagem, ts_inicio, ts_fim, resolvido
- [x] Alerts are deduplicated (no duplicate CRITICO for same cluster+section)
- [x] Output: backend/app/services/alerts.py

---

## AGENT 08 — Routing Agent ✅

- [x] Recommend best alternative WC for a given overcrowded cluster
- [x] Avoid CRITICO clusters
- [x] Prefer lower occupancy
- [x] Prefer lower queue
- [x] Prefer closer distance
- [x] WC-05 (entry_only=True) NOT recommended as relief destination
- [x] Returns: recommended_cluster, reason, distance_m
- [x] Output: backend/app/services/routing.py

---

## AGENT 09 — Backend API Agent ✅

- [x] CORS enabled: localhost:3000, localhost:5173, 127.0.0.1:3000
- [x] GET /api/v1/health
- [x] GET /api/v1/clusters → 8 clusters with full state
- [x] GET /api/v1/kpis → 4 KPIs
- [x] GET /api/v1/shows → full programme
- [x] POST /api/v1/sensor → ingest LilyGo reading
- [x] POST /api/v1/prosegur → ingest camera reading
- [x] POST /api/v1/simulate/tick → advance simulation
- [x] POST /api/v1/chat → chat with Gemini or local fallback
- [x] WS /api/v1/ws → WebSocket
- [x] FastAPI docs at /docs
- [x] Output: backend/app/main.py + all routers

---

## AGENT 10 — WebSocket Agent ✅

- [x] On connect: immediately send full state snapshot
- [x] Broadcast every 5 seconds to all connected clients
- [x] Payload includes: clusters, kpis, alertas_activos, show_activo, minutos_para_headliner, routing_recommendations
- [x] Queue-per-client architecture (slow client doesn't block others)
- [x] Frontend: exponential backoff reconnect (1s → 2s → 4s → ... → 30s max)
- [x] Frontend: WS singleton (doesn't close on component unmount)
- [x] Output: backend/app/routers/websocket.py
- [x] Output: frontend/src/lib/ws.ts

---

## AGENT 11 — Frontend Shell Agent ✅

- [x] Dark UI (#0f1117 background, #1a1f2e cards)
- [x] Navigation: 6 tabs (Twin | Ocupação | Sensores | Shows | Chat | Ops)
- [x] Status bar: LIVE indicator + current time + active show
- [x] Global KPI cards always visible (Flow Index, Ocupação Média, Alertas, Redirecionados)
- [x] No red color anywhere
- [x] Responsive: desktop / tablet / mobile
- [x] Output: frontend/src/app/layout.tsx
- [x] Output: frontend/src/components/Nav.tsx
- [x] Output: frontend/src/components/KpiCards.tsx

---

## AGENT 12 — Product Pages Agent ✅

- [x] /twin: SVG map, clickable WC dots, ClusterDrawer, pulsing critical dots
- [x] /occupation: 8 cards, M/F for misto, U only for unissex, sortable, filterable
- [x] /sensors: sensor health table, fontes_activas, event log
- [x] /shows: 4-day programme, clickable shows, surge indicator, day selector
- [x] /chat: context badge, message history, POST to /api/v1/chat
- [x] /ops: alerts panel, routing panel, SCOR status, timeline, CSV export
- [x] /app: public visitor app, best WC now, list of alternatives

---

## AGENT 13 — Chat Agent ✅

- [x] GEMINI_API_KEY present → calls Gemini 2.5 Flash
- [x] GEMINI_API_KEY absent → local deterministic Portuguese fallback
- [x] Answers: "qual WC mais livre"
- [x] Answers: "qual WC evitar"
- [x] Answers: "alertas críticos"
- [x] Answers: "show ativo"
- [x] Answers: "redirecionar de WC-05"
- [x] Never invents data not in context
- [x] Output: backend/app/services/chat.py

---

## AGENT 14 — Test Agent ✅

Backend tests (pytest):
- [x] WC-05/WC-06 unisex only → passes
- [x] Fusion with all sources → passes
- [x] Fusion with missing camera → passes
- [x] Fusion with only IR → passes
- [x] KPI values in valid range → passes
- [x] CRITICO alert at >90% → passes
- [x] GET /clusters returns 8 clusters → passes
- [x] POST /simulate/tick changes state → passes
- [x] Chat fallback answers with live data → passes
- [x] Total: 140/140 PASSING

Frontend checks:
- [x] `npm run typecheck` → 0 TypeScript errors
- [x] `npm run lint` → 0 ESLint warnings/errors
- [x] No hardcoded red color (grep confirmed)

---

## AGENT 15 — Extreme Counterfactual QA Agent ✅

- [x] docs/COUNTERFACTUAL_QA.md with 50+ scenarios
- [x] All categories covered: sensor failures, data disagreement, impossible values, UI bugs, network issues, GDPR, operational edge cases

---

## Final Deliverables

- [x] AUDIT_SUMMARY.md
- [x] CHECKLIST_MASTER.md (this file)
- [x] docs/COUNTERFACTUAL_QA.md
- [x] RUNBOOK_LOCAL.md
- [x] TEST_REPORT.md
- [x] README.md (updated with exact commands)

---

## Remaining Risks

See bottom of TEST_REPORT.md for the prioritized risk list.
