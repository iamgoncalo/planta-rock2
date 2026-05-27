# Track 06 — Per-Cabin Reed Switch API
**PlantaOS × Rock in Rio Lisboa 2026 — Quality Audit**
Date: 2026-05-27 | Author: Claude (automated track)

---

## 1. Files Created

| Path | Purpose |
|------|---------|
| `backend/app/schemas_cabins.py` | Pydantic v2 schemas for cabin-level data (CabinType, CabinState, CabinAnomaly, CabinClusterSummary, CabinClusterResponse) |
| `backend/app/routers/cabins.py` | FastAPI router implementing GET /api/v1/cabins/{cluster_id} with deterministic simulation |
| `backend/tests/test_cabins.py` | 32 new pytest tests covering counts, section invariants, uniqueness, schema, and error cases |

**app/main.py was NOT modified** (per task spec).

---

## 2. Integration Instructions for app/main.py

Add the import at **line 32** (after the existing router imports, before the closing parenthesis):

```python
# In app/main.py — imports block starting at line 22
from app.routers import (
    chat,
    cabins,          # ← ADD THIS LINE
    clusters,
    health,
    ingest,
    kpis,
    prosegur,
    shows,
    simulate,
    websocket as ws_router,
)
```

Add the router registration at **line 179** (after `ws_router.router`, before the `# Serve the dashboard HTML` comment):

```python
    # app/main.py — create_app() function, router registration block
    app.include_router(ws_router.router, prefix=prefix)
    app.include_router(cabins.router, prefix=prefix)   # ← ADD THIS LINE (after line 179)
```

Both changes are additive — no existing lines need to be removed or modified.

---

## 3. API Contract — GET /api/v1/cabins/{cluster_id}

### Request

```
GET /api/v1/cabins/{cluster_id}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| cluster_id | path string | yes | WC cluster identifier: WC-01 … WC-08 |

### Response — 200 OK

```json
{
  "cluster_id": "WC-06",
  "ts": 1750420860,
  "simulado": true,
  "cabins": [
    {
      "id": "WC-06/U/ACC.1",
      "type": "accessible",
      "section": "U",
      "occupied": false,
      "occupied_since_s": null,
      "last_occupied_s_ago": 42
    },
    {
      "id": "WC-06/U/STD.1",
      "type": "standard",
      "section": "U",
      "occupied": true,
      "occupied_since_s": 87,
      "last_occupied_s_ago": null
    }
  ],
  "anomalies": [
    {
      "cabin_id": "WC-06/U/STD.7",
      "type": "long_occupation",
      "duration_s": 723,
      "message": "Cabine ocupada há 12min — verificar"
    }
  ],
  "summary": {
    "total": 40,
    "occupied": 22,
    "free": 18,
    "accessible_free": 2,
    "avg_occupation_time_s": 92,
    "longest_occupation_s": 723
  }
}
```

### Response — 404 Not Found

```json
{ "detail": "Cluster 'WC-99' not found. Valid values: ['WC-01', 'WC-02', ...]" }
```

### Cabin ID Format

```
{cluster_id}/{section}/{TYPE_ABBREV}.{n}
```

| Abbreviation | Type | Description |
|---|---|---|
| ACC | accessible | PMR-accessible cabin |
| STD | standard | Standard-width cabin |
| WID | wide | Wider cabin |
| END | end | End-of-row cabin |
| CAL | calha | Urinal trough section (float switch) |

### Cabin Counts per Cluster

| Cluster | Layout | Enclosed | Calha | Total |
|---------|--------|----------|-------|-------|
| WC-01 | M: 3acc+8std+3wide+1end / F: 2acc+10std+3wide+1end | 31 | 0 | 31 |
| WC-02 | M: 2acc+6std / F: 2acc+14std+2wide | 26 | 0 | 26 |
| WC-03 | M: 2acc+7std / F: 2acc+9std+1end | 21 | 0 | 21 |
| WC-04 | M: 2acc+12std+2wide / F: 2acc+12std+2end | 32 | 0 | 32 |
| WC-05 | U: 2acc+20std+4wide+1end | 27 | 0 | 27 |
| WC-06 | U: 3acc+24std+6wide+1end + 6 calha | 34 | 6 | 40 |
| WC-07 | M: 2acc+15std+1end / F: 2acc+8std+4wide | 32 | 0 | 32 |
| WC-08 | M: 2acc+12std+2wide / F: 2acc+9std+1end | 28 | 0 | 28 |

**Note on WC-07:** Floor plan lists 4 std_large + 11 std in the Male section; these are merged into 15 standard-type slots in the model since both use the same Reed switch circuit.

**Note on WC-06 calha:** The brief counts "34 cabin positions" referring to enclosed door-equipped units only. The router tracks all 40 monitored positions (34 enclosed + 6 calha float switches). The test suite verifies both figures explicitly.

### Simulation Logic

The simulation is deterministic within a UTC hour:

```
seed = hash(cluster_id + str(hour)) & 0xFFFFFFFF
rng  = random.Random(seed)
```

For each cabin:
1. Read section occupancy % from `app_state.cluster_states[cluster_id].secoes[section].ocupacao_pct`
2. Probability of occupied = occupancy_pct / 100 (calha: × 0.8)
3. The first accessible cabin per section is always kept free (reserved)
4. Occupied cabins receive `occupied_since_s` ∈ [30, 900] s
5. 35 % of free cabins receive `last_occupied_s_ago` ∈ [0, 120] s
6. Any cabin with `occupied_since_s > 600` raises a `long_occupation` anomaly

### Invariants enforced

- `summary.occupied + summary.free == summary.total` (verified by test)
- All cabin IDs are unique within a cluster (verified by test)
- 404 returned for unknown cluster IDs
- Section "U" only for WC-05/WC-06; "M"+"F" for all others

---

## 4. Test Results

```
172 passed in 13.76s
```

- 140 pre-existing tests: all pass (no regression)
- 32 new cabin tests: all pass

### New test breakdown

| Class | Tests |
|-------|-------|
| TestWC01CabinCount | 3 |
| TestWC05Unissex | 3 |
| TestWC06CabinCount | 3 |
| TestUnknownCluster | 2 |
| TestOccupancyInvariant | 8 (parametrized) |
| TestCabinIdUniqueness | 8 (parametrized) |
| TestResponseSchema | 5 |
| **Total** | **32** |

---

## 5. UI Mockup — ASCII Cabin State Grid (WC-06, snapshot)

```
WC-06 / U — W39/S39  [SIMULATED]   2026-05-27 HH:xx UTC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  PMR   [■] ACC.1*  [□] ACC.2  [□] ACC.3*
        * = reserved (always free)

  STD   [■][□][■][■][□][■][■][□][■][■][□][■]
        [■][■][□][■][■][■][□][□][■][□][■][■]

  WIDE  [□][■][■][□][■][□]

  END   [■]

  CALHA ▓▓░▓▓▓░▓▓░▓  (float switch — trough sections 1-6)
        ▓ = flow detected   ░ = dry

  ┌─────────────────────────────────────────────────┐
  │  Total: 40  Occupied: 27  Free: 13             │
  │  Accessible free: 2                            │
  │  Avg occupation: 94s   Longest: 723s ⚠         │
  └─────────────────────────────────────────────────┘

  Legend:  [■] Occupied   [□] Free   [■⚠] Anomaly (>10min)
```

```
WC-01 / M — V34 Near P1  [SIMULATED]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  PMR   [□] ACC.1*  [■] ACC.2  [■] ACC.3
  STD   [■][□][■][■][□][■][■][□]
  WIDE  [■][□][■]
  END   [□]

WC-01 / F — V34 Near P1  [SIMULATED]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  PMR   [□] ACC.1*  [■] ACC.2
  STD   [■][□][■][■][□][■][■][□][■][■]
  WIDE  [■][□][■]
  END   [■]
```

---

## 6. Future Hardware Plan — MC-38 Reed Switches on LilyGo ESP32

### Hardware Overview

**MC-38 Reed Magnetic Contact Switch**
- N/O (normally open) when door is unlocked/open
- Closes when magnet aligns with door in latched position
- Supply: 3.3 V logic — direct GPIO compatible with ESP32
- Max current: 0.5 A / 100 VDC (signal only at 3.3 V → 1 mA pull-down)

### Wiring Diagram (per board)

```
    MC-38 Switch (door latch)
    ┌─────────┐
    │ MAGNET  │ ← attached to door
    └─────────┘
         ↕ (magnetic field closes switch)
    ┌─────────┐
    │  REED   │ ─── GPIO_PIN ──→ LilyGo ESP32-C3
    │ CONTACT │ ─── GND
    └─────────┘

    LilyGo ESP32-C3 GPIO (INPUT_PULLUP mode):
      GPIO pin → MC-38 → GND
      HIGH = door open (switch open, pull-up active)
      LOW  = door latched (switch closed, circuit complete)
```

### Board Assignment (one ESP32-C3 per cluster)

| Cluster | Board ID | GPIO pins needed | Notes |
|---------|----------|-----------------|-------|
| WC-01 | ESP-WC01 | 31 | I²C expander (PCF8574) recommended for >8 pins |
| WC-02 | ESP-WC02 | 26 | PCF8574 × 4 |
| WC-03 | ESP-WC03 | 21 | PCF8574 × 3 |
| WC-04 | ESP-WC04 | 32 | PCF8574 × 4 |
| WC-05 | ESP-WC05 | 27 | PCF8574 × 4 |
| WC-06 | ESP-WC06 | 40 | PCF8574 × 5 + 1 float switch for calha |
| WC-07 | ESP-WC07 | 32 | PCF8574 × 4 |
| WC-08 | ESP-WC08 | 28 | PCF8574 × 4 |

**PCF8574 I²C GPIO Expander** (8 pins each, stackable via address jumpers A0-A2):
- Up to 8 boards per I²C bus → 64 GPIO pins per ESP32-C3
- Address range: 0x20–0x27

### Firmware Behaviour

```
Loop (every 500 ms):
  1. Read all GPIO states via PCF8574 burst read
  2. Debounce: state must be stable for 2 consecutive reads (1 s)
  3. Build bitmask: bit[i] = 1 if cabin[i] is OCCUPIED
  4. If any bit changed since last publish:
       POST /api/v1/ingest/cabins
       {
         "cluster_id": "WC-06",
         "ts": <unix_ms>,
         "bitmask": "0b1101011...",   // one bit per cabin, ordered by cabin ID
         "board_id": "ESP-WC06",
         "fw_version": "1.0.0"
       }
  5. Heartbeat (even if no change): publish every 30 s
```

### Backend Changes Required (post-hardware)

1. **New endpoint:** `POST /api/v1/ingest/cabins` — receives bitmask, updates `app_state.cabin_states[cluster_id]`
2. **New state dict:** `app_state.cabin_states: Dict[str, List[bool]]`
3. **cabins.py router update:** check `app_state.cabin_states.get(cluster_id)` first; fall back to simulation if absent; set `simulado=False` when real data available
4. **OTA updates:** LilyGo boards accept firmware updates via `/api/v1/ingest/ota/{board_id}` (not yet implemented)

### Calha Sections (WC-06, WC-07)

Urinal troughs use a **float switch** (not MC-38) wired to a single GPIO per trough section:
- Float LOW = trough in use (water flow detected)
- Reported as `CabinType.CALHA` with the same occupied/free logic

---

## 7. Issues Found

| Severity | Location | Description |
|----------|----------|-------------|
| NONE | — | No blockers. No existing tests broken. All 172 tests pass. |

### Notes

- **WC-06 total is 40, not 34:** The task brief says "34 cabin positions" referring to enclosed door-equipped units. The router counts all 40 monitored positions (34 + 6 calha). Both figures are verified in the test suite with explicit comments explaining the discrepancy.
- **WC-07 std_large merging:** Floor plan lists 4 std_large + 11 std for Male section. These share identical Reed switch wiring so they are merged as 15 × STANDARD in the model. The distinction can be reintroduced by adding a `STD_LARGE` value to `CabinType` when hardware is installed.
- **Simulation seed stability:** The hour-based seed means cabin states rotate every UTC hour. For the live event a finer-grained seed (e.g. 15-min buckets) may be preferable.
