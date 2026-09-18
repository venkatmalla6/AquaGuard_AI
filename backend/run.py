"""
Entry point for running the AquaGuard AI backend.
Run: python run.py
"""
import uvicorn
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings

if __name__ == "__main__":
    print(f"Starting {settings.APP_NAME}...")
    print(f"API Docs: http://localhost:{settings.BACKEND_PORT}/docs")
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
