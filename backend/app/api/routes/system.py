"""
AquaGuard AI - System Diagnostics & Telemetry Endpoints
Provides real-time host resource utilization and edge inference health.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends
import psutil

from app.api.deps.auth import get_current_user
from app.core.config import settings
from app.models.models import User

router = APIRouter()


@router.get("/status", summary="System Health & Hardware Telemetry")
async def get_system_status(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Retrieve real-time host metrics: CPU usage, memory allocation,
    disk storage, and inference hardware readiness.
    """
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "hardware": {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "cpu_count": psutil.cpu_count(logical=True),
            "ram_percent": vm.percent,
            "ram_used_gb": round(vm.used / (1024**3), 2),
            "ram_total_gb": round(vm.total / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "gpu_available": False,
            "inference_device": "CPU",
        },
        "ai_pipeline": {
            "yolo_model": settings.YOLO_MODEL,
            "yolo_confidence": settings.YOLO_CONFIDENCE,
            "tracker": settings.TRACKER,
            "temporal_model": settings.TEMPORAL_MODEL,
            "sequence_length": settings.SEQUENCE_LENGTH,
            "alert_persistence_frames": settings.ALERT_CONSECUTIVE_FRAMES,
        },
    }


@router.get("/config", summary="Read System Configuration")
async def get_system_config(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Retrieve non-sensitive system configuration parameters."""
    return {
        "app_name": settings.APP_NAME,
        "app_env": settings.APP_ENV,
        "debug": settings.DEBUG,
        "jwt_expiry_minutes": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        "yolo_confidence": settings.YOLO_CONFIDENCE,
        "alert_cooldown_seconds": settings.ALERT_COOLDOWN_SECONDS,
        "iot_simulation_mode": settings.IOT_SIMULATION_MODE,
    }