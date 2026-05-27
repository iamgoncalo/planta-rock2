"""
Sensors health router — GET /api/v1/sensors

Returns simulated sensor health records for all 8 WC clusters.
Since hardware is not yet installed, health is DETERMINISTIC SIMULATED
seeded by hash(cluster_id + str(datetime.now().hour)).
"""
from __future__ import annotations

import datetime
import random
from typing import Any, Dict, List

from fastapi import APIRouter

from app.data.clusters import CLUSTERS

router = APIRouter(tags=["sensors"])

CLUSTER_IDS = [c["id"] for c in CLUSTERS]


def _make_status(rng: random.Random) -> str:
    """Return 'online', 'degraded', or 'offline' with 80/15/5 probability."""
    roll = rng.random()
    if roll < 0.80:
        return "online"
    elif roll < 0.95:
        return "degraded"
    else:
        return "offline"


def _make_confidence(rng: random.Random, status: str) -> float:
    if status == "online":
        return round(rng.uniform(85.0, 99.9), 1)
    elif status == "degraded":
        return round(rng.uniform(40.0, 74.9), 1)
    else:
        return round(rng.uniform(0.0, 20.0), 1)


def _make_last_seen(rng: random.Random, status: str) -> float:
    if status == "online":
        return round(rng.uniform(0.5, 30.0), 1)
    elif status == "degraded":
        return round(rng.uniform(30.0, 180.0), 1)
    else:
        return round(rng.uniform(180.0, 3600.0), 1)


def _build_record(cluster_id: str, hour: int) -> Dict[str, Any]:
    seed = hash(cluster_id + str(hour)) & 0xFFFFFFFF
    rng = random.Random(seed)

    lilygo_status = _make_status(rng)
    lilygo_rssi = rng.randint(-85, -40) if lilygo_status != "offline" else rng.randint(-110, -90)
    lilygo_last = _make_last_seen(rng, lilygo_status)

    ir_entry_status = _make_status(rng)
    ir_entry_conf = _make_confidence(rng, ir_entry_status)
    ir_entry_last = _make_last_seen(rng, ir_entry_status)

    ir_exit_status = _make_status(rng)
    ir_exit_conf = _make_confidence(rng, ir_exit_status)
    ir_exit_last = _make_last_seen(rng, ir_exit_status)

    wifi_status = _make_status(rng)
    wifi_last = _make_last_seen(rng, wifi_status)
    wifi_devices = rng.randint(5, 60) if wifi_status != "offline" else 0

    camera_status = _make_status(rng)
    camera_conf = _make_confidence(rng, camera_status)
    camera_last = _make_last_seen(rng, camera_status)

    lorawan_status = _make_status(rng)
    lorawan_last = _make_last_seen(rng, lorawan_status)

    # Overall confidence: average of available source confidences
    conf_values = []
    if ir_entry_status != "offline":
        conf_values.append(ir_entry_conf)
    if ir_exit_status != "offline":
        conf_values.append(ir_exit_conf)
    if camera_status != "offline":
        conf_values.append(camera_conf)
    if lilygo_status != "offline":
        conf_values.append(80.0)
    overall_confidence = round(sum(conf_values) / len(conf_values), 1) if conf_values else 0.0

    # Collect issues
    issues: List[str] = []
    if lilygo_status == "offline":
        issues.append("LilyGo offline")
    elif lilygo_status == "degraded":
        issues.append("LilyGo degraded")
    if ir_entry_status == "offline":
        issues.append("IR entry offline")
    if ir_exit_status == "offline":
        issues.append("IR exit offline")
    if camera_status == "offline":
        issues.append("Camera ML offline")
    if lorawan_status == "offline":
        issues.append("LoRaWAN offline")

    return {
        "cluster_id": cluster_id,
        "lilygo": {
            "status": lilygo_status,
            "last_seen_s": lilygo_last,
            "rssi": lilygo_rssi,
            "transport": "wifi",
        },
        "ir_entry": {
            "status": ir_entry_status,
            "last_seen_s": ir_entry_last,
            "confidence": ir_entry_conf,
        },
        "ir_exit": {
            "status": ir_exit_status,
            "last_seen_s": ir_exit_last,
            "confidence": ir_exit_conf,
        },
        "wifi_aggregate": {
            "status": wifi_status,
            "last_seen_s": wifi_last,
            "devices_detected": wifi_devices,
        },
        "camera_ml": {
            "status": camera_status,
            "last_seen_s": camera_last,
            "confidence": camera_conf,
        },
        "lorawan": {
            "status": lorawan_status,
            "last_seen_s": lorawan_last,
        },
        "overall_confidence": overall_confidence,
        "issues": issues,
        "simulado": True,
    }


@router.get("/sensors")
async def get_sensors_health() -> List[Dict[str, Any]]:
    """Return deterministic simulated sensor health for all 8 clusters."""
    hour = datetime.datetime.now().hour
    return [_build_record(cid, hour) for cid in CLUSTER_IDS]
