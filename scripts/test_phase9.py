"""
AquaGuard AI - Phase 9 Verification Script
Validates:
1. FastAPI app initialization with all routers
2. WebSocket endpoints (/ws/monitoring, /ws/alerts, /ws/metrics)
3. Video API routes and schema
"""
import sys
import asyncio
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(0, str(ROOT))

async def main():
    print("[1] Importing FastAPI app and routes...")
    from app.main import app
    print("    FastAPI app loaded successfully!")

    print("\n[2] Checking Registered Routes:")
    routes = [r.path for r in app.routes]
    expected = [
        "/health",
        "/api/auth/login",
        "/api/cameras",
        "/api/alerts",
        "/api/experiments",
        "/api/system/status",
        "/api/videos",
        "/api/videos/upload",
        "/ws/monitoring",
        "/ws/alerts",
        "/ws/metrics",
    ]
    for exp in expected:
        assert any(exp in r for r in routes), f"Missing expected route: {exp}"
        print(f"    [OK] Found route matching: {exp}")

    print("\n[3] Testing WebSocket Handlers with Starlette TestClient...")
    from starlette.testclient import TestClient
    client = TestClient(app)

    # Health check
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.status_code}"
    print("    [OK] /health returns 200 OK")

    # WebSocket /ws/metrics
    with client.websocket_connect("/ws/metrics") as ws:
        data = ws.receive_json()
        assert data.get("type") == "system_metrics"
        assert "cpu_percent" in data
        assert "pipeline_fps" in data
        print(f"    [OK] /ws/metrics emitted: {data['type']}, CPU: {data['cpu_percent']}%, FPS: {data['pipeline_fps']}")

    # WebSocket /ws/monitoring
    with client.websocket_connect("/ws/monitoring") as ws:
        data = ws.receive_json()
        assert data.get("type") == "frame_result"
        assert len(data.get("tracks", [])) > 0
        t0 = data["tracks"][0]
        assert "track_id" in t0
        assert "feature_vector" in t0
        assert len(t0["feature_vector"]) == 16
        print(f"    [OK] /ws/monitoring emitted frame #{data.get('frame_number')} with {len(data['tracks'])} tracks and 16-D vectors")

    print("\n[4] All Phase 9 Backend & WebSocket verifications PASSED successfully!")

if __name__ == "__main__":
    asyncio.run(main())



