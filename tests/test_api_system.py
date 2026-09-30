"""
AquaGuard AI - System Diagnostics & Edge AI Optimization API Tests
"""
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_system_status(async_client: AsyncClient):
    """Test /api/system/status retrieves host hardware metrics."""
    response = await async_client.get("/api/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "hardware" in data
    assert "cpu_percent" in data["hardware"]
    assert "ram_percent" in data["hardware"]
    assert data["hardware"]["inference_device"] == "CPU"

@pytest.mark.asyncio
async def test_system_config(async_client: AsyncClient):
    """Test /api/system/config returns operational settings."""
    response = await async_client.get("/api/system/config")
    assert response.status_code == 200
    data = response.json()
    assert "jwt_expiry_minutes" in data
    assert "yolo_confidence" in data

@pytest.mark.asyncio
async def test_edge_status(async_client: AsyncClient):
    """Test /api/system/edge retrieves edge capabilities and models."""
    response = await async_client.get("/api/system/edge")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["active_engine"] in ("onnx", "torchscript", "pytorch")
    assert "frame_skipping" in data
    assert "opencv_acceleration" in data
    assert "models" in data
    assert data["models"]["onnx"]["available"] is True

@pytest.mark.asyncio
async def test_edge_configure(async_client: AsyncClient):
    """Test /api/system/edge/configure updates active engine and frame skipping."""
    response = await async_client.post(
        "/api/system/edge/configure",
        json={"engine": "onnx", "enable_frame_skipping": True, "target_fps": 30.0}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["edge_state"]["engine"] == "onnx"

@pytest.mark.asyncio
async def test_edge_benchmark(async_client: AsyncClient):
    """Test /api/system/edge/benchmark executes live multi-batch CPU benchmark."""
    response = await async_client.post(
        "/api/system/edge/benchmark",
        json={"iterations": 10, "batch_sizes": [1, 4]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "benchmark" in data
    assert "batch_1" in data["benchmark"]["results"]
    assert "onnx" in data["benchmark"]["results"]["batch_1"]
