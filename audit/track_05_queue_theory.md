# Track 05 — Queue Theory Audit
## PlantaOS × Rock in Rio Lisboa 2026

**Audited:** 2026-05-27  
**Scope:** `/backend/app/services/simulation.py`, `/backend/app/services/fusion.py`, `/backend/app/schemas.py`, `/backend/app/data/clusters.py`  
**Result:** 3 BLOCKER findings, 1 HIGH finding, 1 MEDIUM finding

---

## 1. Queueing Model Actually Implemented

The simulation uses **none of the standard queueing models** (M/M/1, M/M/c, M/D/1). It is an **ad hoc heuristic** with three independently computed metrics that are not mutually consistent.

### Queue length (fila) — simulation.py lines 240–242
```python
base_queue = max(0.0, (occ_pct - 60.0) * 0.8)   # queue starts above 60%
fila = int(round(base_queue * queue_mult + _noise(seed ^ 0x1, tick) * 10))
fila = max(0, fila)
```
Queue is derived from occupancy percentage with a manual threshold at 60%. No relationship to arrival rate or service rate.

### Wait time (tempo_espera) — simulation.py lines 244–246
```python
throughput = 8.0
tempo_espera = fila / throughput if fila > 0 else 0.0
```
Wait time = queue / 8.0. The value `8.0` is hardcoded and undocumented. It does not represent any physical throughput parameter (not μ, not c×μ, not λ).

### Arrival rate (fluxo_entrada) — simulation.py line 249
```python
fluxo_entrada = max(0.0, occ_pct * 0.25 + _noise(seed ^ 0x2, tick) * 20)
```
Arrival rate is a linear function of occupancy percentage. At 70% occupancy this yields ~17–20 people/min per section.

### Why these three cannot be consistent
For Little's Law (L = λ × W) to hold with the current formulas:

```
L = λ × W
L = (occ_pct × 0.25) × (L / 8.0)
8 = occ_pct × 0.25
occ_pct = 32%
```

**Little's Law only holds at exactly 32% occupancy.** At typical operational occupancy (65–80%) λ ≈ 17–20, not 8, causing a systematic ~110–140% violation across all sections.

---

## 2. Little's Law Verification — All 14 Sections VIOLATED

Test against API snapshot (normal_day scenario, ~70% occupancy).

| Section | L (actual) | λ (arr/min) | W (min) | λ×W (predicted L) | Error % |
|---------|-----------|------------|---------|-------------------|---------|
| WC-01/M | 11 | 17.8 | 1.4 | 24.9 | **127%** |
| WC-01/F | 8 | 16.7 | 1.0 | 16.7 | **109%** |
| WC-02/M | 7 | 18.1 | 0.9 | 16.3 | **133%** |
| WC-02/F | 11 | 18.0 | 1.4 | 25.2 | **129%** |
| WC-03/M | 13 | 19.6 | 1.6 | 31.4 | **141%** |
| WC-03/F | 10 | 17.2 | 1.2 | 20.6 | **106%** |
| WC-04/M | 12 | 19.4 | 1.5 | 29.1 | **143%** |
| WC-04/F | 13 | 19.0 | 1.6 | 30.4 | **134%** |
| WC-05/U | 9 | 18.8 | 1.1 | 20.7 | **130%** |
| WC-06/U | 6 | 17.4 | 0.8 | 13.9 | **132%** |
| WC-07/M | 12 | 19.2 | 1.5 | 28.8 | **140%** |
| WC-07/F | 13 | 18.3 | 1.6 | 29.3 | **125%** |
| WC-08/M | 13 | 19.1 | 1.6 | 30.6 | **135%** |
| WC-08/F | 10 | 17.9 | 1.2 | 21.5 | **115%** |

**Verdict: 14/14 sections VIOLATE Little's Law by >50%. This is a BLOCKER.**

The violation is not noise or rounding — it is structurally guaranteed by the formula choices as shown above.

---

## 3. M/M/c Utilization at Current Simulated Occupancy

Using μ = 1/3 persons/min per cabin (3-minute average service time), ρ = λ / (c × μ).

| Section | λ (arr/min) | c (cabins) | μ_total (cap/min) | ρ | Status |
|---------|------------|-----------|-------------------|---|--------|
| WC-01/M | 17.8 | 72 | 24.0 | 0.742 | STABLE |
| WC-01/F | 16.7 | 63 | 21.0 | 0.795 | STABLE |
| WC-02/M | 18.1 | 54 | 18.0 | **1.006** | **OVERLOADED** |
| WC-02/F | 18.0 | 72 | 24.0 | 0.750 | STABLE |
| WC-03/M | 19.6 | 54 | 18.0 | **1.089** | **OVERLOADED** |
| WC-03/F | 17.2 | 48 | 16.0 | **1.075** | **OVERLOADED** |
| WC-04/M | 19.4 | 84 | 28.0 | 0.693 | STABLE |
| WC-04/F | 19.0 | 66 | 22.0 | 0.864 | NEAR-CRITICAL |
| WC-05/U | 18.8 | 133 | 44.3 | 0.424 | STABLE |
| WC-06/U | 17.4 | 208 | 69.3 | 0.251 | STABLE |
| WC-07/M | 19.2 | 84 | 28.0 | 0.686 | STABLE |
| WC-07/F | 18.3 | 54 | 18.0 | **1.017** | **OVERLOADED** |
| WC-08/M | 19.1 | 84 | 28.0 | 0.682 | STABLE |
| WC-08/F | 17.9 | 61 | 20.3 | 0.880 | NEAR-CRITICAL |

**4 sections at ρ ≥ 1.0 even during "normal_day" scenario.** This contradicts the API showing these sections as "moderado" (moderate). The simulation is reporting stable-looking queues for theoretically unbounded queues (ρ ≥ 1 → infinite expected wait).

The explanation: the simulation generates λ as a fraction of occupancy without checking whether λ < c×μ. So the API can simultaneously show "moderado" occupancy with ρ > 1 — a physically impossible state.

---

## 4. Correct Formulas vs Current Implementation

### 4a. Wait time formula that should be used

**Current (simulation.py line 245–246):**
```python
throughput = 8.0
tempo_espera = fila / throughput
```

**Correct — Erlang-C formula for M/M/c:**

```
Given:
  λ  = arrival rate (persons/min) — use fluxo_entrada_pmin
  μ  = 1/avg_service_time = 1/3 persons/min per cabin
  c  = number of cabins for this section
  ρ  = λ / (c × μ)   (must be < 1 for a stable queue)

Erlang-C probability (prob a customer must wait):
  A  = λ / μ  (offered traffic in Erlangs)
  
  P_C = [ (A^c / (c! × (1-ρ))) ] / [ Σ_{n=0}^{c-1} A^n/n!  +  A^c/(c!×(1-ρ)) ]

Expected wait in queue:
  W_q = P_C / (c × μ - λ)

Total sojourn time (wait + service):
  W   = W_q + 1/μ
```

**Minimum viable fix (maintains Little's Law at least):**
```python
# Replace lines 244-246 in simulation.py:
# tempo_espera = fila / fluxo_entrada if fluxo_entrada > 0 else 0.0
```
This ensures W = L/λ, which trivially satisfies L = λ × W.

### 4b. M/M/c Erlang-C wait time comparison

For stable sections (ρ < 1), the Erlang-C formula yields near-zero expected queue wait because all clusters have large c (48–208 cabins) relative to arrival rates (~17–20/min):

| Section | c | ρ | W_code (current) | W_Erlang-C (correct) | Overestimate ratio |
|---------|---|---|-----------------|---------------------|-------------------|
| WC-01/M | 72 | 0.742 | 1.4 min | 0.0016 min | **884× (BLOCKER)** |
| WC-01/F | 63 | 0.795 | 1.0 min | 0.012 min | **82× (BLOCKER)** |
| WC-02/F | 72 | 0.750 | 1.4 min | 0.0021 min | **675× (BLOCKER)** |
| WC-04/M | 84 | 0.693 | 1.5 min | 0.0001 min | **13,800× (BLOCKER)** |
| WC-04/F | 66 | 0.864 | 1.6 min | 0.058 min | **28× (BLOCKER)** |
| WC-05/U | 133 | 0.424 | 1.1 min | ~0 min | **inf× (BLOCKER)** |
| WC-06/U | 208 | 0.251 | 0.8 min | ~0 min | **inf× (BLOCKER)** |
| WC-08/F | 61 | 0.880 | 1.2 min | 0.10 min | **12× (BLOCKER)** |

**The current implementation over-reports wait times by 10× to 13,000×.** With 50–200 cabins available, the M/M/c model predicts near-zero queuing wait when ρ < 0.9. The simulation instead always shows 0.8–1.6 minutes of wait even when utilization is low, misleading operators into thinking queues are forming when they are not.

### 4c. Clusters correctly modeled vs approximated

| Cluster | Model Applied | Correct Model | Assessment |
|---------|--------------|---------------|------------|
| WC-01, WC-02, WC-04, WC-07, WC-08 (M/F) | Ad hoc | M/M/c (large c, individual cabins) | WRONG model |
| WC-03/M, WC-03/F | Ad hoc | M/M/c (c=54, c=48) | WRONG model + ρ>1 undetected |
| WC-05/U | Ad hoc | M/M/133 | WRONG model (extremely over-reports queue) |
| WC-06/U | Ad hoc | M/M/208 | WRONG model (extremely over-reports queue) |
| WC-07/M | Ad hoc (cabin model) | M/G/∞ batch server (calha) | WRONG model TYPE — see section 5 |

---

## 5. The WC-07 CALHA Problem

### What the code stores
`clusters.py` line 113: `"capacidade_m": 84` for WC-07.

The audit spec states WC-07/M has **8 calha sections**, not 84 individual cabin servers.

### What a calha is
A calha (trough urinal) is a **batch server**: 8–12 men can use it simultaneously. Service time is ~30–60 seconds (0.5–1 min), not 3 minutes like a cabin.

| Property | Individual Cabin | Calha (WC-07/M) |
|----------|-----------------|----------------|
| Server type | M/M/c single server | Batch/infinite-server |
| c (servers) | 1 per cabin | 8–12 per calha section |
| Avg service time | 3.0 min | 0.5–1.0 min |
| Simultaneous users | 1 | 8–12 |
| μ per unit | 0.333 persons/min | 1.0–2.0 persons/min |

### Throughput error
- **Current model assumption:** c=84 cabins, μ=0.333/cabin → total μ=28 persons/min
- **Actual calha throughput:** 8 calhas × 10 users × 1/min = **80–160 persons/min**
- **Underestimate of throughput: 3–6× lower than reality**

The capacity value of 84 appears to be the number of simultaneous standing positions across all 8 calhas (8 calhas × ~10 positions ≈ 80, rounded to 84). That's a capacity count, not a server count for the M/M/c formula.

### Consequence
The queue formula for WC-07/M overstates wait times and understates throughput. Operators may be incorrectly redirected away from WC-07/M when it actually has the highest throughput of any male section in the venue.

### Correct model for WC-07/M
Model as **M/G/∞** (infinite-server queue) or **M/M/c with c=8 calhas and μ_calha = 8–10/min**:
```
c = 8 calha sections
μ_per_calha = 10 users × (1/0.5 min) = 20 persons/min per calha
μ_total = 8 × 20 = 160 persons/min
ρ = λ / (c × μ_per_calha) = 25 / (8 × 20) = 0.156 (essentially never queues)
```

---

## 6. Peak Scenario Analysis (headliner_end_surge, occ_mult=1.6)

At peak, occ_pct → ~100% (capped), so fluxo_entrada ≈ 100 × 0.25 = **25 persons/min**.

| Section | c | ρ_peak | Status |
|---------|---|--------|--------|
| WC-01/M | 72 | **1.042** | OVERLOADED |
| WC-01/F | 63 | **1.190** | OVERLOADED |
| WC-02/M | 54 | **1.389** | OVERLOADED |
| WC-02/F | 72 | **1.042** | OVERLOADED |
| WC-03/M | 54 | **1.389** | OVERLOADED |
| WC-03/F | 48 | **1.563** | OVERLOADED |
| WC-04/M | 84 | 0.893 | NEAR-CRITICAL |
| WC-04/F | 66 | **1.136** | OVERLOADED |
| WC-05/U | 133 | 0.564 | STABLE |
| WC-06/U | 208 | 0.361 | STABLE |
| WC-07/M | 84 | 0.893 | NEAR-CRITICAL (calha: STABLE) |
| WC-07/F | 54 | **1.389** | OVERLOADED |
| WC-08/M | 84 | 0.893 | NEAR-CRITICAL |
| WC-08/F | 61 | **1.230** | OVERLOADED |

**8 out of 14 sections exceed ρ=1.0 at peak surge.** The simulation does NOT detect or report this — it still outputs "cheio" (75–89%) status rather than "CRITICO" because occupancy is capped at 100% and the queue/wait logic does not use utilization. No CRITICO alert fires even when queues are theoretically unbounded.

**WC-05 (133 unisex) and WC-06 (208 unisex) remain stable at peak** because their large cabin counts give μ_total = 44 and 69 persons/min respectively, far above the peak λ of 25/min.

---

## 7. Code Fixes Required

### FIX 1 — BLOCKER: Wait time formula (simulation.py lines 244–246)

**Current:**
```python
# Wait time: queue / average throughput (~8 people/min per section)
throughput = 8.0
tempo_espera = fila / throughput if fila > 0 else 0.0
```

**Required fix (minimal — restores Little's Law consistency):**
```python
# Wait time derived from Little's Law: W = L / λ
# This ensures L = λ × W holds by construction.
tempo_espera = fila / fluxo_entrada if fluxo_entrada > 0 else 0.0
```
Note: `fluxo_entrada` must be computed before `tempo_espera` in `_compute_section_state`. Lines 249 and 246 need to be reordered so that `fluxo_entrada` is available when computing `tempo_espera`.

**Full fix (physically correct M/M/c — requires importing math and passing cabin count):**
```python
def _mmc_wait_time(lam: float, c: int, mu: float = 1/3.0) -> float:
    """Erlang-C expected wait time in queue (minutes)."""
    import math
    rho = lam / (c * mu)
    if rho >= 1.0:
        return float('inf')   # unstable — queue grows unboundedly
    A = lam / mu
    try:
        sum_term = sum(A**n / math.factorial(n) for n in range(c))
        erlang_term = A**c / (math.factorial(c) * (1.0 - rho))
        P0 = 1.0 / (sum_term + erlang_term)
        Pc = erlang_term * P0
        return Pc / (c * mu - lam)
    except OverflowError:
        return 0.0   # very large c → effectively no queue

# In _compute_section_state:
tempo_espera = _mmc_wait_time(fluxo_entrada, capacity)
```

### FIX 2 — BLOCKER: ρ ≥ 1.0 undetected (simulation.py, _compute_section_state)

Sections WC-02/M, WC-03/M, WC-03/F, WC-07/F have ρ > 1.0 during normal_day but show "moderado" status. The status logic only checks `occ_pct`, not utilization:

```python
# Current (lines 258–265): only checks occupancy percentage
if occ_pct >= 90:
    status = SectionStatus.CRITICO
```

**Required addition — check utilization before setting status:**
```python
MU_PER_CABIN = 1 / 3.0   # module-level constant

# In _compute_section_state, after computing fluxo_entrada:
mu_total = capacity * MU_PER_CABIN
rho = fluxo_entrada / mu_total if mu_total > 0 else 0.0
if rho >= 1.0:
    status = SectionStatus.CRITICO   # queue unstable — override
elif occ_pct >= 90:
    status = SectionStatus.CRITICO
elif occ_pct >= 75:
    status = SectionStatus.CHEIO
elif occ_pct >= 50:
    status = SectionStatus.MODERADO
else:
    status = SectionStatus.LIVRE
```

### FIX 3 — HIGH: Little's Law violated in all 14 sections

Root cause documented in section 1. Fixing FIX 1 (using `W = L/λ`) resolves this structurally. If the full Erlang-C path is taken, `fila` should also be derived from the M/M/c steady-state:
```python
# Lq (expected queue length) from Erlang-C:
W_q = _mmc_wait_time(fluxo_entrada, capacity)
fila = int(round(fluxo_entrada * W_q))   # Little's Law: L = λ × W
```
This replaces lines 240–241 of simulation.py.

### FIX 4 — MEDIUM: WC-07/M modeled as cabin queue instead of calha batch server

**Current:** `capacidade_m = 84` treated as 84 individual M/M/1 cabin servers.

**Required:** Distinguish calha from cabin in cluster metadata. Add a field or use a separate throughput constant:

```python
# In clusters.py, WC-07 entry:
"calha_sections_m": 8,     # number of calha trough sections
"calha_capacity_m": 84,    # simultaneous standing positions
# Note: calha μ = ~20 persons/min per section, not 0.333
```

In simulation.py, detect calha sections and apply the correct throughput:
```python
CALHA_CLUSTERS = {"WC-07": {"M"}}   # calha (trough urinal) sections
CALHA_MU_PER_SECTION = 20.0         # persons/min per calha section
CALHA_SECTIONS = {"WC-07": {"M": 8}}  # c = 8 calha sections

def _get_service_params(cluster_id: str, section: str, capacity: int):
    if cluster_id in CALHA_CLUSTERS and section in CALHA_CLUSTERS[cluster_id]:
        c = CALHA_SECTIONS[cluster_id][section]
        mu = CALHA_MU_PER_SECTION
    else:
        c = capacity       # one cabin = one server
        mu = 1 / 3.0       # 3-min avg service
    return c, mu
```

### FIX 5 — LOW: `fluxo_entrada` computation order must precede `tempo_espera`

In `_compute_section_state`, after applying Fix 1, the computation of `fluxo_entrada` (line 249) must be moved above `tempo_espera` (line 246). Current order:

```
line 240: base_queue / fila
line 244–246: tempo_espera = fila / 8.0        # uses fila ✓
line 249: fluxo_entrada = occ_pct * 0.25       # used by tempo_espera — but defined AFTER
```

With Fix 1, `tempo_espera = fila / fluxo_entrada` requires `fluxo_entrada` to be defined first. Move lines 249–250 above lines 244–246.

---

## Summary Table

| # | Severity | Finding | File | Lines |
|---|----------|---------|------|-------|
| 1 | **BLOCKER** | Wait time hardcoded as `L/8.0` — 10× to 13,800× above M/M/c value | simulation.py | 244–246 |
| 2 | **BLOCKER** | Little's Law violated in all 14 sections (systematic, not noise) | simulation.py | 240–249 |
| 3 | **BLOCKER** | ρ ≥ 1.0 in 4 sections (normal_day) and 8 sections (peak) — not detected or alerted | simulation.py | 258–265 |
| 4 | **HIGH** | WC-07/M modeled as 84 cabin servers instead of 8 calha batch servers — throughput underestimated 3–6× | simulation.py + clusters.py | 244–246, 113 |
| 5 | **MEDIUM** | All sections use M/M/1-equivalent throughput (8.0/min) instead of M/M/c — overcounts expected queue for large-c clusters (WC-05: 133, WC-06: 208) | simulation.py | 245 |
| 6 | **LOW** | `fluxo_entrada` computed after `tempo_espera` — ordering dependency for proposed fix | simulation.py | 246, 249 |

---

## Key Physical Insight

With 50–200 cabins and typical arrival rates of 17–25 people/min, these clusters are **massively over-provisioned for queueing** under normal conditions. M/M/c theory predicts near-zero queue wait for ρ < 0.85 with large c. The current simulation falsely shows 0.8–1.6 minutes of wait for all sections at all times, making the system appear to be in a persistent moderate-queue state that does not exist physically.

The only genuinely dangerous scenario is surge at small-cabin sections (WC-03/F with c=48, WC-02/M and WC-07/F with c=54), which reach ρ > 1.0 even at moderate arrival rates.
