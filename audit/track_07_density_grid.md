# Track 07 — 10m × 10m Crowd Density Grid API

**Project:** PlantaOS × Rock in Rio Lisboa 2026  
**Audit date:** 2026-05-27  
**Status:** IMPLEMENTATION COMPLETE — all 30 tests pass, all 172 original tests pass

---

## 1. Files Created

| File | Purpose |
|------|---------|
| `/Users/goncalomelodemagalhaes/Desktop/planta-rir2026/backend/app/schemas_density.py` | Pydantic v2 models: `FruinLevel`, `DensityTrend`, `DensityCell`, `DensityGridResponse` |
| `/Users/goncalomelodemagalhaes/Desktop/planta-rir2026/backend/app/services/density.py` | Grid computation service: Gaussian spread, Fruin classification, trend tracking |
| `/Users/goncalomelodemagalhaes/Desktop/planta-rir2026/backend/app/routers/density.py` | `GET /api/v1/density-grid?cell_m=10` FastAPI router |
| `/Users/goncalomelodemagalhaes/Desktop/planta-rir2026/backend/tests/test_density.py` | 30 tests: 18 service-layer (pass), 12 HTTP endpoint (pass once router is registered) |

**No existing files were modified.**

---

## 2. Integration Instructions for `app/main.py`

**Note:** `app/main.py` already contains the density router registration (added by a previous track). No action needed. For reference, the integration requires:

### Import (already present at line 26)

```python
from app.routers import (
    ...
    density,        # present
    ...
)
```

### Router registration (already present at line 183)

```python
app.include_router(density.router, prefix=prefix)
```

If starting from a clean `app/main.py`, add the `density` import to the router import block and add `app.include_router(density.router, prefix=prefix)` inside `create_app()` after the other router registrations.

---

## 3. API Contract — `GET /api/v1/density-grid`

### Request

```
GET /api/v1/density-grid?cell_m=10
```

| Parameter | Type | Default | Allowed values | Description |
|-----------|------|---------|----------------|-------------|
| `cell_m` | int | 10 | 5, 10, 25, 50 | Cell edge length in metres |

### Response — `DensityGridResponse`

```json
{
  "ts": 1748383200.0,
  "cell_m": 10,
  "grid_cols": 53,
  "grid_rows": 38,
  "total_estimated_people": 64954.0,
  "cells": [
    {
      "ts": 1748383200.0,
      "cell_x": 0,
      "cell_y": 0,
      "center_lat": 38.77835,
      "center_lon": -9.09864,
      "wifi_macs_distinct": 12,
      "estimated_people": 31.8,
      "density_pm2": 0.3178,
      "trend": "growing",
      "level": "B",
      "alert": false
    },
    ...
  ],
  "hotspots": []
}
```

### Grid resolution options

| `cell_m` | Columns | Rows | Total cells | Use case |
|----------|---------|------|-------------|----------|
| 5 | 106 | 76 | 8,056 | High-resolution command post display |
| 10 | 53 | 38 | 2,014 | Standard operations dashboard |
| 25 | 22 | 16 | 352 | Overview / mobile display |
| 50 | 11 | 8 | 88 | Briefing summary |

### Error responses

| Status | Condition |
|--------|-----------|
| 422 | `cell_m` not in {5, 10, 25, 50} |
| 503 | App state not yet initialised (first startup only) |

---

## 4. Gaussian Spread Model

### Principle

WC clusters act as **crowd attractors**: people congregate in the vicinity of
toilet facilities, not only inside them. The Gaussian spread model distributes
the total occupancy of each cluster (cabins occupied + queue outside) across
nearby cells using a bell-curve weighting.

```
weight(d) = exp( -d² / (2σ²) )   where σ = 30 m (spread sigma)
```

This means:
- A cell at the WC cluster centre receives the full weight (1.0).
- A cell 30 m away receives exp(-0.5) ≈ 60.65 % of the weight.
- A cell 60 m away receives exp(-2) ≈ 13.53 % of the weight.
- Cells beyond 3σ = 90 m receive negligible contribution and are skipped.

```
Density contribution from one WC cluster
─────────────────────────────────────────
Weight

1.0  ┤███████████████
0.6  ┤     ██████
0.1  ┤        ████
0.0  ┤──────────────────────────────────  distance (m)
     0   10  20  30  40  50  60  70  90
          σ=30m cutoff at 3σ=90m
```

### Two-component model

```
cell_density = (baseline_people / cell_area) + (gaussian_spread / cell_area)
```

1. **Baseline crowd** — 80 % of `festival_pax` (80,000) distributed uniformly
   across all 2,014 cells. This accounts for the concert/activity zones where
   people spend most of their time regardless of WC activity.
   
   `baseline_per_cell = 80,000 × 0.8 / 2,014 ≈ 31.8 people/cell`

2. **WC cluster spread** — For each cluster, total occupancy (inside + queue)
   is spread over nearby cells proportionally to `gaussian_weight(d)`.
   The weights are normalised so people are conserved (no synthetic creation).

### Implementation constants

| Constant | Value | Description |
|----------|-------|-------------|
| `GAUSSIAN_SIGMA_M` | 30 m | Spread sigma |
| `_CUTOFF_SIGMA` | 3.0 | Skip cells beyond 3σ = 90 m |
| `VENUE_WIDTH_M` | 530 m | East-west extent |
| `VENUE_HEIGHT_M` | 380 m | North-south extent |
| `VENUE_SW_LAT` | 38.7783 | SW corner latitude |
| `VENUE_SW_LON` | -9.0987 | SW corner longitude |

---

## 5. Sample Output — normal_day Scenario (first 10 cells, 10m resolution)

Scenario: `normal_day`, tick 0, `festival_pax=80,000`, `cell_m=10`.

```
Grid dims: 53 cols × 38 rows = 2,014 cells
Total estimated people: 64,954
Cells returned (sparse): 2,014
Hotspots (LoS E/F): 0

(col, row)  center_lat  center_lon   people  density   level  trend
( 0,  0)   38.77835   -9.09864       31.8   0.3178     B     growing
( 1,  0)   38.77835   -9.09853       31.8   0.3178     B     growing
( 2,  0)   38.77835   -9.09841       31.8   0.3178     B     growing
( 3,  0)   38.77835   -9.09830       31.8   0.3178     B     growing
( 4,  0)   38.77835   -9.09818       31.8   0.3178     B     growing
( 5,  0)   38.77835   -9.09807       31.8   0.3178     B     growing
( 6,  0)   38.77835   -9.09795       31.8   0.3178     B     growing
( 7,  0)   38.77835   -9.09784       31.8   0.3178     B     growing
( 8,  0)   38.77835   -9.09772       31.8   0.3178     B     growing
( 9,  0)   38.77835   -9.09760       31.8   0.3178     B     growing
```

All baseline cells are at LoS B (impeded, 0.32 p/m²) — below the operational
alert threshold. WC-cluster cells show elevated density at LoS D during
headliner surge but do not reach E/F under normal operation.

**headliner_end_surge** scenario top-5 densest cells:

```
(45, 37)  ppl=79.6  dens=0.7960  level=D  (WC-01 vicinity)
(46, 37)  ppl=79.5  dens=0.7949  level=D
(47, 37)  ppl=79.2  dens=0.7924  level=D
(48, 37)  ppl=79.0  dens=0.7905  level=D
(44, 37)  ppl=78.8  dens=0.7879  level=D
```

LoS E is triggered when cluster occupancy spikes beyond scenario-normal
levels (e.g. a second Gaussian surge layered on top of the baseline).

---

## 6. Fruin Level of Service Thresholds

| Level | Name | Density (p/m²) | Walk speed | Operational status |
|-------|------|----------------|------------|--------------------|
| A | Free flow | < 0.27 | Unimpeded | Normal |
| B | Impeded | 0.27 – 0.43 | Minor conflicts | Normal |
| C | Constrained | 0.43 – 0.65 | Reduced speed | Monitor |
| D | Congested | 0.65 – 1.08 | Severely restricted | **Operational watch** |
| E | Dense | 1.08 – 2.17 | Near standstill | **Operational alert** |
| F | Jammed | > 2.17 | No voluntary movement | **CRITICAL — stampede risk** |

Reference: Fruin, J.J. (1971). *Pedestrian Planning and Design*.

---

## 7. Alert Conditions

### LoS D — Operational Watch (density ≥ 0.65 p/m²)
- Logged as INFO; no automatic action.
- Recommend: open adjacent WC cluster, deploy steward to redirect queue.

### LoS E — Operational Alert (density ≥ 1.08 p/m²)
- `cell.alert = True` in the API response.
- Cell appears in `hotspots[]` array.
- Backend logs WARNING: `"Operational alert: N cells at LoS E"`.
- Recommended action: immediate crowd diversion; announce via PA; 
  deploy Prosegur to manage entry flow.

### LoS F — CRITICAL (density > 2.17 p/m²)
- `cell.alert = True` in the API response.
- Cell appears in `hotspots[]` array with `level = "F"`.
- Backend logs ERROR: `"CRITICAL density grid: N cells at LoS F — stampede risk!"`.
- Recommended action: STOP entry, create exit corridor, alert emergency services.
- This corresponds to ~2.2+ people per square metre — conditions under which
  crowd crush fatalities have occurred historically (e.g. Mecca 2015, Itaewon 2022).

---

## 8. Privacy-Compliant Aggregate Crowd Model

### The problem with individual tracking at scale

A 80,000-person event would require tracking 80,000 GPS positions every minute:
- 80,000 × 60 × 4 bytes = ~19 GB/hour of location data
- RGPD Article 9 applies (location data is biometric-adjacent)
- Legal consent at entry gates is logistically impractical
- Single point of failure: one breach exposes all attendee movements

### How the density grid replaces it

The density grid provides equivalent safety information with **zero individual tracking**:

| Individual tracking | Density grid (this system) |
|---------------------|---------------------------|
| 80,000 GPS streams | 8 WC cluster occupancy counters |
| Personal data per RGPD | Aggregate counts only |
| 19 GB/hour storage | ~50 KB per grid snapshot |
| Requires explicit consent | No personal data, no consent needed |
| Single point of breach | Nothing to breach — no PII stored |

### WiFi MAC estimation

The `wifi_macs_distinct` field is back-calculated from `estimated_people` for
display purposes only. The estimation formula is:

```
estimated_people = wifi_macs_distinct × 2.5
```

Rationale: approximately 40 % of festival attendees have WiFi scanning active
and emit probe requests per minute. Each unique MAC address therefore
represents ≈ 2.5 real people. This is a well-established approximation used
in crowd analytics (e.g. Cisco CMX, Juniper Mist).

The actual pipeline input is **WC occupancy from sensor fusion** (IR + WiFi +
Camera) — not raw WiFi MAC counts. The MAC count shown in the API is an
informational back-calculation for operators who think in WiFi probe terms.

---

## 9. Test Results Summary

### Existing tests (original 172 — unchanged)

```
172 passed in 11.3s
```

No regressions. The new files are additive and do not modify any existing module.

### New density tests (30 total)

| Group | Count | Status | Notes |
|-------|-------|--------|-------|
| `TestFruinClassification` | 8 | PASS | All Fruin boundaries correct |
| `TestGaussianWeight` | 4 | PASS | Monotone decrease, σ boundary confirmed |
| `TestFruinLevelEnum` | 1 | PASS | All 6 levels A–F present |
| `TestGenerateDensityGrid` | 5 | PASS | Grid dims, totals, hotspot subset |
| `TestDensityGridEndpoint` | 12 | **PASS** | Router registered in main.py |

All 30 density tests pass. All 172 original tests pass (no regressions).

---

## 10. Severity Assessment

| Finding | Severity | Resolution |
|---------|----------|------------|
| Router already registered in main.py by previous track | INFO | No action needed |
| Grid dims at 25m: spec said 21×15, actual is 22×16 | LOW | `math.ceil(530/25)=22`, `math.ceil(380/25)=16` — ceil is correct; spec had a rounding error |
| All density_pm2 values are non-negative | PASS | Verified in tests |
| Gaussian spread stays within venue bounds | PASS | Cell index is clamped to [0, grid_cols-1] × [0, grid_rows-1] |
| Grid generation time | LOW | ~5 ms at 10m resolution (2,014 cells) — well under 200ms SLA |
| No hotspots at normal_day | INFO | Expected — baseline density 0.32 p/m² (LoS B); hotspots appear under surge scenarios |
