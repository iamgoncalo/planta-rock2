# Track 08 — Visitor UX Audit
**PlantaOS × Rock in Rio Lisboa 2026**
**Audit date:** 2026-05-27
**Auditor:** Track 08 automated quality audit

---

## Executive Summary

The PlantaOS dashboard is built for operations staff, not for festival visitors. A stressed attendee who lands on the site cannot find the nearest free WC in under 3 taps — or even under 10. There is no geolocation feature, no "find nearest WC" button, and no simplified visitor view. The primary CTA buttons are dramatically under-sized for mobile touch (28 px vs. 44 px minimum). Muted text fails WCAG contrast entirely. The Nearest-WC feature that exists in `rockinrio_official_v1/plantaos.html` was not ported into the current dashboard.

**Overall verdict: BLOCKER — a real festival visitor cannot accomplish the core task.**

---

## 1. Critical Path Analysis

**Can a visitor find the nearest free WC in 2 taps? NO.**

### Actual tap path to find any WC info:
| Tap | Action | Result |
|-----|--------|--------|
| 1 | Load page | Hero marketing copy + 9 technical KPI counters visible |
| 2 | Tap "Digital Twin + Zoom" CTA | Navigates to map page |
| 3 | Scan the map visually | No zoom-to-nearest, no highlight of free clusters |
| 4 | Tap a WC bubble on SVG map | Opens detail panel |
| 5 | Read detail panel | Get utilisation %, queue, occupancy |

**Minimum taps to see any WC status: 4 (map → find cluster → tap → read).**
**Minimum taps via home page cluster cards: 2 (tap card → lands on map with detail panel).**

However even the 2-tap path via cluster cards fails the "2 seconds" test because:
- The home page shows 8 cluster cards (one per cluster) — visitor must already know which cluster is closest
- Cards show `WC-01 · 42%` with tiny `.5rem` sub-labels — requires reading and interpretation
- No single "GO HERE NOW" recommendation is surfaced
- No geolocation, no distance calculation, no sorting by proximity

### Evidence
```
Home page buttons:
  <button class="btn btn-p" data-page="pm">Digital Twin + Zoom</button>
  <button class="btn btn-o" data-page="ps">Simular Shows</button>
  <button class="btn btn-o" data-page="psen">Sensores</button>
  <button class="btn btn-o" data-page="pcf">↯ Contrafactuais</button>

id="nwc-btn" in current dashboard: NOT PRESENT
nearest-wc API endpoint: NOT REGISTERED (confirmed via /openapi.json)
```

**Severity: BLOCKER**

---

## 2. Page Size Assessment

| Metric | Value |
|--------|-------|
| Total HTML file | 726 KB |
| Embedded map WebP (base64) | 614 KB base64 (461 KB decoded) — 85% of file |
| CSS | 19.5 KB |
| HTML + JS | ~112 KB |
| Google Fonts (external, blocking) | ~200 KB additional |
| Inline base64 images | 0 (the map data is `application/octet-stream`, not base64 img) |

### Load time estimates

| Network | Speed | HTML only | HTML + Fonts |
|---------|-------|-----------|--------------|
| 100 Mbps ideal | 12.8 MB/s | 0.1 s | 0.1 s |
| 10 Mbps decent | 1.28 MB/s | 0.6 s | 0.7 s |
| 5 Mbps busy festival WiFi | 640 KB/s | 1.1 s | 1.4 s |
| 1 Mbps congested | 128 KB/s | 5.7 s | 7.2 s |
| 3G (400 kbps) | 50 KB/s | 14.5 s | 18.5 s |

**Assessment:**
- On dedicated festival WiFi at realistic 5 Mbps per device: 1.4 s — ACCEPTABLE
- On congested WiFi (100k people sharing infrastructure): 7 s+ — PROBLEMATIC
- On 3G fallback (visitors outside WiFi range): 18 s — UNACCEPTABLE
- The 614 KB map blob dominates the payload. If the map were served as a separate resource (loaded lazily), initial page load would drop to ~112 KB HTML + 200 KB fonts = ~312 KB, cutting load time by 80%.
- Google Fonts are render-blocking (no `font-display: swap`, no preload hints). Text is invisible until fonts download.

**Severity: HIGH** (the map blob and render-blocking fonts together cause unacceptable load times in congested/3G conditions)

---

## 3. Color Contrast Table

Background colors: `--ink: #07100a` (body), `--c1: #0d1a0f` (card)

| Foreground | Background | Ratio | WCAG Rating | Usage |
|------------|------------|-------|-------------|-------|
| `--t` `#c8e4cc` | `--ink` `#07100a` | 14.18:1 | **AAA** | Primary text on body |
| `--t2` `#6ba872` | `--ink` `#07100a` | 6.87:1 | **AA** | Secondary text on body |
| `--t3` `#3a6040` | `--ink` `#07100a` | 2.69:1 | **FAIL** | Muted/label text on body |
| `--heading` `#ffffff` | `--ink` `#07100a` | 19.31:1 | **AAA** | Headings on body |
| `--verde` `#6FAF82` | `--ink` `#07100a` | 7.48:1 | **AAA** | Green status on body |
| `--amb` `#BA7517` | `--ink` `#07100a` | 5.19:1 | **AA** | Amber status on body |
| `--red` `#C25A1A` | `--ink` `#07100a` | 4.39:1 | **AA Large only** | Critical status on body |
| `--t` `#c8e4cc` | `--c1` `#0d1a0f` | 13.16:1 | **AAA** | Primary text on card |
| `--t2` `#6ba872` | `--c1` `#0d1a0f` | 6.37:1 | **AA** | Secondary text on card |
| `--t3` `#3a6040` | `--c1` `#0d1a0f` | 2.50:1 | **FAIL** | Muted text on card |
| `--verde` `#6FAF82` | `--c1` `#0d1a0f` | 6.94:1 | **AA** | Verde status on card |
| `--amb` `#BA7517` | `--c1` `#0d1a0f` | 4.82:1 | **AA** | Amber status on card |
| `--red` `#C25A1A` | `--c1` `#0d1a0f` | 4.07:1 | **AA Large only** | Critical red on card |
| `--g` `#07100a` (btn txt) | `--gl` `#6FAF82` (btn bg) | 7.48:1 | **AAA** | CTA button text |

### Critical findings:
- **`--t3` (#3a6040) FAILS WCAG at 2.69:1 and 2.50:1** — used for cluster card sub-labels, legend text, confidence %, and map annotations. Text is unreadable in bright festival sunlight.
- **`--red` (#C25A1A) is 4.39:1 — just below 4.5:1 AA** — the "CRÍTICO" status badge (the most important signal for visitors) fails normal-text AA. It only passes for large text (≥18pt/24px or ≥14pt/19px bold).
- In direct sunlight the effective contrast is worse than lab conditions suggest.

**Severity: HIGH** (--t3 muted text FAIL, --red critical status borderline AA Large only)

---

## 4. Touch Target Audit

### WCAG 2.5.5 criterion: minimum 44×44 px touch target

| Element | Padding | Font | Est. Height | Status |
|---------|---------|------|-------------|--------|
| `.btn` (primary CTA) | 7px top+bottom | .72rem (11.5px) | ~28 px | **FAIL — 16px short** |
| `.nb` (nav buttons) | 5px top+bottom | .70rem (11.2px) | ~23 px | **FAIL — 21px short** |
| `.btn-s` (small button) | 4px top+bottom | .64rem (10.2px) | ~21 px | **FAIL — 23px short** |
| `.pill` (chat quick actions) | 3px top+bottom | .62rem (9.9px) | ~16 px | **FAIL — 28px short** |
| WCC cluster cards | 12px top+bottom | N/A (grid) | ~100px | PASS (grid cell) |

**All interactive button elements fail the 44px minimum touch target rule.** The home page CTAs ("Digital Twin + Zoom", "Simular Shows") are approximately 28px tall — 36% too short. On mobile, these are very difficult to tap accurately in a crowded festival environment.

The nav buttons at 23px height are particularly problematic: 7 navigation items crammed into a horizontal strip, each only 23px tall with 9px horizontal padding.

**Severity: HIGH**

---

## 5. Nearest-WC Feature

| Check | Result |
|-------|--------|
| `id="nwc-btn"` in current dashboard | **NOT PRESENT** |
| `navigator.geolocation` usage | **NOT PRESENT** |
| `/api/v1/nearest-wc` endpoint registered | **NOT PRESENT** (confirmed via OpenAPI spec) |
| Backend density service has lat/lon conversion | Present in `density.py` line 119 |
| Chat pills include "Qual WC tem menos fila?" | Present — but requires navigating to Chat AI tab first |

**The nearest-WC feature is completely absent from the current dashboard.** The only path for a visitor to find a less-occupied WC is:
1. Navigate to Chat AI page (tab 6 of 7)
2. Wait for Gemini to respond to "Qual WC tem menos fila?"

This is a multi-step, text-heavy, latency-dependent flow — the opposite of what a stressed visitor needs.

**Severity: MEDIUM** (blocked only because the backend endpoint doesn't exist either; but the reference file shows it was designed)

---

## 6. Comparison with rockinrio_official_v1/plantaos.html

### Reference file stats
- Size: 759 KB (slightly larger, same map blob)
- Pages: `ph, pm, pch, ps, pcf, psen, pins, padm` — has **Installation page** (`pins`)

### Features in reference that are MISSING from current dashboard:

| Feature | Reference (v1) | Current dashboard |
|---------|----------------|-------------------|
| `id="nwc-btn"` nearest-WC pill | **YES** — in Chat AI page footer | **NO** |
| `navigator.geolocation` call | **YES** — fires on nwc-btn click | **NO** |
| `/v1/nearest-wc?lat=&lon=` API fetch | **YES** | **NO** (endpoint 404s) |
| Installation guide page (`pins`) | **YES** — full 8-cluster guide | **NO** |
| Toast with WC recommendation | **YES** — "WC mais próxima: WC-03 (47m)" | **NO** |
| Auto-navigate to map + open detail | **YES** — `go("pm"); openDP(id)` | **NO** |

### Features identical across both versions:
- PILLS constant with 8 quick chat questions (identical content)
- All 7 nav pages (ph, pm, pch, ps, pcf, psen, padm)
- Same map blob (614 KB)
- Same CSS architecture
- Same color scheme

**The key regression: the Nearest-WC geolocation pill was dropped between v1 and the current build.** The backend API route was never ported either.

---

## 7. Top 10 UX Fixes (Ordered by Visitor Impact)

### BLOCKER

**Fix 1 — Add "WC mais próxima" button to HOME PAGE**
A large, prominent pill/button on the home page (not buried in Chat AI) that fires geolocation and returns a single recommendation. This is the single highest-impact fix.
- Re-port the `nwc-btn` from v1 but place it on `#ph` hero, not chat footer
- Register `/api/v1/nearest-wc` endpoint in backend
- Show result as full-screen modal: "Vá para WC-03 — 47m · 23% utilização · 0 fila"

**Fix 2 — Add "Nearest Free WC" sort / highlight on home cluster cards**
Sort the 8 WCC cluster cards by `util` ascending (or distance if geolocation granted). Add a "Mais livre agora" badge on card #1. First card = go here.

### HIGH

**Fix 3 — Increase all touch targets to minimum 44px**
- `.btn`: change `padding: 7px 14px` to `padding: 14px 18px`
- `.nb`: change `padding: 5px 9px` to `padding: 12px 14px`; consider hamburger menu on mobile
- `.pill`: change `padding: 3px 9px` to `padding: 10px 16px`
- `.btn-s`: change `padding: 4px 10px` to `padding: 11px 14px`

**Fix 4 — Fix `--t3` color contrast (currently 2.69:1, FAIL)**
Change `--t3: #3a6040` to `#6b9e78` (achieves ~4.6:1 on dark bg) or remove `--t3` from any text smaller than 18px.

**Fix 5 — Fix `--red` critical status contrast (currently 4.39:1, AA Large only)**
Change `--red: #C25A1A` to `#D4693A` (achieves ~4.6:1) or use `--t` for critical badge text on a red background instead of red text on dark background.

**Fix 6 — Lazy-load the map WebP blob**
Move the 614 KB `<script id="map-data">` blob out of the HTML file and load it on-demand only when the user navigates to `#pm` (Digital Twin page). This reduces initial HTML from 726 KB to ~112 KB, cutting load time by ~85% on congested networks.

**Fix 7 — Add `font-display: swap` and preload for primary font**
Add `?&display=swap` (already partially set in URL but `font-display` is not applied in `@font-face`). Add `<link rel="preload" as="style">` for the Google Fonts stylesheet. This eliminates the invisible-text flash during font download.

### MEDIUM

**Fix 8 — Add mobile responsive CSS**
There are zero `@media` queries in the entire file. `html,body { overflow: hidden }` prevents native scroll on mobile. The topbar with 7 navigation items collapses into unreadable overflow on phones. Add at minimum:
```css
@media (max-width: 768px) {
  #nav { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .wgrid { grid-template-columns: repeat(2, 1fr); }
  .hero { padding: 20px 16px; }
  .wcs { padding: 12px 16px; }
}
```

**Fix 9 — Reduce font size proliferation**
Body font is 13px (`font-size:13px`). Sub-labels use `.5rem` (8px), `.48rem` (7.7px), `.52rem` (8.3px). Text below 11px is unreadable on most phone screens, let alone in sunlight. Minimum readable size for a festival context: 14px body, 12px secondary.

**Fix 10 — Add PWA manifest + offline capability**
No `<meta name="apple-mobile-web-app-capable">`, no service worker, no manifest. Visitors who scan a QR code get a plain browser tab that disappears. Adding a manifest + basic cache makes the app installable and usable if WiFi drops between WC clusters.

### LOW

**Bonus Fix — Add a visitor mode toggle**
Separate the 7-tab staff dashboard from a simplified 1-screen visitor view showing only: nearest WC, % free, queue size, and directions. The current app assumes the user understands "% utilização", "pax estimado", "contrafactuais", and "modo N/D/R" — none of which are visitor-facing concepts.

---

## 8. Proposed Visitor Flow

**Goal: First-time visitor finds a free WC in under 2 taps / 5 seconds.**

### Proposed UX (after fixes):

```
[Page loads — 112 KB HTML, fast]
       |
       v
┌──────────────────────────────────────────┐
│  PlantaOS · Rock in Rio Lisboa           │
│                                          │
│  🟢 WC-03 · Palco Mundo  23% · 0 fila  │
│  🟡 WC-05 · Galp Arena   61% · 4 fila  │
│  🔴 WC-01 · Entrada      82% · 11 fila │
│                                          │
│  [ 📍 WC mais próxima — IR AGORA ]       │  ← TAP 1
│                                          │
│  Todos os clusters ▼                     │
└──────────────────────────────────────────┘

TAP 1: "WC mais próxima" fires geolocation

┌──────────────────────────────────────────┐
│  ✅ WC MAIS PRÓXIMA                      │
│                                          │
│  WC-03 · Zona Galp Norte                 │
│  47 metros daqui                         │
│  🟢 23% utilização · 0 fila              │
│  12 lugares livres                       │
│                                          │
│  [ Ver no mapa ]   [ OK, vou lá ]        │  ← TAP 2 (optional)
└──────────────────────────────────────────┘

Total: 1-2 taps, ~3 seconds
```

### Current actual flow (audit finding):

```
[Page loads — 726 KB HTML, 5-18s on congested WiFi]
       |
       v
Hero marketing copy: "100 000+ pessoas. 1 137 lugares WC."
[Read 4 nav CTAs, pick "Digital Twin + Zoom"]  ← TAP 1

[Map loads, find WC bubbles on 1684×2384px SVG]
[Pan/zoom to find green cluster]               ← INTERACTION 2-5

[Tap WC bubble on map]                         ← TAP 6+

[Read detail panel: util%, fila, pax/hora, 
 historico, contrafactuais, Reed sensors...]   ← READ 7+

Total: 6+ taps, 30+ seconds (on good WiFi)
       Impossible in < 18s on congested networks
```

---

## Appendix — File Locations

- Dashboard HTML: `/Users/goncalomelodemagalhaes/Desktop/planta-rir2026/backend/app/static/index.html`
- Reference with geolocation: `/Users/goncalomelodemagalhaes/rockinrio_official_v1/frontend/public/plantaos.html`
- Backend API routes: confirmed via `http://localhost:8000/openapi.json`
- Backend density service (has lat/lon → cell): `/Users/goncalomelodemagalhaes/Desktop/planta-rir2026/backend/app/services/density.py`

---

## Severity Summary

| Severity | Finding | Fix |
|----------|---------|-----|
| BLOCKER | No nearest-WC feature on home page; visitor cannot find free WC in < 3 taps | Add geolocation pill to home page + register API endpoint |
| HIGH | All buttons < 44px (28px primary, 23px nav, 16px pills) | Increase padding on .btn, .nb, .pill |
| HIGH | --t3 muted text 2.69:1 contrast (FAIL WCAG AA) | Lighten --t3 to ≥ #6b9e78 |
| HIGH | --red critical status 4.39:1 (fails normal-text AA) | Darken or use background-based badge |
| HIGH | 614 KB map blob in HTML; 7-18s load on congested/3G | Lazy-load map blob on tab navigation |
| HIGH | Render-blocking Google Fonts (no font-display, no preload) | Add font-display:swap + preload hint |
| MEDIUM | Zero media queries; layout broken on mobile phones | Add @media breakpoints at 768px |
| MEDIUM | 8px–10px sub-label text (unreadable in sunlight) | Minimum 12px for any visible text |
| MEDIUM | Nearest-WC geolocation (existed in v1) was dropped | Re-port nwc-btn + backend /nearest-wc route |
| LOW | No PWA manifest or offline cache | Add manifest.json + service worker |
