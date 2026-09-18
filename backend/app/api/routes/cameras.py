"""
AquaGuard AI - Camera Management Endpoints
CRUD operations for physical CCTV feeds, RTSP streams, and webcams.
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps.auth import get_current_user, require_role
from app.database.db import get_session
from app.models.models import Camera, CameraStatus, User

router = APIRouter()


class CameraCreate(BaseModel):
    name: str
    location: str
    stream_url: str
    status: Optional[CameraStatus] = CameraStatus.ONLINE
    is_active: Optional[bool] = True
    resolution_width: Optional[int] = 1280
    resolution_height: Optional[int] = 720
    fps: Optional[float] = 30.0
    notes: Optional[str] = None


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    stream_url: Optional[str] = None
    status: Optional[CameraStatus] = None
    is_active: Optional[bool] = None
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None
    fps: Optional[float] = None
    notes: Optional[str] = None


@router.get("", response_model=List[Camera], summary="List Cameras")
async def list_cameras(
    is_active: Optional[bool] = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List all registered surveillance cameras."""
    statement = select(Camera)
    if is_active is not None:
        statement = statement.where(Camera.is_active == is_active)
    result = await session.execute(statement)
    return result.scalars().all()


@router.post("", response_model=Camera, status_code=status.HTTP_201_CREATED, summary="Register Camera")
async def create_camera(
    camera_in: CameraCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(["admin", "operator"])),
):
    """Register a new pool surveillance camera stream (Admin/Operator only)."""
    camera = Camera(
        name=camera_in.name,
        location=camera_in.location,
        stream_url=camera_in.stream_url,
        status=camera_in.status or CameraStatus.ONLINE,
        is_active=camera_in.is_active if camera_in.is_active is not None else True,
        resolution_width=camera_in.resolution_width,
        resolution_height=camera_in.resolution_height,
        fps=camera_in.fps,
        notes=camera_in.notes,
        created_at=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc),
    )
    session.add(camera)
    await session.commit()
    await session.refresh(camera)
    return camera


@router.get("/{camera_id}", response_model=Camera, summary="Get Camera Details")
async def get_camera(
    camera_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Retrieve detailed telemetry and configuration for a specific camera."""
    camera = await session.get(Camera, camera_id)
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    return camera


@router.put("/{camera_id}", response_model=Camera, summary="Update Camera")
async def update_camera(
    camera_id: int,
    camera_in: CameraUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(["admin", "operator"])),
):
    """Update camera configuration (Admin/Operator only)."""
    camera = await session.get(Camera, camera_id)
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")

    update_data = camera_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(camera, field, value)

    session.add(camera)
    await session.commit()
    await session.refresh(camera)
    return camera


@router.delete("/{camera_id}", summary="Delete Camera")
async def delete_camera(
    camera_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(["admin"])),
):
    """Remove a camera feed from the system (Admin only)."""
    camera = await session.get(Camera, camera_id)
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")

    await session.delete(camera)
    await session.commit()
    return {"message": f"Camera '{camera.name}' deleted successfully"}