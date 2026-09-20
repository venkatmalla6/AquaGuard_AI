"""
AquaGuard AI - FastAPI Application Entry Point

This is the main application file. It:
1. Creates the FastAPI app instance
2. Configures CORS (Cross-Origin Resource Sharing)
3. Registers all API routers
4. Sets up WebSocket endpoints
5. Initializes the database on startup
6. Configures structured logging

WHY FastAPI: 
- Automatic OpenAPI documentation (crucial for API.md)
- Native async support matches our async database
- Pydantic integration for request/response validation
- WebSocket support for real-time monitoring
"""
import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.config import settings
from app.database.db import create_db_and_tables


# ============================================================
# Logging Setup
# ============================================================
# Remove default handler and add structured logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
    colorize=True,
)

# Create logs directory
Path("./logs").mkdir(exist_ok=True)
logger.add(
    settings.LOG_FILE,
    rotation="50 MB",
    retention="30 days",
    level=settings.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}",
)


# ============================================================
# Application Lifecycle
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.
    WHY lifespan context manager: FastAPI recommends this over @app.on_event
    as it provides clear startup/shutdown boundaries and proper cleanup.
    """
    # STARTUP
    logger.info(f"Starting {settings.APP_NAME} v1.0.0")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Initialize database
    try:
        await create_db_and_tables()
        logger.info("Database initialized successfully.")
        try:
            from app.database.seed import seed_initial_data
            await seed_initial_data()
        except Exception as e:
            logger.error(f"Seeding failed: {e}")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("Continuing without database - some features will be unavailable.")
    
    # Create upload directories
    settings.upload_dir_path  # This creates the directory
    
    logger.info(f"AquaGuard AI is ready. API docs: http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}/docs")
    
    yield  # Application runs here
    
    # SHUTDOWN
    logger.info("Shutting down AquaGuard AI...")


# ============================================================
# FastAPI App Instance
# ============================================================
app = FastAPI(
    title="AquaGuard AI",
    description="""
    ## Real-Time Drowning Detection System
    
    AquaGuard AI uses YOLO person detection, ByteTrack person tracking, and 
    LSTM temporal behavior analysis to detect potential drowning events in 
    swimming pool surveillance footage.
    
    ### Research System
    This API supports comparative experiments between:
    - **Baseline**: YOLOv8 frame-level detection
    - **Proposed**: YOLOv8 + ByteTrack + LSTM temporal analysis
    
    ### WebSocket Endpoints
    - `/ws/monitoring` — Live detection stream
    - `/ws/alerts` — Real-time alert notifications  
    - `/ws/metrics` — System performance metrics
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ============================================================
# CORS Middleware
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Static Files (for saved snapshots/clips)
# ============================================================
uploads_dir = Path("./uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


# ============================================================
# Health Check (basic, no DB required)
# ============================================================
@app.get("/health", tags=["System"])
async def health_check():
    """
    Basic health check endpoint.
    Returns 200 if the server is running.
    No authentication required.
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "demo_mode": True,
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "message": "AquaGuard AI — Real-Time Drowning Detection System",
        "docs": "/docs",
        "health": "/health",
    }


# ============================================================
# API Routers (imported when implemented)
# ============================================================
# These will be uncommented as each phase is implemented:
#
from app.api.routes import auth, cameras, alerts, experiments, system, videos

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(cameras.router, prefix="/api/cameras", tags=["Cameras"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(experiments.router, prefix="/api/experiments", tags=["Experiments"])
app.include_router(system.router, prefix="/api/system", tags=["System"])
app.include_router(videos.router, prefix="/api/videos", tags=["Videos"])


# ============================================================
# WebSocket Endpoints (stub - implemented in Phase 9)
# ============================================================
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio

@app.websocket("/ws/monitoring")
async def ws_monitoring(websocket: WebSocket):
    """Live detection and tracking stream."""
    await websocket.accept()
    logger.info("WebSocket client connected to /ws/monitoring")
    try:
        while True:
            # Placeholder: will emit real detection data in Phase 4/5
            await websocket.send_json({
                "type": "heartbeat",
                "message": "AquaGuard AI monitoring active",
                "demo_mode": True
            })
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected from /ws/monitoring")


@app.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    """Real-time alert notifications."""
    await websocket.accept()
    logger.info("WebSocket client connected to /ws/alerts")
    try:
        while True:
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected from /ws/alerts")


@app.websocket("/ws/metrics")
async def ws_metrics(websocket: WebSocket):
    """System performance metrics stream."""
    import psutil
    await websocket.accept()
    logger.info("WebSocket client connected to /ws/metrics")
    try:
        while True:
            metrics = {
                "type": "system_metrics",
                "cpu_percent": psutil.cpu_percent(interval=None),
                "ram_percent": psutil.virtual_memory().percent,
                "ram_used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
                "gpu_available": False,
                "fps": None,  # Will be filled by inference pipeline
                "latency_ms": None,
            }
            await websocket.send_json(metrics)
            await asyncio.sleep(settings.LOG_LEVEL and 5)  # every 5s
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected from /ws/metrics")


# ============================================================
# Run directly (development only)
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
