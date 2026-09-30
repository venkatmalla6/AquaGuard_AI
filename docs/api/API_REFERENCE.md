# AQUAGUARD AI: REST & WEBSOCKET API SPECIFICATION REFERENCE
## 1. Overview & Architecture
AquaGuard AI provides an asynchronous REST and WebSocket API built with FastAPI.
- Base URL: http://localhost:8000/api
- WebSocket Base URL: ws://localhost:8000/ws
- Interactive Documentation: Swagger UI at /docs and ReDoc at /redoc

## 2. Authentication Endpoints (/api/auth)
- POST /api/auth/login: Authenticates user, returns JWT access token.
- GET /api/auth/me: Returns current authenticated user profile.

## 3. Camera Management Endpoints (/api/cameras)
- GET /api/cameras: List all registered cameras.
- POST /api/cameras: Register new camera.
- GET /api/cameras/{id}: Retrieve camera details.

## 4. Alert & Emergency Dispatch Endpoints (/api/alerts)
- GET /api/alerts: Query incident alerts with severity filters.
- POST /api/alerts/{id}/acknowledge: Acknowledge alert with responder notes.
- GET /api/alerts/channels: Retrieve multi-channel dispatch status.
- POST /api/alerts/test-dispatch: Trigger emergency drill across channels.

## 5. System & Edge Computing Endpoints (/api/system)
- GET /api/system/health: Health check and service uptime.
- GET /api/system/edge: Edge engine status (onnx, torchscript, pytorch, threads, stride).
- POST /api/system/edge/configure: Configure active engine, CPU threads, and adaptive skipping.
- POST /api/system/edge/benchmark: Execute latency and throughput benchmarks.
- POST /api/system/edge/export-models: Export TorchScript and ONNX model artifacts.

## 6. Research & Paper Assets Endpoints (/api/experiments)
- GET /api/experiments: List completed benchmark experiments.
- POST /api/experiments/run: Execute automated research experiments.
- GET /api/experiments/paper-assets: Retrieve metadata for 300 DPI figures and LaTeX tables.
- POST /api/experiments/generate-paper-assets: Re-generate publication figures and tables.

## 7. Synthetic Scenarios Engine Endpoints (/api/scenarios)
- GET /api/scenarios: Catalog of 6 physiological scenarios.
- POST /api/scenarios/generate: Generate synthetic trajectory and MP4 video.
- POST /api/scenarios/evaluate: Automated evaluation of detection latency and SLA compliance.

## 8. Real-Time WebSocket Streaming Protocol (/ws)
- URL: ws://localhost:8000/ws/monitor/{camera_id}
- Provides low-latency per-frame telemetry: swimmer bounding boxes, state probabilities, 16-D feature values, and system stride.
