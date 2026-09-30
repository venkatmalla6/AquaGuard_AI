"""
AquaGuard AI - Alert Management & Multi-Channel Dispatch API Tests
"""
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_alerts(async_client: AsyncClient):
    """Test retrieving alert incidents list."""
    response = await async_client.get("/api/alerts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_get_alert_channels(async_client: AsyncClient):
    """Test retrieving multi-channel dispatch capabilities."""
    response = await async_client.get("/api/alerts/channels")
    assert response.status_code == 200
    data = response.json()
    assert "webhook" in data
    assert "iot_siren" in data
    assert "websocket_push" in data

@pytest.mark.asyncio
async def test_test_dispatch(async_client: AsyncClient):
    """Test triggering emergency drill broadcast across all channels."""
    response = await async_client.post("/api/alerts/test-dispatch")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "drill_alert_id" in data
    assert "dispatch_summary" in data
