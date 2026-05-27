# TRACK 02 — Data Consistency Audit
**PlantaOS × Rock in Rio Lisboa 2026**
**Audit date:** 2026-05-27
**Auditor:** Track 02 agent (Claude Sonnet 4.6)

---

## Executive Summary

All three originally flagged contradictions have been resolved. The code and XLSX are **fully consistent** on every capacity number. Two crowd-figure discrepancies exist between old and new sources and are explained by version history, not data corruption.

| Finding | Severity | Resolution |
|---------|----------|------------|
| WC-07 masc=84 vs "ZERO individual, 8 CALHA only" | BLOCKER → **CLEARED** | XLSX formula confirms M=84; "8 CALHA" is a misreading of 8*9 factors |
| Festival capacity: 80k vs 100k vs 120k | HIGH → **RESOLVED** | Three distinct contexts; canonical value is 120,000 (new dashboard, Day 4 peak) |
| Total WC places: 1137 | **CONFIRMED CORRECT** | XLSX and code both sum to exactly 1,137 |
| WC-05 type: UNISSEX vs entry-only | **CONFIRMED CORRECT** | entry_only=True AND tipo=unissex — both flags are set correctly |

---

## 1. XLSX vs Code — Full Cluster Cross-Reference

### Source data

**XLSX file:** `RIRLX_limiteocupacaobanheiros (2).xlsx`, sheet `Planilha1`
**Code file:** `/Users/goncalomelodemagalhaes/Desktop/planta-rir2026/backend/app/data/clusters.py`

### XLSX raw formulas (column B = MASC, column C = FEM)

| Cluster | MASC formula | MASC value | FEM formula | FEM value | XLSX flag |
|---------|-------------|-----------|------------|----------|-----------|
| WC 01 | `(7*9)+9` | 72 | `9*7` | 63 | — |
| WC 02 | `(3*6)+(4*9)` | 54 | `12*6` | 72 | — |
| WC 03 | `(3*6)+4*9` | 54 | `8*6` | 48 | — |
| WC 04 | `(2*6)+8*9` | 84 | `11*6` | 66 | — |
| WC 05 | `19*7` | 133 | `0` | 0 | UNISSEX |
| WC 06 | `(25*3)+(6*14)+(7*7)` | 208 | `0` | 0 | UNISSEX |
| WC 07 | `(2*6)+8*9` | 84 | `9*6` | 54 | — |
| WC 08 | `(2*6)+(8*9)` | 84 | `(7*7)+(2*6)` | 61 | — |

**XLSX ESPERA (waiting capacity):** computed as `(M+F)*0.8` for all except WC-01 which uses `*0.6`.
**XLSX TOTAL per cluster includes waiting queue** — this is not a physical WC places total.

### Match result vs code

| Cluster | XLSX_M | CODE_M | Match | XLSX_F | CODE_F | Match | XLSX_U | CODE_U | Match |
|---------|--------|--------|-------|--------|--------|-------|--------|--------|-------|
| WC-01 | 72 | 72 | OK | 63 | 63 | OK | — | 0 | — |
| WC-02 | 54 | 54 | OK | 72 | 72 | OK | — | 0 | — |
| WC-03 | 54 | 54 | OK | 48 | 48 | OK | — | 0 | — |
| WC-04 | 84 | 84 | OK | 66 | 66 | OK | — | 0 | — |
| WC-05 | 133 (UNISSEX col M) | 0+0 | — | 0 | 0 | — | 133 | 133 | OK |
| WC-06 | 208 (UNISSEX col M) | 0+0 | — | 0 | 0 | — | 208 | 208 | OK |
| WC-07 | 84 | 84 | **OK** | 54 | 54 | **OK** | — | 0 | — |
| WC-08 | 84 | 84 | OK | 61 | 61 | OK | — | 0 | — |

**Result: ZERO discrepancies. All 16 capacity figures match exactly.**

---

## 2. WC-07 — The "8 CALHA Only" Question

### The claim
The audit brief stated: *"XLSX says ZERO individual, 8 CALHA only"* for WC-07 masc, contradicting `code: masc=84`.

### What the XLSX actually shows

WC-07 MASC formula: `(2*6)+8*9`

Breaking this down:
- `2*6 = 12` — 2 fixture groups × 6 positions each
- `8*9 = 72` — 8 fixture groups × 9 positions each
- Total: **84**

This is **identical** to WC-04 and WC-08 which have the same formula `(2*6)+8*9 = 84`.

### What "8 CALHA" means in context

The digital twin JSON (`wc_clusters_digital_twin.json`) lists WC-07 `internal_fixtures` as containing **"CALHA URINÓIS" count: "multiple"** — confirming calhas (trough urinals) are present. However:

1. The XLSX **does not** treat WC-07 as zero-individual. The formula `(2*6)+8*9` has **two distinct groups** — likely 2 individual cabin blocks (×6) plus 8 calha positions (×9 throughput factor per calha section).
2. WC-08, which the digital twin explicitly lists as having **5 CALHA URINÓIS**, uses the exact same formula: `(2*6)+(8*9)=84`. This confirms that the `8*9` term represents calha throughput capacity, not 8 individual cabins.
3. The multiplier `*9` in the XLSX formulas appears consistently for male urinal runs (both individual and calha). The `*3` multiplier appears exclusively in WC-06's unisex formula `(25*3)+(6*14)+(7*7)=208`, likely representing a different (smaller) fixture type.

### Resolution

**The code value `masc=84` for WC-07 is correct and matches the XLSX.**

The "8 CALHA only" description was a misreading of the formula structure. The XLSX formula for WC-07 encodes:
- A mixed installation of cabin-type fixtures (2 groups × 6) AND calha-type fixtures (8 sections × 9 capacity)
- The **84** is the simultaneous-use capacity (occupancy limit), not the count of physical trough units

For queue calculation purposes: using 84 as the capacity ceiling is the correct approach per the XLSX model. There is **no calculation error**.

---

## 3. Festival Capacity — 80k vs 100k vs 120k

### All sources mapped

| Source | Value | Context |
|--------|-------|---------|
| `rockinrio_official_v1/simulator/festival_simulator.py` | **80,000** | Legacy simulator, `PEAK_CROWD = 80_000` |
| Dashboard hero text (`index.html` line 320) | **100,000+** | Marketing copy, approximate/rounded |
| Dashboard KPI counter (`animCnt cnt3`) | **120,000** | Current live counter in new dashboard |
| New dashboard `shows` data — Day 1 (Katy Perry) curve peak | **118,000** | Per-show crowd curve |
| New dashboard `shows` data — Day 2 (Linkin Park) | **115,000** | `crowd: 115000` field |
| New dashboard `shows` data — Day 3 (Rod Stewart) | **110,000** | `crowd: 110000` field |
| New dashboard `shows` data — Day 4 (21 Savage) | **120,000** | `crowd: 120000` field — maximum |

### Canonical resolution

**There is no single "capacity/day" number — the festival uses per-show crowd curves.**

The figures by context:
- **80,000**: Outdated legacy value from `rockinrio_official_v1`. Do not use for new calculations.
- **100,000+**: Dashboard marketing hero text, intentionally vague (correct as a floor).
- **110,000–120,000**: Authoritative per-day crowd estimates used in new dashboard simulation.
- **120,000**: The single-day peak (Day 4, 21 Savage), used as the absolute maximum for stress-testing.

**For WC queue calculations the canonical figure is:**
- Baseline simulation: **110,000** (conservative, Day 3)
- Peak stress test: **120,000** (Day 4)
- Legacy simulator only: 80,000 (not to be used for dimensioning)

---

## 4. WC-05 Type Audit

### Claim: "UNISSEX vs entry-only — verify not entry-only"

Code in `clusters.py`:
```python
{
    "id": "WC-05",
    "nome": "M38 — ENTRY ONLY",
    "tipo": "unissex",
    "entry_only": True,
    "capacidade_m": 0,
    "capacidade_f": 0,
    "capacidade_unissex": 133,
}
```

**Both conditions are true simultaneously and correctly:**
- `tipo="unissex"`: WC-05 has no M/F split (correct — XLSX flags col F as UNISSEX)
- `entry_only=True`: WC-05 has flow-control entry with ENTRADA ONLY access (correct — digital twin confirms "ENTRADA ENTRY ONLY flow control")
- `ENTRY_ONLY_CLUSTER_IDS = {"WC-05"}` is correctly set in the routing exclusion set
- `capacidade_unissex=133` matches XLSX formula `19*7=133`

**Status: CONFIRMED CORRECT. No contradiction exists.**

---

## 5. Total WC Places

### Calculation

| Cluster | Masc | Fem | Unissex | Subtotal |
|---------|------|-----|---------|----------|
| WC-01 | 72 | 63 | 0 | 135 |
| WC-02 | 54 | 72 | 0 | 126 |
| WC-03 | 54 | 48 | 0 | 102 |
| WC-04 | 84 | 66 | 0 | 150 |
| WC-05 | 0 | 0 | 133 | 133 |
| WC-06 | 0 | 0 | 208 | 208 |
| WC-07 | 84 | 54 | 0 | 138 |
| WC-08 | 84 | 61 | 0 | 145 |
| **TOTAL** | **432** | **364** | **341** | **1,137** |

**Canonical total: 1,137 WC places.**
- XLSX sum: 1,137 (without waiting queue)
- Code sum: 1,137
- Dashboard hero counter: "1 137 lugares WC" — correct

---

## 6. Formula Multiplier Reference (for future audits)

The XLSX uses these multipliers to encode fixture throughput capacity:

| Multiplier | Interpretation | Example |
|-----------|---------------|---------|
| `× 6` | Small fixture unit (cabin or compact urinal block) | WC-02 masc: `3×6=18` |
| `× 7` | Standard individual cabin (full throughput) | WC-05 unissex: `19×7=133` |
| `× 9` | Larger fixture block or calha section (high throughput) | WC-07 masc: `8×9=72` |
| `× 3` | Compact calha / trough (WC-06 only) | WC-06 unissex: `25×3=75` |
| `× 14` | Extended calha run | WC-06 unissex: `6×14=84` |

These multipliers represent **simultaneous occupancy capacity**, not physical fixture counts.

---

## 7. Open Questions / Items Requiring Physical Verification

1. **WC-08 drawing caveat**: Digital twin notes *"Necessário conferência de dimensões in loco"* — all WC-08 dimensions need field verification before event. Capacity 84M+61F should be treated as provisional.
2. **WC-07 CALHA count**: Digital twin lists "multiple" CALHA URINÓIS without a specific count. WC-08 lists 5 CALHA explicitly. WC-07 should be field-verified before event.
3. **GPS coordinates**: All GPS coordinates in the code are approximate linear interpolations from SVG, not geodetic surveys. Sub-10m accuracy noted. These do not affect capacity calculations.
4. **Day 1 crowd figure**: Dashboard `shows` data for Day 1 (Katy Perry / 20 Jun) has no `crowd:` field — only `crowd_curve`. Peak of curve is 118,000. Should be normalized to `crowd: 118000` for consistency.

---

## Severity Summary

| Issue | Severity | Status |
|-------|----------|--------|
| WC-07 masc=84 contradiction | ~~BLOCKER~~ | CLEARED — no contradiction |
| Festival capacity ambiguity | HIGH | RESOLVED — see canonical values above |
| Total 1,137 WC places | — | CONFIRMED |
| WC-05 UNISSEX + entry_only | — | CONFIRMED CORRECT |
| WC-08 field verification needed | MEDIUM | OPEN — requires on-site check |
| Day 1 missing crowd field | LOW | OPEN — cosmetic data normalization |
| Legacy simulator uses 80k | LOW | OPEN — simulator should be updated to 120k |
