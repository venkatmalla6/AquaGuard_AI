"""
AquaGuard AI - Research Benchmark Experiments API Tests
"""
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_experiments(async_client: AsyncClient):
    """Test listing all registered research experiments."""
    response = await async_client.get("/api/experiments")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3  # At least EXP-A, EXP-B, EXP-C

@pytest.mark.asyncio
async def test_get_experiment_comparison(async_client: AsyncClient):
    """Test retrieving comparison matrix across all models (Phase 10)."""
    response = await async_client.get("/api/experiments/comparison")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "f1_score" in data[0]
    assert "improvement_f1_pct" in data[0]
