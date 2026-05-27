# Track 09 — Failure Mode Audit
**PlantaOS × Rock in Rio Lisboa 2026**
**Date:** 2026-05-27
**Auditor:** Claude Sonnet 4.6 (Track 09 / 10)

---

## 1. Failure Scenario Results

### 1.1 Malformed Sensor Data

| Scenario | Expected Behavior | Actual Behavior | Gap | Severity |
|---|---|---|---|---|
| Missing all required fields (only `cluster_id`) | 422 with field errors | 422 — correctly reports `section` and `source` as missing | None | — |
| Invalid cluster ID `WC-99` | 422 with descriptive error | 422 — `"Unknown cluster_id: WC-99. Must be one of {...}"` | None | — |
| Negative values (`contagem_entrada: -5`, `contagem_saida: -3`) | 422 with `ge=0` violation | 422 — Pydantic rejects with `"Input should be greater than or equal to 0"` | None | — |
| Extreme occupancy injection (`ocupacao_absoluta: 9999`) | Clamped to 100% or rejected | Accepted (200). `fuse()` clamps to 100% at `max(0.0, min(100.0, occupancy_pct))`. `ocupacao_pct` settles at 100% then recovers on next sim tick | `ocupacao_absoluta` is not independently bounded by schema; the raw value is used directly in `reading.ocupacao_absoluta / cap * 100.0` before clamping in the fusion layer. No schema `le=` guard on the field itself | **MEDIUM** |
| Old test payload fields (`telemoveis_detectados`, `entradas_ir`) | 422 | 422 — correctly rejected as missing required fields (`section`, `source`) | None | — |

### 1.2 Invalid Prosegur Data

| Scenario | Expected Behavior | Actual Behavior | Gap | Severity |
|---|---|---|---|---|
| `confianca_ml: 150` (integer, 100× out of range) | 422 range error | 422 — `"Input should be less than or equal to 1"` | None | — |
| `confianca_ml: 1.5` (just over bound) | 422 range error | 422 — same Pydantic guard | None | — |
| `confianca_ml` as 0–100 integer scale (common field confusion) | Reject or document | Accepted only if value ≤ 1. Callers may confuse 0–1 float vs 0–100 % scale — schema description says `0.0–1.0` but field name `confianca_ml` implies percent to some API consumers | Documentation gap: field description in schema is correct but a `0–100` range with a division in the router would be friendlier | **LOW** |
| Section `"M"` for UNISSEX cluster `WC-05` | 422 UNISSEX enforcement | 422 — `"Cluster WC-05 é UNISSEX — apenas a secção 'U' é válida"` | None | — |
| Section `"U"` for MISTO cluster `WC-01` | 422 MISTO enforcement | 422 — `"Cluster WC-01 é MISTO — secções válidas são 'M' e 'F'"` | None | — |
| Missing required `section` field | 422 | 422 — Pydantic catches it | None | — |

### 1.3 Concurrent Request Handling

| Scenario | Expected Behavior | Actual Behavior | Gap | Severity |
|---|---|---|---|---|
| 50 concurrent sensor POSTs (WC-01/M) | All 200, no race conditions | **50/50 OK, 0.02 s total** | No asyncio.Lock on `cluster_states` — Python's GIL prevents TOCTOU corruption at the dict-write level for a single-worker process; safe under current single-process uvicorn deployment | Under multi-worker deployment (`--workers N`) with no shared memory (no Redis/DB), each worker has its own in-memory state — state would diverge across workers. **MEDIUM** for multi-worker |
| 200 concurrent GET /clusters | All 200, low latency | **200/200 OK, 0.05 s, ~4 000 req/s** | None | — |
| 200 concurrent sensor POSTs | All 200, no corruption | **200/200 OK, 0.04 s, ~4 700 req/s** | None | — |

### 1.4 Sensor Offline Detection

| Scenario | Expected Behavior | Actual Behavior | Gap | Severity |
|---|---|---|---|---|
| Background simulation loop generates INFO alert when sensor silent > 5 min | `evaluate_all_clusters` called with `sensor_timestamps` | `evaluate_all_clusters(app_state.cluster_states)` called **without** `sensor_timestamps` — offline check is skipped every automatic tick | **SENSOR OFFLINE ALERTS NEVER FIRE IN NORMAL OPERATION.** Only the manually-called `POST /simulate/tick` endpoint passes timestamps. The background `_simulation_loop` in `main.py` (line 124) does not. | **HIGH** |
| Per-section offline granularity (WC-01/M silent, WC-01/F active) | Separate alert per section | `app_state.sensor_readings` is keyed by `cluster_id` (not `"{cluster_id}_{section}"`). A reading from WC-01/M overwrites any reading from WC-01/F. `simulate.py` then maps that single timestamp to ALL sections of the cluster | If WC-01/M is silent but WC-01/F reports, WC-01/M will never generate an offline alert because WC-01/F's timestamp satisfies the check for both sections | **HIGH** |

### 1.5 WebSocket Reconnection

| Aspect | Expected | Actual | Gap | Severity |
|---|---|---|---|---|
| Exponential backoff on disconnect | Delays: 1s → 2s → 4s → 8s → 16s → 30s → 30s… | `onclose`: `setTimeout(fn, _wsRetry)` then inside fn: `_wsRetry = Math.min(_wsRetry*2, 30000)`. Sequence: 1 s, 2 s, 4 s, 8 s, 16 s, 30 s, 30 s… **Correct** | None | — |
| Max cap at 30 s | 30 000 ms | `Math.min(_wsRetry*2, 30000)` — **Correct** | None | — |
| Reset to 1 s on successful reconnect | Reset `_wsRetry=1000` on open | `_ws.onopen` resets `_wsRetry=1000` — **Correct** | None | — |
| Jitter to avoid thundering herd | Random jitter on backoff | **No jitter.** All clients reconnect at exactly the same intervals after a server restart. With O(100) dashboard sessions this could cause a brief spike, though at festival scale it is minor | Minor — not a festival-breaking issue | **LOW** |
| try/catch in `_wsConnect` | Catch synchronous WebSocket constructor exceptions | `try{_ws=new WebSocket(...) … }catch(e){ setTimeout(fn, _wsRetry); }` — **Correct** | None | — |

### 1.6 Schema Validation Coverage

| Field | Validated | Rule | Gap |
|---|---|---|---|
| `cluster_id` | Yes | Explicit whitelist of 8 IDs (`field_validator`) | — |
| `section` | Yes | Must be `"M"`, `"F"`, or `"U"` + unissex/misto cross-check in router | — |
| `source` | Yes | `SensorSource` enum (IR / WiFi / Camera) | — |
| `contagem_entrada` / `contagem_saida` | Yes | `ge=0` | — |
| `ocupacao_absoluta` (SensorReading) | Partial | `ge=0` only — **no upper bound** | No `le=capacity` guard; value 9 999 is accepted and passed raw to `reading.ocupacao_absoluta / cap * 100.0` before fusion clamps it. State integrity preserved by `fuse()`, but raw value is semantically invalid |
| `confianca_pct` (SensorReading) | Yes | `ge=0.0, le=100.0` + `clamp_confianca` validator | — |
| `confianca_ml` (ProsegurReading) | Yes | `ge=0.0, le=1.0` | — |
| `fila_actual` / `ocupacao_absoluta` (ProsegurReading) | Partial | `ge=0` only | No upper bound |
| `ChatRequest.mensagem` | Partial | `min_length=1` only — **no `max_length`** | 10 000-character message accepted and forwarded to Gemini API; could incur excess API cost or trigger provider-side limits |
| `ChatRequest.historico` | No | No size limit | Unbounded history list could be used to craft extremely large request bodies |
| `SimulateTickRequest.scenario` | Yes | Checked against `VALID_SCENARIOS` in router, raises 422 | — |
| `SimulateTickRequest.hora_simulada` | No | Optional string, no format validation (`"HH:MM"` only in doc comment) | Malformed hour string (e.g. `"25:99"`) passed to simulation engine |

### 1.7 Chat Failure Handling

| Scenario | Expected Behavior | Actual Behavior | Gap | Severity |
|---|---|---|---|---|
| Gemini configured, normal message | Gemini response | `{"resposta": "...", "fonte": "gemini"}` | None | — |
| Gemini call fails / key invalid | Graceful fallback to local engine | `services/chat.py` wraps Gemini call in `try/except Exception` and falls back to `_local_fallback()` | None | — |
| Very long message (10 000 chars) | Truncated or rejected | **Accepted and forwarded.** Response was `{"resposta":"Não foi possível processar...","fonte":"gemini"}` — Gemini returned a soft error but the server did not crash | No `max_length` guard on `mensagem`; no token-count truncation before API call | **MEDIUM** |
| Empty message (`""`) | 422 | 422 — `min_length=1` fires correctly | None | — |

### 1.8 Simulation Recovery

| Scenario | Expected Behavior | Actual Behavior | Gap | Severity |
|---|---|---|---|---|
| Invalid scenario name `"nonexistent_scenario"` | 422 with valid options listed | 422 — `"Cenário 'nonexistent_scenario' desconhecido. Válidos: [...]"` with full list | None | — |
| WC-05/F section injection (WC-05 is UNISSEX) | 422 | 422 — `"Cluster WC-05 é UNISSEX — apenas a secção 'U' é válida"` | None | — |

### 1.9 Error Handling Code Review

| Location | Finding | Severity |
|---|---|---|
| `main.py` `_simulation_loop` | Wrapped in `try/except Exception` with `logger.warning` — loop continues on any error. **Server survives** a bad tick | — |
| `main.py` startup | `evaluate_all_clusters` at startup called **without** `sensor_timestamps` — offline alerts impossible at startup | **HIGH** |
| `websocket.py` `broadcast_loop` | Wrapped in `try/except Exception` with `logger.warning` — broadcast continues on error | — |
| `websocket.py` per-client handler | `WebSocketDisconnect` + generic `Exception` caught; `finally` cleans up queue | — |
| `ingest.py` | All branches raise typed `HTTPException`; no bare exceptions | — |
| `prosegur.py` | All branches raise typed `HTTPException`; no bare exceptions | — |
| `simulate.py` | All branches raise typed `HTTPException`; no bare exceptions | — |
| **No global exception handler** | `@app.exception_handler` is not registered. FastAPI default handler returns Pydantic validation errors in full detail (field names, input values). **Internal field names are exposed to clients** | **LOW** |
| `ingest.py` line 112–113 | `ts_key` computed but **not stored**; sensor_readings stored per-cluster overwriting previous section | **HIGH** (offline detection broken) |

### 1.10 Load Test Results

| Test | Result | Notes |
|---|---|---|
| 100 concurrent GET `/clusters` | 100/100 OK, 0.03 s, **~3 600 req/s** | In-memory only, no DB bottleneck |
| 200 concurrent GET `/clusters` | 200/200 OK, 0.05 s, **~4 000 req/s** | Scales linearly |
| 50 concurrent POST `/sensor` | 50/50 OK, 0.02 s | Zero errors |
| 200 concurrent POST `/sensor` | 200/200 OK, 0.04 s, **~4 700 req/s** | |

---

## 2. Specific Findings

### 2.1 WS Reconnection Implementation Review

**Implementation is correct.**

```javascript
// onclose handler
_wsTimer = setTimeout(function() {
  _wsRetry = Math.min(_wsRetry * 2, 30000);
  _wsConnect();
}, _wsRetry);
// onopen resets
_wsConnected = true; _wsRetry = 1000;
```

- Initial delay: 1 000 ms
- Doubling sequence: 1 s → 2 s → 4 s → 8 s → 16 s → 30 s (cap)
- Max cap: **30 s — correct**
- Reset on reconnect: **correct**
- **Missing:** No random jitter. Under a full server restart with ~100 connected dashboards, all clients will attempt to reconnect at the same 1-second mark, creating a brief burst. At festival scale this is tolerable but worth noting.

### 2.2 Input Validation Coverage

**Well-validated:**
- `cluster_id`: whitelist of 8 valid IDs
- `section`: enum + unissex/misto cross-check at router level
- `source`: strict enum
- `contagem_entrada`, `contagem_saida`, `fila_actual`: `ge=0`
- `confianca_pct` (sensor): `ge=0, le=100` + clamping validator
- `confianca_ml` (Prosegur): `ge=0.0, le=1.0`
- `ChatRequest.mensagem`: `min_length=1`
- Simulation `scenario`: checked against `VALID_SCENARIOS`

**Not validated / incomplete:**
- `ocupacao_absoluta` (both `SensorReading` and `ProsegurReading`): `ge=0` only, no upper bound. Value 9 999 accepted; semantics preserved by fusion clamping but raw field is unconstrained.
- `ChatRequest.mensagem`: no `max_length`. Accepts arbitrary-length strings forwarded to Gemini API.
- `ChatRequest.historico`: no list size limit. Could be used to craft an extremely large request body.
- `SimulateTickRequest.hora_simulada`: no format validation; documented as `"HH:MM"` but any string accepted.
- `SectionState.ocupacao_absoluta`, `fila_actual`: no upper bound when stored in state (protected only by fusion layer logic).

### 2.3 Missing Error Handling — What Could Crash or Corrupt

| Risk | Location | Description |
|---|---|---|
| State divergence under multiple workers | `app_state` (global singleton) | If deployed with `uvicorn --workers 4` (or behind gunicorn), each process has its own in-memory state. There is **no shared store (Redis, Postgres)**. Sensor readings sent to worker A will not appear in worker B. Festival ops would see inconsistent dashboards. **Currently safe only as a single-worker process.** |
| Division by zero | `ingest.py` line 71, `prosegur.py` line 64 | `_get_capacity()` could return 0 for an unknown section. Both callers check `if cap > 0` — **correctly guarded.** |
| `hora_simulada` parsing | `simulation.py` | Malformed `"25:99"` string passed to `hora_simulada` — no format validation before use in the simulation engine. If the engine does `int(hora_simulada.split(':')[0])` and the string has no colon, it will raise `IndexError` or `ValueError`. The outer `_simulation_loop` try/except catches it and logs a warning — **server survives, but state is silently stale for that tick.** |
| Gemini API rate limits or quota | `services/chat.py` | Handled by `try/except Exception` fallback — **server survives**. |
| WebSocket queue overflow | `state.py` `broadcast()` | `asyncio.Queue(maxsize=10)` — if a client is too slow, its queue fills, it is silently removed from `ws_clients`, and the disconnect is not signalled to the client. Client will miss updates until its `onclose` fires naturally. Minor data-consistency gap. |

### 2.4 Sensor Offline Detection

**STATUS: PARTIALLY IMPLEMENTED — effectively MISSING in normal operation**

- The alert rule is **correctly implemented** in `services/alerts.py` (5-minute threshold, `SENSOR_OFFLINE_SECONDS = 300`).
- The alert **is NOT fired** by the background simulation loop (`main.py` `_simulation_loop`), which runs every 5 seconds and calls `evaluate_all_clusters` **without** `sensor_timestamps`. Because `last_sensor_ts` is `None`, the offline check is silently skipped on every automatic tick.
- The alert **is only fired** when a human or test script manually calls `POST /api/v1/simulate/tick`, which is the only code path that builds the `sensor_ts` dict and passes it to `evaluate_all_clusters`.
- **Second bug:** `app_state.sensor_readings` is keyed by `cluster_id`, not `"{cluster_id}_{section}"`. For a MISTO cluster (WC-01 through WC-04, WC-07, WC-08) that has both `M` and `F` sections, a reading from section `M` overwrites the entry for section `F`. If `M` is active and `F` is silent, `F` will never generate an offline alert because both sections use the same timestamp from the last `M` reading.

**Fix required:**
1. In `ingest.py`, store the timestamp in a per-section dict: `app_state.sensor_ts[f"{reading.cluster_id}_{reading.section}"] = reading.ts`
2. In `main.py` `_simulation_loop`, build the `sensor_ts` dict from that per-section store and pass it to `evaluate_all_clusters`.

### 2.5 Rate Limiting

**STATUS: NOT IMPLEMENTED**

There is no rate limiting anywhere in the codebase:
- No `slowapi` or equivalent middleware
- No per-IP, per-cluster-id, or per-endpoint throttle
- No request body size limit (FastAPI default is unlimited unless uvicorn is configured)

A single malicious or misconfigured IoT sensor could:
- POST to `/sensor` at 10 000 req/s, burning CPU
- POST to `/chat` with 10 000-character messages in a tight loop, exhausting the Gemini API quota
- POST to `/simulate/tick` repeatedly, causing rapid state mutations

**Recommendation:** Add `slowapi` with limits such as:
- `POST /sensor`: 1 000/minute per IP
- `POST /prosegur`: 500/minute per IP
- `POST /chat`: 60/minute per IP
- `POST /simulate/tick`: 120/minute per IP

### 2.6 Architecture Capacity Estimate — 50 000 Simultaneous Users

**Observed throughput (single process, single core):**
- GET `/clusters`: ~4 000 req/s
- POST `/sensor`: ~4 700 req/s

**Realistic festival load model:**
- 50 000 users on the dashboard = ~50 000 WebSocket connections
- WebSocket broadcast every 5 s = one fan-out to 50 000 queues per broadcast cycle
- `app_state.broadcast()` iterates the `ws_clients` set synchronously; at 50 000 clients this is a blocking loop of 50 000 `queue.put_nowait()` calls inside a single coroutine
- Estimated risk: `broadcast_loop` blocks the event loop for several hundred ms per cycle, degrading all REST API response times. **Single-process architecture is safe up to approximately 500–1 000 concurrent WebSocket clients.** Beyond that, WebSocket fan-out becomes a bottleneck.

**For 50 000 simultaneous dashboard users, the current architecture requires:**
1. Horizontal scaling behind a load balancer with sticky WebSocket sessions
2. A shared pub/sub backend (Redis pub/sub or similar) replacing the in-memory `ws_clients` set
3. Rate limiting on the chat endpoint to prevent Gemini quota exhaustion

---

## 3. Summary Table

| Finding | Severity | File | Fix |
|---|---|---|---|
| Sensor offline alerts never fire in background loop | **HIGH** | `app/main.py:124` | Pass `sensor_timestamps` to `evaluate_all_clusters` in `_simulation_loop` |
| `sensor_readings` stored per-cluster, not per-section | **HIGH** | `app/routers/ingest.py:113` | Key by `f"{cluster_id}_{section}"`; add `sensor_ts: Dict[str, float]` to `AppState` |
| No rate limiting on any endpoint | **MEDIUM** | `app/main.py` | Add `slowapi` middleware |
| `ocupacao_absoluta` has no upper bound in schema | **MEDIUM** | `app/schemas.py:151,180` | Add `le=` guard or cap at a reasonable maximum (e.g. 10 000) |
| `ChatRequest.mensagem` has no `max_length` | **MEDIUM** | `app/schemas.py:276` | Add `max_length=2000` |
| Multi-worker state divergence (no shared store) | **MEDIUM** | `app/state.py` | Document single-worker constraint; add Redis if scaling required |
| No global exception handler — Pydantic internals exposed | **LOW** | `app/main.py` | Add `@app.exception_handler(RequestValidationError)` to normalise 422 output |
| `ChatRequest.historico` has no size limit | **LOW** | `app/schemas.py:277` | Add `max_items=50` |
| `hora_simulada` no format validation | **LOW** | `app/schemas.py:252` | Add regex pattern `r"^[0-2]\d:[0-5]\d$"` |
| WS reconnection lacks jitter | **LOW** | `app/static/index.html:1539` | Add `Math.random() * 500` jitter to `setTimeout` delay |
| `confianca_ml` uses 0–1 scale (vs 0–100 % convention) | **LOW** (doc gap) | `app/schemas.py:182` | Add example value in field description |
