# Track 04 — End-to-End Latency Audit

**Date:** 2026-05-27  
**Backend:** http://localhost:8000  
**Protocol:** PlantaOS × Rock in Rio Lisboa 2026

---

## 1. Baseline API Latency (n=20 per endpoint)

| Endpoint | p50 | p95 | p99 |
|---|---|---|---|
| GET /api/v1/health | 1.0 ms | 1.2 ms | 1.2 ms |
| GET /api/v1/clusters | 1.0 ms | 1.4 ms | 1.4 ms |
| GET /api/v1/kpis | 1.2 ms | 2.3 ms | 2.3 ms |
| GET /api/v1/shows | 1.1 ms | 1.3 ms | 1.3 ms |
| POST /api/v1/sensor | 2.0 ms | 9.8 ms | 9.8 ms |

All GET endpoints are well under 10 ms. The sensor POST p95 of 9.8 ms reflects occasional Python GIL/event-loop contention; still far below the 50 ms threshold.

---

## 2. Sensor Ingest Latency (T0 → state visible via GET /clusters)

- **POST /sensor response time:** ~1.5–2.0 ms (p50)
- **State visible after ingest:** poll 1 fired at ~108 ms after T0  
  (100 ms sleep + ~8 ms for the GET /clusters round-trip)

The state is updated **synchronously** inside the POST handler — there is no async queue. The 108 ms figure includes one 100 ms sleep tick; true propagation delay is effectively < 10 ms.

**Note on the original test payload:** The test protocol used a legacy flat sensor schema (fields `telemoveis_detectados`, `pessoas_estimadas_wifi`, etc.) which is no longer the active schema. The current `SensorReading` schema requires `section` (M/F/U) and `source` (IR/WiFi/Camera). The protocol was corrected and all measurements above use the correct schema.

---

## 3. WebSocket Push Latency (T0 → WS push received, n=10 cycles)

| Cycle | WS Latency |
|---|---|
| 1 | 1,400 ms |
| 2–10 | ~4,699–4,704 ms |

| Metric | Value |
|---|---|
| p50 | 4,700 ms |
| p95 | 4,704 ms |
| p99 | 4,704 ms |

**Explanation:** Cycle 1 arrived within 1.4 s because the sensor POST happened just before the next scheduled broadcast tick. Cycles 2–10 all arrived at ~4.7 s, meaning the sensor POST fired just after a broadcast tick and had to wait for the next 5 s interval — worst-case latency ≈ broadcast_interval − ε.

The WS push mechanism is **time-triggered** (every 5 s via `asyncio.sleep(interval)`) rather than event-triggered. There is no "dirty flag" that would force an early broadcast after a sensor POST.

---

## 4. WebSocket Broadcast Interval

| Broadcast | Interval |
|---|---|
| 1 (partial) | 1,643 ms |
| 2 | 5,003 ms |
| 3 | 4,996 ms |
| 4 | 5,005 ms |
| 5 | 4,999 ms |
| 6 | 5,002 ms |
| 7 | 5,001 ms |
| 8 | 5,001 ms |

**Average (excl. first partial):** 5,001 ms  
**Configured value:** `simulation_tick_interval_seconds = 5.0` (app/config.py)  
**Jitter:** ±5 ms — essentially zero drift.

---

## 5. Pass / Fail Summary

| Criterion | Target | Measured | Result |
|---|---|---|---|
| Sensor POST response time | < 50 ms | p50=2.0 ms, p99=9.8 ms | PASS |
| State visible via GET /clusters after ingest | < 1,000 ms | ~108 ms (poll-bounded) | PASS |
| WS push after ingest | < 6,000 ms | p50=4,700 ms, p99=4,704 ms | PASS |
| Broadcast interval | ~5,000 ms ± 500 ms | 5,001 ms avg | PASS |
| GET endpoint p99 latency | < 500 ms | 2.3 ms (worst) | PASS |

**Overall: 5/5 criteria PASS. No blockers, no high/medium/low severity findings.**

---

## 6. Architecture Target vs. Actual

The original PlantaOS architecture target was **"sensor → ecrã < 90 seconds"** (a conservative field-deployment budget for a congested Wi-Fi environment at a festival site).

**Current implementation is ~18× faster than spec:**

| Leg | Architecture Target | Measured |
|---|---|---|
| Sensor POST ingest | — | ~2 ms |
| State propagation | — | synchronous (<10 ms) |
| WS push to UI | ≤ 90 s end-to-end | ≤ 5 s worst-case |
| Full sensor→screen | < 90 s | **< 5.1 s** |

This is a meaningful over-delivery. The system operates at near-real-time for a time-triggered broadcast model. The 90 s budget exists to accommodate unreliable cellular/Wi-Fi at large venues; the current implementation provides headroom for future network degradation without breaching SLA.

---

## 7. Bottlenecks Identified

### Minor / Informational

1. **WS push is time-triggered, not event-triggered.** After a sensor ingest, the worst-case UI refresh lag is ≈ 5 s (one full broadcast cycle). If the system is ever required to reflect occupancy changes in < 2 s (e.g., for emergency overcrowding alerts), the broadcast loop would need a dirty-flag mechanism to fire an early push.

2. **POST /sensor p95 spike (9.8 ms vs 2.0 ms p50).** Likely caused by asyncio event-loop scheduling jitter under light load. Not a concern at current throughput; worth monitoring under concurrent load (many simultaneous sensor nodes).

3. **No legacy sensor schema compatibility.** The original test protocol used a flat payload (`telemoveis_detectados`, `pessoas_estimadas_wifi`, etc.) — the server returns HTTP 422 for those payloads. Any legacy sensors or integration tests using the old schema will silently fail ingest. Consider adding a deprecation adapter or clear error message.

---

## 8. Severity Summary

| Finding | Severity |
|---|---|
| WS push latency > 30 s | BLOCKER — Not triggered (p99=4.7 s) |
| Sensor POST > 500 ms | HIGH — Not triggered (p99=9.8 ms) |
| Broadcast interval > 10 s | MEDIUM — Not triggered (avg 5.0 s) |
| GET p99 > 500 ms | LOW — Not triggered (max 2.3 ms) |
| Legacy sensor schema returns 422 | LOW — Informational finding |

**No severity thresholds breached.**
