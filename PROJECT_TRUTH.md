# PROJECT_TRUTH

## Identity
- Project name: PlantaOS × Rock in Rio Lisboa 2026 [CONFIRMED_FROM_FILES]
- Owner: Planta Smart Homes · hi@planta.design [CONFIRMED_FROM_FILES]
- Festival dates: 20, 21, 27, 28 June 2026 · Parque Tejo · Lisboa [CONFIRMED_FROM_FILES]
- Repository: https://github.com/iamgoncalo/planta-rock2 [CONFIRMED_FROM_FILES]
- Frozen tag: pre-architect-freeze [CONFIRMED_FROM_FILES]

## Product (the one sentence)
- Real-time WC occupancy monitoring for 8 clusters at Rock in Rio Lisboa 2026, counting people and flows only, using IR + WiFi + Prosegur camera sensor fusion. [CONFIRMED_FROM_FILES]

## Codebases
- Backend A: this repository, FastAPI 0.115, Python 3.14, port 8000, 202 tests passing — SOURCE OF TRUTH [CONFIRMED_FROM_FILES]
- Backend B: separate older codebase, port 8001 — reference only, NOT production, do not port features without explicit instruction [REQUIRED_BY_USER]
- Frontend (Next.js 15): lives under frontend/ in this repo, secondary interface [CONFIRMED_FROM_FILES]
- Embedded dashboard: app/static/index.html — single-file SPA served at GET / [CONFIRMED_FROM_FILES]
- Railway deployment: NOT VERIFIED — do not claim the backend is deployed [REQUIRED_BY_USER]
- Vercel deployment: NOT VERIFIED — do not claim the site is live [REQUIRED_BY_USER]
- Domain www.plantarockinrio.com: NOT VERIFIED — do not claim it points to anything [REQUIRED_BY_USER]

## Sections (the 14 WC sections)
- WC-01_M: cluster WC-01, male section, capacity 72 [CONFIRMED_FROM_FILES]
- WC-01_F: cluster WC-01, female section, capacity 63 [CONFIRMED_FROM_FILES]
- WC-02_M: cluster WC-02, male section, capacity 54 [CONFIRMED_FROM_FILES]
- WC-02_F: cluster WC-02, female section, capacity 72 [CONFIRMED_FROM_FILES]
- WC-03_M: cluster WC-03, male section, capacity 54 [CONFIRMED_FROM_FILES]
- WC-03_F: cluster WC-03, female section, capacity 48 [CONFIRMED_FROM_FILES]
- WC-04_M: cluster WC-04, male section, capacity 84 [CONFIRMED_FROM_FILES]
- WC-04_F: cluster WC-04, female section, capacity 66 [CONFIRMED_FROM_FILES]
- WC-05: cluster WC-05 (M38 ENTRY ONLY), unisex, capacity 133, no gender split [CONFIRMED_FROM_FILES]
- WC-06: cluster WC-06 (W39/S39), unisex, capacity 208, no gender split [CONFIRMED_FROM_FILES]
- WC-07_M: cluster WC-07, male section, capacity 84 (calha trough — not individual cabins) [CONFIRMED_FROM_FILES]
- WC-07_F: cluster WC-07, female section, capacity 54 [CONFIRMED_FROM_FILES]
- WC-08_M: cluster WC-08, male section, capacity 84 [CONFIRMED_FROM_FILES]
- WC-08_F: cluster WC-08, female section, capacity 61 [CONFIRMED_FROM_FILES]
- Total places: 1,137 [CONFIRMED_FROM_FILES]

## Forbidden in product surfaces
- CO2, temperature, humidity: forbidden everywhere — no field, no badge, no sensor [REQUIRED_BY_USER]
- Individual tracking: forbidden — only aggregated counts [REQUIRED_BY_USER]
- Raw MAC addresses: forbidden in any payload, log, or stored record [REQUIRED_BY_USER]
- GPS in telemetry payloads: forbidden — GPS is static cluster metadata only [REQUIRED_BY_USER]
- Red color (#EF4444, #FF0000, red): forbidden — critical state uses #C25A1A [REQUIRED_BY_USER]
- Deucalion: forbidden — no references anywhere in code, docs, or UI [REQUIRED_BY_USER]
- Gender field on WC-05 or WC-06: forbidden — these sections are always unisex [REQUIRED_BY_USER]
- "SIMULADO · seed=2026" badge: forbidden — removed [REQUIRED_BY_USER]
- Live data claims before 11–12 June 2026 installation: forbidden — all data is simulated until then [REQUIRED_BY_USER]
- Chat inventing live data: forbidden — chat disabled before Phase 6 closes [REQUIRED_BY_USER]

## SCOR tokens
- SCOR_TOKEN_KPI: configured via environment variable SCOR_TOKEN_KPI [CONFIRMED_FROM_FILES]
- SCOR_TOKEN_CLUSTER: not present in config.py or backend.env.example [NOT_VERIFIED]
- SCOR_BASE_URL: not present in config.py; hardcoded fallback in ops.py to https://scor.sensaway.com/api/v1 [CONFIRMED_FROM_FILES]
- Without tokens: SCOR publish silently skipped, returns status=skipped [CONFIRMED_FROM_FILES]
- Canonical token values: MISSING_DECISION — must be supplied by user via .env

## Routing cost equation
- score(cluster) = 0.5 × avg_occupancy_pct + 0.3 × min(100, queue/50 × 100) + 0.2 × min(100, dist_entrada_m/500 × 100) [CONFIRMED_FROM_FILES]
- Lower score = better candidate [CONFIRMED_FROM_FILES]
- Pressure threshold: clusters above 75% avg occupancy are considered under pressure [CONFIRMED_FROM_FILES]
- WC-05 (entry_only=True): never recommended as a relief destination [CONFIRMED_FROM_FILES]
- CRITICO clusters (>90% occupancy): excluded from candidates [CONFIRMED_FROM_FILES]

## Fusion weights
- IR: 0.50 [CONFIRMED_FROM_FILES]
- WiFi: 0.30 [CONFIRMED_FROM_FILES]
- Camera: 0.20, scaled by camera ML confidence before normalisation [CONFIRMED_FROM_FILES]
- Missing source: its weight redistributed proportionally to remaining sources [CONFIRMED_FROM_FILES]
- All-sources-missing: equal-weight fallback [CONFIRMED_FROM_FILES]
- Camera ML confidence range: 0.0–1.0 [CONFIRMED_FROM_FILES]

## Deployment targets
- Backend: Railway — NOT VERIFIED [REQUIRED_BY_USER]
- Frontend / dashboard: Vercel — NOT VERIFIED [REQUIRED_BY_USER]
- Domain: www.plantarockinrio.com — NOT VERIFIED [REQUIRED_BY_USER]
- Local start command: cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000 [CONFIRMED_FROM_FILES]
- WebSocket broadcast interval: 5 seconds [CONFIRMED_FROM_FILES]
- Sensor installation date: 11–12 June 2026 [REQUIRED_BY_USER]
- Festival days: 20, 21, 27, 28 June 2026 [CONFIRMED_FROM_FILES]
- Admin PIN default: planta2026 (weak — must be changed before deployment) [CONFIRMED_FROM_FILES]

## Status board
- Tests: 202 passing, 0 failing [CONFIRMED_FROM_FILES]
- Tag: pre-architect-freeze pushed to origin [CONFIRMED_FROM_FILES]
- API endpoints: 15 live (health, clusters, clusters/{id}, kpis, shows, alerts, routing/recommend, nearest-wc, sensor, prosegur, publish, simulate/tick, chat, density-grid, cabins/{cluster_id}) [CONFIRMED_FROM_FILES]
- New pages: /manutencao (maintenance + sensor health) [CONFIRMED_FROM_FILES]
- Density grid: 53×38 = 2,014 cells at 10m resolution, Fruin LoS A–F [CONFIRMED_FROM_FILES]
- Physical sensors: none online — all data is SIMULATED [REQUIRED_BY_USER]
- Railway: NOT VERIFIED [REQUIRED_BY_USER]
- Vercel: NOT VERIFIED [REQUIRED_BY_USER]
- Domain: NOT VERIFIED [REQUIRED_BY_USER]
- Open HIGH items: H-03 (retention policy), H-04 (geolocation CTA on visitor home) [CONFIRMED_FROM_FILES]
- Queue theory BLOCKERs: Q-02 (Little's Law), Q-03 (ρ≥1 undetected) — simulation accuracy only [CONFIRMED_FROM_FILES]
