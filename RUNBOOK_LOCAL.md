# PlantaOS × Rock in Rio Lisboa 2026 — Runbook Local

**Planta Smart Homes · hi@planta.design**
**Stack: FastAPI 0.115 · Python 3.14 · Next.js 15 · TypeScript**

---

## Prerequisites

- Python 3.12+ (tested on 3.14)
- Node.js 18+ and npm
- A terminal

---

## Quick Open (single command)

Just run the backend — the dashboard is embedded:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Open: **http://localhost:8000** — full dashboard, live data.

The Next.js frontend (`npm run dev`) is still available at http://localhost:3000 as a secondary interface.

---

## 1. Start the Backend

```bash
cd backend

# Create virtual environment (first time only)
python3 -m venv .venv

# Activate
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows

# Install dependencies (first time only)
pip install -e ".[dev]"

# Start server
uvicorn app.main:app --reload --port 8000
```

Backend is ready when you see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     PlantaOS backend starting up…
INFO:     State initialised with scenario: normal_day
```

Verify: http://localhost:8000/api/v1/health → `{"status":"ok","ts":...,"version":"1.0.0"}`

---

## 2. Start the Frontend

Open a **second terminal**:

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

Frontend is ready when you see:
```
▲ Next.js 15.x.x
- Local: http://localhost:3000
```

Open: http://localhost:3000/twin

---

## 3. Run Backend Tests

```bash
cd backend
source .venv/bin/activate
pytest
```

Expected: **140 passed** in ~13 seconds.

```bash
pytest -v                    # verbose output
pytest tests/test_api.py     # single file
pytest -k "wc05"             # filter by name
```

---

## 4. Run Frontend Checks

```bash
cd frontend
npm run typecheck    # TypeScript — expect 0 errors
npm run lint         # ESLint — expect 0 warnings/errors
npm test             # smoke (placeholder, always exits 0)
```

---

## 5. Environment Variables

### Backend (optional — all have safe defaults)

Copy `backend/backend.env.example` to `backend/.env` and adjust:

```bash
# Optional — Gemini AI chat
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash-preview-05-14

# Optional — SCOR Sensaway publishing
SCOR_TOKEN_KPI=gGQhPd2c1kVqQjQglsmt
SCOR_TOKEN_CLUSTER=04614480-c43a-1f5f-af68-86c606bddb32
SCOR_BASE_URL=https://scor.sensaway.com/api/v1

# Optional — simulation
SIMULATION_INITIAL_SCENARIO=normal_day
SIMULATION_TICK_INTERVAL_S=5

# Optional — admin PIN for counter reset
ADMIN_PIN=1234
```

Without any env vars the system runs fully in local simulation mode.

### Frontend

`frontend/.env.local` is pre-configured for local development:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/v1/ws
```

---

## 6. Available URLs (local)

| URL | Description |
|-----|-------------|
| http://localhost:8000/api/v1/health | Backend health |
| http://localhost:8000/api/v1/clusters | All 8 WC clusters (JSON) |
| http://localhost:8000/api/v1/kpis | 4 global KPIs |
| http://localhost:8000/api/v1/shows | Show programme |
| http://localhost:8000/docs | FastAPI Swagger UI |
| http://localhost:3000/twin | Digital Twin map |
| http://localhost:3000/occupation | WC occupancy cards |
| http://localhost:3000/sensors | Sensor health |
| http://localhost:3000/shows | Show programme |
| http://localhost:3000/chat | AI chat |
| http://localhost:3000/ops | Operations dashboard |
| http://localhost:3000/app | Public visitor app |

---

## 7. Simulation Scenarios

Trigger a specific scenario via the API:

```bash
# Switch to headliner surge scenario
curl -X POST http://localhost:8000/api/v1/simulate/tick \
  -H "Content-Type: application/json" \
  -d '{"scenario": "headliner_end_surge"}'

# Back to normal
curl -X POST http://localhost:8000/api/v1/simulate/tick \
  -H "Content-Type: application/json" \
  -d '{"scenario": "normal_day"}'
```

Available scenarios:
- `normal_day`
- `headliner_start`
- `headliner_end_surge`
- `wc05_overcrowded`
- `wc06_relief`
- `sensor_ir_offline`
- `wifi_offline`
- `camera_offline`
- `all_sensors_degraded`
- `prosegur_disagreement`
- `entry_only_pressure`
- `rain_surge`
- `crowd_surge`
- `network_dropout`
- `recovery_after_redirect`

---

## 8. Inject a Sensor Reading (simulate a LilyGo)

```bash
curl -X POST http://localhost:8000/api/v1/sensor \
  -H "Content-Type: application/json" \
  -d '{
    "cluster_id": "WC-01",
    "ts": 1750420800,
    "telemoveis_detectados": 47,
    "pessoas_estimadas_wifi": 19,
    "entradas_ir": 23,
    "saidas_ir": 21,
    "ocupacao_ir": 2,
    "uptime_s": 3600
  }'
```

---

## 9. Inject a Prosegur Camera Reading

```bash
curl -X POST http://localhost:8000/api/v1/prosegur \
  -H "Content-Type: application/json" \
  -d '{
    "cluster_id": "WC-03",
    "ts": 1750420800,
    "contagem_total": 42,
    "confianca_ml": 85
  }'
```

---

## 10. Test Chat (local fallback, no Gemini key needed)

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"mensagem": "Qual o WC mais livre?", "historico": []}'
```

---

## 11. WebSocket Test

```javascript
// In browser console at localhost:3000
const ws = new WebSocket("ws://localhost:8000/api/v1/ws")
ws.onmessage = e => console.log(JSON.parse(e.data))
// Should immediately receive full state snapshot
```

---

## 12. Common Issues

### Backend won't start
- Check Python version: `python3 --version` (need 3.12+)
- Activate venv: `source .venv/bin/activate`
- Reinstall: `pip install -e ".[dev]"`

### Frontend can't reach backend
- Ensure backend is running on port 8000
- Check `frontend/.env.local` has correct URLs
- CORS is pre-configured for localhost:3000

### TypeScript errors
- `npm install` in frontend directory
- Delete `tsconfig.tsbuildinfo` and retry

### Port 8000 already in use
- `lsof -ti:8000 | xargs kill` (macOS/Linux)
- Or start on different port: `uvicorn app.main:app --port 8001`
- Update `frontend/.env.local` accordingly

### Port 3000 already in use
- Next.js will auto-select 3001, 3002, etc.
- Update `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` accordingly (ws:// not wss://)
