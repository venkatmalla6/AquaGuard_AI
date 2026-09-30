"""
AquaGuard AI - System Diagnostics, Hardware Telemetry & Edge AI Optimization Endpoints (Phase 12)
Provides real-time host resource utilization, edge inference health,
ONNX/TorchScript hardware acceleration, and dynamic benchmark suite.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
import psutil
from pydantic import BaseModel, Field

# Ensure root dir in path for AI imports
root_dir = str(Path(__file__).parent.parent.parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.api.deps.auth import get_current_user
from app.core.config import settings
from app.models.models import User
from ai.optimization.edge_inference import EdgeLSTMInference
from ai.optimization.cv_optimizer import OpenCVOptimizer
from ai.optimization.model_exporter import run_export_pipeline

router = APIRouter()

# In-memory edge state
EDGE_STATE = {
    "engine": "onnx",
    "enable_frame_skipping": True,
    "target_fps": 30.0,
    "idle_stride": 3,
    "max_stride": 4,
}


class EdgeConfigRequest(BaseModel):
    engine: str = Field("onnx", description="Inference engine backend: onnx, torchscript, or pytorch")
    enable_frame_skipping: bool = Field(True, description="Enable risk-sensitive adaptive frame skipping")
    target_fps: float = Field(30.0, ge=5.0, le=60.0, description="Target processing framerate")


class BenchmarkRequest(BaseModel):
    iterations: int = Field(25, ge=5, le=100)
    batch_sizes: List[int] = Field(default_factory=lambda: [1, 4, 16])


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
            "cpu_physical_count": psutil.cpu_count(logical=False),
            "ram_percent": vm.percent,
            "ram_used_gb": round(vm.used / (1024**3), 2),
            "ram_total_gb": round(vm.total / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "gpu_available": False,
            "inference_device": "CPU",
            "active_edge_engine": EDGE_STATE["engine"].upper(),
        },
        "ai_pipeline": {
            "yolo_model": settings.YOLO_MODEL,
            "yolo_confidence": settings.YOLO_CONFIDENCE,
            "tracker": settings.TRACKER,
            "temporal_model": settings.TEMPORAL_MODEL,
            "sequence_length": settings.SEQUENCE_LENGTH,
            "alert_persistence_frames": settings.ALERT_CONSECUTIVE_FRAMES,
            "edge_acceleration": EDGE_STATE["engine"],
            "adaptive_frame_skipping": EDGE_STATE["enable_frame_skipping"],
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
        "edge_state": EDGE_STATE,
    }


@router.get("/edge", summary="Get Edge Optimization Status & Capabilities")
async def get_edge_status(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Retrieve edge inference acceleration capabilities, active backend,
    OpenCV SIMD acceleration status, and model artifact availability.
    """
    cv_info = OpenCVOptimizer.apply_optimizations()

    onnx_file = os.path.join(root_dir, "ai", "models", "registry", "behavior_lstm.onnx")
    ts_file = os.path.join(root_dir, "ai", "models", "registry", "behavior_lstm.torchscript.pt")
    pt_file = os.path.join(root_dir, "ai", "models", "registry", "best_model.pt")

    models_status = {
        "onnx": {
            "available": os.path.exists(onnx_file),
            "size_kb": round(os.path.getsize(onnx_file) / 1024, 1) if os.path.exists(onnx_file) else 0,
            "path": onnx_file,
        },
        "torchscript": {
            "available": os.path.exists(ts_file),
            "size_kb": round(os.path.getsize(ts_file) / 1024, 1) if os.path.exists(ts_file) else 0,
            "path": ts_file,
        },
        "pytorch": {
            "available": os.path.exists(pt_file),
            "size_kb": round(os.path.getsize(pt_file) / 1024, 1) if os.path.exists(pt_file) else 0,
            "path": pt_file,
        },
    }

    return {
        "status": "active",
        "active_engine": EDGE_STATE["engine"],
        "available_engines": ["onnx", "torchscript", "pytorch"],
        "frame_skipping": {
            "enabled": EDGE_STATE["enable_frame_skipping"],
            "target_fps": EDGE_STATE["target_fps"],
            "idle_stride": EDGE_STATE["idle_stride"],
            "max_stride": EDGE_STATE["max_stride"],
            "estimated_cpu_saving_idle_pct": 66.7,
        },
        "opencv_acceleration": cv_info,
        "hardware_concurrency": {
            "logical_cores": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False),
            "cpu_percent": psutil.cpu_percent(interval=None),
        },
        "models": models_status,
    }


@router.post("/edge/configure", summary="Update Edge Acceleration Settings")
async def configure_edge(
    config: EdgeConfigRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Hot-swap the active edge inference engine or update frame skipping parameters.
    """
    engine_name = config.engine.lower()
    if engine_name not in ("onnx", "torchscript", "pytorch"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid engine '{config.engine}'. Must be one of: onnx, torchscript, pytorch."
        )

    EDGE_STATE["engine"] = engine_name
    EDGE_STATE["enable_frame_skipping"] = config.enable_frame_skipping
    EDGE_STATE["target_fps"] = config.target_fps

    return {
        "status": "success",
        "message": f"Edge engine successfully configured to '{engine_name.upper()}'.",
        "edge_state": EDGE_STATE,
    }


@router.post("/edge/benchmark", summary="Execute Live CPU Edge Benchmark")
async def run_edge_benchmark(
    req: BenchmarkRequest = Body(...),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Executes live multi-batch benchmark comparing PyTorch vs TorchScript vs ONNX Runtime on CPU.
    """
    try:
        results = EdgeLSTMInference.benchmark_all(
            iterations=req.iterations,
            warmup=5,
            batch_sizes=req.batch_sizes
        )
        return {
            "status": "success",
            "benchmark": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark execution failed: {str(e)}")


@router.post("/edge/export-models", summary="Regenerate & Verify ONNX/TorchScript Exports")
async def export_edge_models(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Triggers model export pipeline to regenerate TorchScript and ONNX model files
    with numerical parity verification.
    """
    try:
        res = run_export_pipeline()
        return {
            "status": "success",
            "message": "Models exported and verified successfully.",
            "export_results": res,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model export failed: {str(e)}")
