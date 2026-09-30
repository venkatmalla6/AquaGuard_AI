"""
AquaGuard AI - Authentication & Authorization Unit Tests
"""
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login_success(unauth_client: AsyncClient):
    """Test successful authentication with valid credentials."""
    response = await unauth_client.post(
        "/api/auth/login",
        json={"email": "admin@aquaguard.ai", "password": "admin"}
    )
    # The default seed admin password in seed_db is admin or admin123
    if response.status_code != 200:
        response = await unauth_client.post(
            "/api/auth/login",
            json={"email": "admin@aquaguard.ai", "password": "admin123"}
        )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_password(unauth_client: AsyncClient):
    """Test authentication failure with incorrect password."""
    response = await unauth_client.post(
        "/api/auth/login",
        json={"email": "admin@aquaguard.ai", "password": "wrong_password_999"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_me_endpoint_authenticated(async_client: AsyncClient):
    """Test /api/auth/me returns valid user profile when authenticated."""
    response = await async_client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@aquaguard.ai"
    assert data["role"] == "admin"

@pytest.mark.asyncio
async def test_me_endpoint_unauthorized(unauth_client: AsyncClient):
    """Test /api/auth/me rejects requests without valid JWT token."""
    response = await unauth_client.get("/api/auth/me")
    assert response.status_code == 401
