"""
Health check router — GET /api/v1/health
"""
from __future__ import annotations

import time

from fastapi import APIRouter

from app.config import get_settings
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Returns application health status."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        ts=time.time(),
        version=settings.app_version,
    )
