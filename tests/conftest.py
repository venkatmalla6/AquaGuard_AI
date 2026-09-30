"""
AquaGuard AI - Pytest Test Configuration & Shared Fixtures (Phase 13)
Provides asynchronous database sessions, FastAPI test clients, synthetic frames,
and mocked hardware telemetry.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import AsyncGenerator
import pytest
import pytest_asyncio
import numpy as np
from httpx import AsyncClient, ASGITransport

# Configure paths
root_dir = str(Path(__file__).parent.parent)
backend_dir = os.path.join(root_dir, "backend")
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.core.config import settings
from app.database.db import get_session
from app.api.deps.auth import create_access_token
from app.models.models import User

@pytest.fixture(scope="session")
def admin_token() -> str:
    """JWT token for administrator role."""
    return create_access_token(data={"sub": "admin@aquaguard.ai", "role": "admin"})

@pytest.fixture(scope="session")
def operator_token() -> str:
    """JWT token for operator/lifeguard role."""
    return create_access_token(data={"sub": "operator@aquaguard.ai", "role": "operator"})

@pytest.fixture(scope="session")
def researcher_token() -> str:
    """JWT token for research scientist role."""
    return create_access_token(data={"sub": "researcher@aquaguard.ai", "role": "researcher"})

@pytest_asyncio.fixture
async def async_client(admin_token: str) -> AsyncGenerator[AsyncClient, None]:
    """Authenticated HTTP client fixture targeting FastAPI test app."""
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with AsyncClient(transport=transport, base_url="http://testserver", headers=headers) as client:
        yield client

@pytest_asyncio.fixture
async def unauth_client() -> AsyncGenerator[AsyncClient, None]:
    """Unauthenticated HTTP client fixture."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

@pytest.fixture
def synthetic_frame() -> np.ndarray:
    """Synthetic 640x480 RGB test video frame."""
    return np.zeros((480, 640, 3), dtype=np.uint8)

@pytest.fixture
def synthetic_drowning_features() -> np.ndarray:
    """
    16-D feature vector characteristic of a drowning victim:
    High vertical ratio, low speed, zero aspect ratio, high inactivity.
    """
    fv = np.zeros(16, dtype=np.float32)
    fv[0] = 0.5   # cx_norm
    fv[1] = 0.7   # cy_norm (sinking)
    fv[2] = 0.05  # w_norm
    fv[3] = 0.25  # h_norm
    fv[4] = 0.20  # aspect_ratio (vertical)
    fv[5] = 0.012 # area_norm
    fv[6] = 0.001 # displacement (minimal translation)
    fv[7] = 0.0   # vel_x
    fv[8] = 0.005 # vel_y
    fv[9] = 0.5   # speed (< 5.0)
    fv[10] = 0.0  # acceleration
    fv[11] = 0.0  # dir_sin
    fv[12] = 1.0  # dir_cos
    fv[13] = 10.0 # movement_variance (low thrashing / exhausted)
    fv[14] = 0.95 # vertical_ratio
    fv[15] = 0.90 # inactivity score
    return fv

@pytest.fixture
def synthetic_normal_features() -> np.ndarray:
    """
    16-D feature vector characteristic of normal horizontal swimming:
    Horizontal aspect ratio, steady speed, low inactivity, low vertical ratio.
    """
    fv = np.zeros(16, dtype=np.float32)
    fv[0] = 0.4
    fv[1] = 0.3
    fv[2] = 0.20
    fv[3] = 0.08
    fv[4] = 2.50  # horizontal body
    fv[5] = 0.016
    fv[6] = 0.04
    fv[7] = 0.03
    fv[8] = 0.01
    fv[9] = 12.0  # vigorous swimming speed
    fv[10] = 0.2
    fv[11] = 0.8
    fv[12] = 0.6
    fv[13] = 45.0
    fv[14] = 0.15 # low vertical ratio
    fv[15] = 0.05 # low inactivity
    return fv
