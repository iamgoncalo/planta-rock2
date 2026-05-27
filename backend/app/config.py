"""
Application configuration using pydantic-settings.
All values can be overridden via environment variables or a .env file.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_reload: bool = True
    app_version: str = "1.0.0"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000"

    # Optional integrations
    gemini_api_key: str = ""
    scor_token_kpi: str = ""

    # Simulation
    simulation_tick_interval_seconds: float = 5.0
    simulation_initial_scenario: str = "normal_day"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def gemini_enabled(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def scor_enabled(self) -> bool:
        return bool(self.scor_token_kpi)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
