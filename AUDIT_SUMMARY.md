# PlantaOS × Rock in Rio Lisboa 2026 — Audit Summary

**Date:** 2026-05-27
**Auditor:** Agent 01 (Repo Auditor)
**Repo:** planta-rir2026/

---

## Pre-Build State

The repository existed as an empty scaffold:

| Item | Pre-build Status |
|------|-----------------|
| backend/ | Empty directory |
| frontend/ | Empty directory |
| docs/ | Empty directory |
| firmware/ | Empty directory |
| scripts/ | Empty directory |
| tests/ | Empty directory |
| README.md | Empty file |
| docker-compose.yml | Empty file |
| .gitignore | Empty file |

**Verdict:** Full cold build required. No existing code to repair.

---

## Post-Build State

### Backend (`backend/`)

| Component | Status | Notes |
|-----------|--------|-------|
| `pyproject.toml` | ✅ Created | setuptools build, Python 3.12+ |
| `app/main.py` | ✅ Created | FastAPI + CORS + lifespan |
| `app/config.py` | ✅ Created | Pydantic Settings, all env vars |
| `app/state.py` | ✅ Created | In-memory singleton AppState |
| `app/schemas.py` | ✅ Created | All Pydantic models |
| `app/data/clusters.py` | ✅ Created | 8 WC clusters with full metadata |
| `app/data/shows.py` | ✅ Created | 39 shows across 4 festival days |
| `app/routers/health.py` | ✅ Created | GET /api/v1/health |
| `app/routers/clusters.py` | ✅ Created | GET /api/v1/clusters |
| `app/routers/kpis.py` | ✅ Created | GET /api/v1/kpis |
| `app/routers/shows.py` | ✅ Created | GET /api/v1/shows |
| `app/routers/ingest.py` | ✅ Created | POST /api/v1/sensor |
| `app/routers/prosegur.py` | ✅ Created | POST /api/v1/prosegur |
| `app/routers/simulate.py` | ✅ Created | POST /api/v1/simulate/tick |
| `app/routers/chat.py` | ✅ Created | POST /api/v1/chat |
| `app/routers/websocket.py` | ✅ Created | WS /api/v1/ws |
| `app/services/simulation.py` | ✅ Created | 15 scenarios, deterministic |
| `app/services/fusion.py` | ✅ Created | IR+WiFi+Camera weighted fusion |
| `app/services/kpis.py` | ✅ Created | 4 KPIs computed |
| `app/services/alerts.py` | ✅ Created | CRITICO/ALTO/MEDIO/INFO thresholds |
| `app/services/routing.py` | ✅ Created | Best alternative WC recommendation |
| `app/services/chat.py` | ✅ Created | Gemini adapter + local fallback |
| `tests/` (6 files) | ✅ Created | 140 tests, all passing |

### Frontend (`frontend/`)

| Component | Status | Notes |
|-----------|--------|-------|
| `package.json` | ✅ Created | Next.js 15.3.2, React 19 |
| `next.config.ts` | ✅ Created | Minimal config |
| `tsconfig.json` | ✅ Created | Strict TypeScript |
| `tailwind.config.ts` | ✅ Created | Dark theme custom colors |
| `src/types/index.ts` | ✅ Created | All TypeScript contracts |
| `src/lib/api.ts` | ✅ Created | Typed fetch helpers |
| `src/lib/ws.ts` | ✅ Created | Singleton WS + exponential backoff |
| `src/lib/clusters.ts` | ✅ Created | Static cluster metadata |
| `src/lib/shows.ts` | ✅ Created | Static shows data |
| `src/lib/colors.ts` | ✅ Created | Status colors, NO RED |
| `src/hooks/useClusters.ts` | ✅ Created | WS-first, REST fallback |
| `src/hooks/useKPIs.ts` | ✅ Created | Live KPI state |
| `src/hooks/useAlerts.ts` | ✅ Created | Active alerts |
| `src/hooks/useCurrentShow.ts` | ✅ Created | Active/next show |
| `src/app/layout.tsx` | ✅ Created | Nav + KPI cards + StatusBar |
| `src/app/twin/page.tsx` | ✅ Created | SVG map, clickable dots |
| `src/app/occupation/page.tsx` | ✅ Created | Grid cards, M/F/U gauges |
| `src/app/sensors/page.tsx` | ✅ Created | Sensor health table |
| `src/app/shows/page.tsx` | ✅ Created | Programme by day |
| `src/app/chat/page.tsx` | ✅ Created | AI chat interface |
| `src/app/ops/page.tsx` | ✅ Created | Alerts + routing + export |
| `src/app/app/page.tsx` | ✅ Created | Public visitor app |

---

## Product Rule Compliance

| Rule | Status | Evidence |
|------|--------|---------|
| Count only people and flows | ✅ | No CO2/temp/humidity in any schema |
| WC-05/WC-06 unisex only | ✅ | Test `test_wc05_and_wc06_have_only_u_section` PASSES; UI branches on `tipo === "unissex"` |
| WC-01–04, 07–08 have M and F | ✅ | Test `test_misto_clusters_have_only_m_and_f` PASSES |
| All 7 required pages exist | ✅ | /twin /occupation /sensors /shows /chat /ops /app |
| All 9 required API endpoints | ✅ | health, clusters, kpis, sensor, prosegur, simulate/tick, chat, ws, shows |
| Frontend calls backend | ✅ | All hooks use WS + REST API, no isolated mocks |
| 4 global KPIs displayed | ✅ | KpiCards component in layout, always visible |
| Shows clickable | ✅ | ShowCard has onClick + detail panel |
| WC cards clickable | ✅ | ClusterCard has onClick + ClusterDrawer |
| Map dots clickable | ✅ | ClusterDot has onClick, opens ClusterDrawer |
| AI Chat local fallback | ✅ | services/chat.py has deterministic Portuguese fallback |
| No red UI color | ✅ | grep confirms no #FF0000/#EF4444/text-red-*/bg-red-* |
| Critical = #C25A1A | ✅ | colors.ts and CSS confirmed |
| GPS fixed metadata only | ✅ | lat/lon in cluster config, absent from SensorReading/ProsegurReading |
| No individual tracking | ✅ | Only aggregated counts in all schemas |
| Local single-command run | ✅ | `uvicorn app.main:app` + `npm run dev` |
| No Deucalion references | ✅ | grep found zero results |

---

## Frontend–Backend Connection

The frontend connects to the backend via:

1. **WebSocket** (`ws://localhost:8000/api/v1/ws`) — primary, receives full state on connect, updates every 5 seconds
2. **REST polling** (`GET /api/v1/clusters`, `/kpis`) — fallback if WS disconnected, polls every 10 seconds
3. **POST requests** — `/api/v1/chat`, `/api/v1/simulate/tick`

The connection is NOT isolated mock-only. If the backend is unreachable, the UI shows a "Backend offline" state gracefully.

---

## Tests

| Suite | Tests | Status |
|-------|-------|--------|
| test_schemas.py | 27 | ✅ All pass |
| test_fusion.py | 24 | ✅ All pass |
| test_kpis.py | 18 | ✅ All pass |
| test_alerts.py | 22 | ✅ All pass |
| test_simulation.py | 18 | ✅ All pass |
| test_api.py | 31 | ✅ All pass |
| **Total** | **140** | **✅ 140/140** |

Frontend: `npm run typecheck` → 0 errors, `npm run lint` → 0 warnings.

---

## Known Gaps / Remaining Risks

See `CHECKLIST_MASTER.md` and the Remaining Risks section.
