"""
Maintenance router — PlantaOS × Rock in Rio Lisboa 2026

Routes:
    GET  /manutencao                          → serve maintenance.html
    GET  /api/v1/maintenance/log              → list log entries (JSON)
    POST /api/v1/maintenance/log              → append log entry
    GET  /api/v1/maintenance/inventory        → get inventory (JSON)
    PUT  /api/v1/maintenance/inventory/{component} → update stock (PIN required)

The log is in-memory, append-only, capped at 100 entries (oldest dropped).
Inventory is initialised from INITIAL_INVENTORY and modified in place.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Pin verification
# ---------------------------------------------------------------------------

_ADMIN_PIN: str = os.environ.get("ADMIN_PIN", "planta2026")


def _check_pin(pin: str | None) -> None:
    """Raise 403 if pin does not match the configured admin pin."""
    if pin != _ADMIN_PIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PIN inválido",
        )


# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------

_MAX_LOG_ENTRIES = 100

_log_entries: List[Dict[str, Any]] = []

INITIAL_INVENTORY: List[Dict[str, Any]] = [
    {"component": "Reed MC-38",           "stock": 20,  "minimum": 10, "unit": "pcs"},
    {"component": "IR E18-D80NK",         "stock": 8,   "minimum": 4,  "unit": "pcs"},
    {"component": "LilyGo T-SIM7670",     "stock": 2,   "minimum": 2,  "unit": "pcs"},
    {"component": "PoE injector",         "stock": 10,  "minimum": 4,  "unit": "pcs"},
    {"component": "CAT6 cable (m)",       "stock": 100, "minimum": 50, "unit": "m"},
]

# Keyed by component name for fast lookup
_inventory: Dict[str, Dict[str, Any]] = {
    row["component"]: dict(row) for row in INITIAL_INVENTORY
}


def _inventory_status(stock: int, minimum: int) -> str:
    if stock <= 0:
        return "EMPTY"
    if stock <= minimum:
        return "WARNING"
    return "OK"


def _inventory_list() -> List[Dict[str, Any]]:
    result = []
    for row in _inventory.values():
        out = dict(row)
        out["status"] = _inventory_status(out["stock"], out["minimum"])
        result.append(out)
    return result


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class LogEntryIn(BaseModel):
    technician: str = Field(..., min_length=1, max_length=100)
    cluster: str = Field(..., min_length=1, max_length=20)
    action: str = Field(..., min_length=1, max_length=200)
    notes: Optional[str] = Field("", max_length=500)


class InventoryUpdate(BaseModel):
    stock: int = Field(..., ge=0)
    pin: str = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

# Serves the HTML page at /manutencao
router = APIRouter(tags=["maintenance"])

# API endpoints (to be mounted at /api/v1)
api_router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.get("/manutencao", include_in_schema=False)
async def serve_maintenance() -> FileResponse:
    """Serve the maintenance HTML page."""
    html_path = Path(__file__).parent.parent / "static" / "maintenance.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="maintenance.html not found")
    return FileResponse(str(html_path), media_type="text/html")


@api_router.get("/log")
async def get_log() -> Dict[str, Any]:
    """Return all maintenance log entries, most recent first."""
    return {
        "ts": time.time(),
        "count": len(_log_entries),
        "entries": list(reversed(_log_entries)),
    }


@api_router.post("/log", status_code=status.HTTP_201_CREATED)
async def add_log_entry(body: LogEntryIn) -> Dict[str, Any]:
    """Append a new maintenance log entry (no auth required)."""
    entry: Dict[str, Any] = {
        "id": len(_log_entries) + 1,
        "ts": time.time(),
        "technician": body.technician.strip(),
        "cluster": body.cluster.strip(),
        "action": body.action.strip(),
        "notes": (body.notes or "").strip(),
    }
    _log_entries.append(entry)
    # Cap at MAX_LOG_ENTRIES (drop oldest)
    if len(_log_entries) > _MAX_LOG_ENTRIES:
        _log_entries.pop(0)
    return {"ok": True, "entry": entry}


@api_router.get("/inventory")
async def get_inventory() -> Dict[str, Any]:
    """Return current spare-parts inventory with computed status."""
    return {
        "ts": time.time(),
        "inventory": _inventory_list(),
    }


@api_router.put("/inventory/{component}")
async def update_inventory(component: str, body: InventoryUpdate) -> Dict[str, Any]:
    """Update stock for a component (PIN required)."""
    _check_pin(body.pin)
    # URL-decode component name (spaces encoded as %20)
    from urllib.parse import unquote
    comp_name = unquote(component)
    if comp_name not in _inventory:
        raise HTTPException(status_code=404, detail=f"Component '{comp_name}' not found")
    _inventory[comp_name]["stock"] = body.stock
    updated = dict(_inventory[comp_name])
    updated["status"] = _inventory_status(updated["stock"], updated["minimum"])
    return {"ok": True, "item": updated}
