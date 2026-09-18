"""
AquaGuard AI - Core Configuration
Loads settings from environment variables and config.yaml.
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import yaml


class Settings(BaseSettings):
    """
    Application settings loaded from .env file and environment variables.
    
    WHY: Pydantic-settings automatically reads .env and validates types.
    This prevents hard-coded secrets and makes the app 12-factor compliant.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "AquaGuard AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key-CHANGE-IN-PRODUCTION"

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./aquaguard.db"  # SQLite fallback for dev

    # JWT
    JWT_SECRET_KEY: str = "jwt-dev-secret-CHANGE-IN-PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # AI
    YOLO_MODEL: str = "yolov8n.pt"
    YOLO_CONFIDENCE: float = 0.5
    YOLO_IOU: float = 0.45
    TRACKER: str = "bytetrack"

    # Temporal
    TEMPORAL_MODEL: str = "lstm"
    SEQUENCE_LENGTH: int = 32
    TEMPORAL_CONFIDENCE: float = 0.8
    ALERT_CONSECUTIVE_FRAMES: int = 5

    # Alert
    ALERT_COOLDOWN_SECONDS: int = 30

    # Upload
    MAX_UPLOAD_SIZE_MB: int = 500
    UPLOAD_DIR: str = "./uploads"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/aquaguard.log"

    # IoT
    IOT_SIMULATION_MODE: bool = True

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def upload_dir_path(self) -> Path:
        path = Path(self.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


def load_yaml_config(config_path: str = "config/config.yaml") -> dict:
    """
    Load YAML configuration file.
    
    WHY: YAML config provides a human-readable way to manage AI/CV parameters
    without requiring code changes or environment variable proliferation.
    """
    path = Path(config_path)
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


# Singleton settings instance
settings = Settings()

# Load YAML config
yaml_config = load_yaml_config()
