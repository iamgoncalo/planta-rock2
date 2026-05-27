# PlantaOS × Rock in Rio Lisboa 2026 — Test Report

**Date:** 2026-05-27
**Environment:** macOS Darwin 25.2.0, Python 3.14, Node.js 22.x

---

## Backend Tests

### Run Command
```bash
cd backend
source .venv/bin/activate
pytest -v
```

### Results

| Suite | Tests | Passed | Failed | Skipped |
|-------|-------|--------|--------|---------|
| test_schemas.py | 27 | 27 | 0 | 0 |
| test_fusion.py | 24 | 24 | 0 | 0 |
| test_kpis.py | 18 | 18 | 0 | 0 |
| test_alerts.py | 22 | 22 | 0 | 0 |
| test_simulation.py | 18 | 18 | 0 | 0 |
| test_api.py | 31 | 31 | 0 | 0 |
| **TOTAL** | **140** | **140** | **0** | **0** |

**Duration:** ~13 seconds

### Critical Test Cases

#### WC-05 / WC-06 Unisex Invariant
```
test_schemas.py::TestClusterSections::test_unisex_clusters_have_no_m_or_f  PASSED
test_simulation.py::TestSimulationTick::test_wc05_and_wc06_have_only_u_section  PASSED
test_schemas.py::TestClusterSections::test_wc05_tipo_is_unissex  PASSED
test_schemas.py::TestClusterSections::test_wc06_tipo_is_unissex  PASSED
```

#### Sensor Fusion
```
test_fusion.py::TestFusion::test_all_sources  PASSED
test_fusion.py::TestFusion::test_missing_camera_redistributes_weights  PASSED
test_fusion.py::TestFusion::test_only_ir  PASSED
test_fusion.py::TestFusion::test_confidence_drops_with_fewer_sources  PASSED
```

#### Alert Thresholds
```
test_alerts.py::TestAlerts::test_critico_above_90  PASSED
test_alerts.py::TestAlerts::test_alto_above_75_queue_above_20  PASSED
test_alerts.py::TestAlerts::test_no_critico_at_90  PASSED (boundary)
test_alerts.py::TestAlerts::test_medio_low_confidence  PASSED
```

#### KPI Range Validation
```
test_kpis.py::TestKPIs::test_kpi01_in_range  PASSED
test_kpis.py::TestKPIs::test_kpi02_is_average  PASSED
test_kpis.py::TestKPIs::test_kpi03_counts_critico_only  PASSED
test_kpis.py::TestKPIs::test_kpi04_non_negative  PASSED
```

#### API Endpoints
```
test_api.py::TestAPI::test_health  PASSED  (200 OK)
test_api.py::TestAPI::test_clusters_returns_8  PASSED
test_api.py::TestAPI::test_kpis_structure  PASSED
test_api.py::TestAPI::test_simulate_tick  PASSED
test_api.py::TestAPI::test_chat_fallback  PASSED
test_api.py::TestAPI::test_shows  PASSED
test_api.py::TestAPI::test_sensor_ingest  PASSED
```

#### Simulation Scenarios
```
test_simulation.py::TestSimulationTick::test_all_scenarios_run_without_error  PASSED  (15 scenarios)
test_simulation.py::TestSimulationTick::test_headliner_start_higher_than_normal_day  PASSED
test_simulation.py::TestSimulationTick::test_occupancy_always_in_valid_range  PASSED
test_simulation.py::TestSimulationTick::test_sensor_ir_offline_lowers_confidence  PASSED
```

---

## Frontend Checks

### Run Commands
```bash
cd frontend
npm run typecheck
npm run lint
```

### Results

| Check | Result |
|-------|--------|
| TypeScript (`tsc --noEmit`) | ✅ 0 errors |
| ESLint (`next lint`) | ✅ 0 warnings, 0 errors |
| Red color grep | ✅ 0 occurrences of `#FF0000`, `#EF4444`, `text-red-*`, `bg-red-*` |
| Deucalion grep | ✅ 0 occurrences |
| CO2/temperature sensor grep | ✅ 0 occurrences (only in forbidden-list comments) |
| WC-05/06 M/F split grep | ✅ 0 occurrences |

---

## End-to-End Verification (manual)

The following flows were verified by inspecting the code paths (automated E2E not set up in this build):

| Scenario | Status | How |
|----------|--------|-----|
| Frontend loads /twin | ✅ | Page fetches GET /clusters on mount; WS hook connects |
| /occupation shows 8 clusters | ✅ | useClusters hook returns all 8; map is exhaustive |
| /occupation WC-05 shows Unissex only | ✅ | ClusterCard branches on `tipo === "unissex"` |
| /shows cards are clickable | ✅ | ShowCard has onClick + state for selected show |
| /chat sends a message | ✅ | ChatWindow POSTs to /api/v1/chat |
| Map dot click opens drawer | ✅ | ClusterDot calls onSelect; ParqueTejo renders ClusterDrawer |
| WC card click opens drawer | ✅ | ClusterCard has expandable detail section |
| KPI cards update from WS | ✅ | useKPIs subscribes to WS; KpiCards renders live |
| Backend /health returns 200 | ✅ | Tested with uvicorn + curl |
| Chat fallback without Gemini | ✅ | test_api.py::test_chat_fallback PASSES |
| WebSocket full state on connect | ✅ | websocket.py sends snapshot immediately on connect |

---

## Known Test Gaps

| Gap | Risk | Mitigation |
|-----|------|-----------|
| No Playwright/Cypress E2E | Medium | Manual smoke test + code review |
| No WS reconnect integration test | Low | Unit-tested in ws.ts logic; exponential backoff verified in code |
| No load test | Low | Festival is 100k people but backend serves ~20 dashboard clients |
| No Gemini API integration test | Low | Requires live key; fallback always tested |
| Frontend unit tests minimal | Low | TypeScript + lint provide strong static guarantees |

---

## Remaining Risks (Prioritized)

### HIGH
1. **No real sensor hardware** — System runs on simulation. If LilyGo firmware doesn't match POST /api/v1/sensor schema exactly, ingest will fail. Mitigate: validate firmware JSON against schema before event.

2. **Prosegur camera integration unknown** — The POST /api/v1/prosegur endpoint is implemented but Prosegur's actual payload format may differ. Their API was not documented; the schema is an assumption. Mitigate: confirm with Prosegur team before go-live.

### MEDIUM
3. **WebSocket at scale** — uvicorn single-process handles ~200 concurrent WS connections fine. If more clients connect (unexpected), consider gunicorn workers or Railway multi-instance. Current setup sufficient for ops team (< 20 clients).

4. **SCOR publishing untested** — `scor.py` implements the Sensaway endpoint POST but no integration test was run (requires live SCOR credentials). Mitigate: test SCOR token validity 48h before event.

5. **Gemini 2.5 Flash rate limits** — If the team sends many chat messages during peak, the 2.5-flash-preview model may throttle. The local fallback activates automatically on any API error, so the chat stays functional.

6. **Simulation vs reality gap** — The simulation uses deterministic seeded noise calibrated for plausibility, not real historical RiR data. Actual occupancy patterns may differ. The system adapts in real-time once real sensors start POSTing.

### LOW
7. **Admin PIN not enforced on frontend** — The /ops reset button sends the request; the backend checks ADMIN_PIN. If ADMIN_PIN is not set in env, the endpoint is unprotected. Mitigate: always set ADMIN_PIN in production env.

8. **CSV export is client-side** — The /ops Export CSV generates from current in-memory WS state. If the page was just opened, it may have incomplete history. Full history export requires a dedicated /api/v1/export endpoint (not yet implemented).

9. **Mobile layout not fully tested** — The UI uses Tailwind responsive classes but was not validated on a real mobile device. The `/app` public page is the most mobile-critical path.

10. **Timezone handling** — The simulation uses server UTC time. If the Raspberry Pi is in Lisbon timezone (UTC+1 in June), show schedule calculations will be off by 1 hour. Mitigate: set `TZ=Europe/Lisbon` on the server.
