# PlantaOS × Rock in Rio Lisboa 2026

**Planta Smart Homes · hi@planta.design**
**Parque Tejo · Lisboa · 20, 21, 27, 28 Junho 2026**

Real-time occupancy monitoring for 8 WC clusters at Rock in Rio Lisboa 2026.
Counts people and flows only. Three sensor sources fused: IR, WiFi, Prosegur cameras.

---

## Quick Start — One Command

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Open: **http://localhost:8000** — full dashboard, live backend data.

### Optional: secondary Next.js interface

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000/twin
```

---

## Pages

| URL | Description |
|-----|-------------|
| /twin | Digital Twin — SVG map with live WC status |
| /occupation | WC Occupancy — cards for all 8 clusters |
| /sensors | Sensor Health — IR, WiFi, Camera status |
| /shows | Show Programme — 4-day festival schedule |
| /chat | AI Assistant — Gemini 2.5 Flash or local fallback |
| /ops | Operations — alerts, routing, export |
| /app | Public Visitor App — "which WC now?" |

---

## API

```
GET  /api/v1/health           → healthcheck
GET  /api/v1/clusters         → all 8 WC clusters (live state)
GET  /api/v1/kpis             → 4 global KPIs
GET  /api/v1/shows            → festival programme
POST /api/v1/sensor           → ingest LilyGo reading
POST /api/v1/prosegur         → ingest Prosegur camera reading
POST /api/v1/simulate/tick    → advance simulation scenario
POST /api/v1/chat             → AI chat (Gemini or local fallback)
WS   /api/v1/ws               → WebSocket (full state on connect, updates every 5s)
```

Swagger docs: http://localhost:8000/docs

---

## Tests

```bash
# Backend
cd backend && source .venv/bin/activate && pytest
# Expected: 140 passed

# Frontend
cd frontend
npm run typecheck   # 0 errors
npm run lint        # 0 warnings
```

---

## The 8 WC Clusters

| ID | Location | Type | Capacity |
|----|----------|------|----------|
| WC-01 | V34 — Near P1 | M + F | M:72 · F:63 |
| WC-02 | V35 — Female Dominant | M + F | M:54 · F:72 |
| WC-03 | S36 — Entrada Principal | M + F | M:54 · F:48 |
| WC-04 | S37 — Summit +20m | M + F | M:84 · F:66 |
| WC-05 | M38 — ENTRY ONLY | **Unisex** | 133 |
| WC-06 | W39/S39 — Maior cluster | **Unisex** | 208 |
| WC-07 | M40 — Lockers | M + F | M:84 · F:54 |
| WC-08 | V41 — Produção | M + F | M:84 · F:61 |

WC-05 and WC-06 are **always unisex** — never split by M/F.

---

## Sensor Fusion

```
occupancy = (IR × 0.50) + (WiFi × 0.30) + (Camera × 0.20)
            ──────────────────────────────────────────────
            normalized by available source weights
```

If a source is offline, its weight is redistributed proportionally.

---

## Alert Thresholds

| Severity | Condition |
|----------|-----------|
| CRITICO | occupancy > 90% |
| ALTO | occupancy > 75% AND queue > 20 |
| MEDIO | confidence < 40% |
| INFO | sensor offline > 5 min |

---

## Environment Variables (optional)

Copy `backend/backend.env.example` to `backend/.env`:

```bash
GEMINI_API_KEY=...           # Optional — enables Gemini 2.5 Flash chat
SCOR_TOKEN_KPI=...           # Optional — enables SCOR Sensaway publishing
SCOR_TOKEN_CLUSTER=...       # Optional
ADMIN_PIN=1234               # Optional — protects counter reset
```

Without any env vars, the system runs fully in local simulation mode.

---

## Documentation

| File | Contents |
|------|----------|
| RUNBOOK_LOCAL.md | Full local setup guide |
| AUDIT_SUMMARY.md | Build audit results |
| CHECKLIST_MASTER.md | All 15 agent checklists |
| TEST_REPORT.md | Test results + remaining risks |
| docs/COUNTERFACTUAL_QA.md | 60 edge-case scenarios |

---

*"I design to free." — Planta Smart Homes*
