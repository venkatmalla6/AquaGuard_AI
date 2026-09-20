"""
AquaGuard AI - Video Ingestion & Processing API Endpoints
Handles video file uploads, metadata extraction, background processing,
live progress tracking, and processed stream playback.
"""
from datetime import datetime, timezone
from pathlib import Path
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc
from loguru import logger

from app.api.deps.auth import get_current_user, require_role
from app.core.config import settings
from app.database.db import get_session, AsyncSessionLocal
from app.models.models import Video, VideoStatus, User
from ai.pipeline.video_processor import extract_video_metadata, VideoProcessor

router = APIRouter()

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}


class VideoResponse(BaseModel):
    id: int
    video_uid: str
    filename: str
    original_filename: str
    file_size_bytes: int
    duration_seconds: Optional[float] = None
    fps: Optional[float] = None
    total_frames: Optional[int] = None
    processed_frames: int = 0
    progress_percent: float = 0.0
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None
    status: VideoStatus
    error_message: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


def format_video_response(v: Video) -> VideoResponse:
    pct = 0.0
    if v.total_frames and v.total_frames > 0:
        pct = min(100.0, round((v.processed_frames / v.total_frames) * 100, 1))
    if v.status == VideoStatus.COMPLETED:
        pct = 100.0

    return VideoResponse(
        id=v.id,
        video_uid=v.video_uid,
        filename=v.filename,
        original_filename=v.original_filename,
        file_size_bytes=v.file_size_bytes,
        duration_seconds=v.duration_seconds,
        fps=v.fps,
        total_frames=v.total_frames,
        processed_frames=v.processed_frames,
        progress_percent=pct,
        resolution_width=v.resolution_width,
        resolution_height=v.resolution_height,
        status=v.status,
        error_message=v.error_message,
        uploaded_at=v.uploaded_at,
        processed_at=v.processed_at,
    )


async def _async_update_progress(video_id: int, current_frame: int, total_frames: int):
    """Updates the processed frame count in the database during inference."""
    try:
        async with AsyncSessionLocal() as session:
            v = await session.get(Video, video_id)
            if v:
                v.processed_frames = current_frame
                session.add(v)
                await session.commit()
    except Exception as e:
        logger.warning(f"Failed to update progress for video {video_id}: {e}")


def process_video_background_task(video_id: int, input_path: str, output_path: str):
    """
    Background worker that runs the computer vision detection & tracking
    pipeline on the uploaded video file.
    """
    import asyncio

    async def _run():
        logger.info(f"Starting background processing for video ID {video_id}")
        # Mark PROCESSING
        async with AsyncSessionLocal() as session:
            v = await session.get(Video, video_id)
            if not v:
                return
            v.status = VideoStatus.PROCESSING
            session.add(v)
            await session.commit()

        loop = asyncio.get_running_loop()

        def progress_cb(current, total, pct):
            # Schedule DB progress update
            asyncio.run_coroutine_threadsafe(
                _async_update_progress(video_id, current, total),
                loop,
            )

        processor = VideoProcessor()

        try:
            # Run heavy CPU OpenCV processing
            stats = await loop.run_in_executor(
                None,
                processor.process_file,
                input_path,
                output_path,
                progress_cb,
            )

            # Mark COMPLETED
            async with AsyncSessionLocal() as session:
                v = await session.get(Video, video_id)
                if v:
                    v.status = VideoStatus.COMPLETED
                    v.processed_filepath = output_path
                    v.processed_frames = stats.get("total_frames_processed", v.total_frames)
                    v.processed_at = datetime.now(timezone.utc)
                    session.add(v)
                    await session.commit()
            logger.info(f"Video ID {video_id} processing completed successfully: {stats}")

        except Exception as err:
            logger.error(f"Video ID {video_id} processing failed: {err}")
            async with AsyncSessionLocal() as session:
                v = await session.get(Video, video_id)
                if v:
                    v.status = VideoStatus.FAILED
                    v.error_message = str(err)
                    session.add(v)
                    await session.commit()

    asyncio.run(_run())


@router.post("/upload", response_model=VideoResponse, status_code=status.HTTP_201_CREATED, summary="Upload Video")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    auto_process: bool = Query(default=False, description="Automatically trigger AI processing upon upload"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a video file (.mp4, .avi, .mov, .mkv) for drowning detection analysis.
    Extracts metadata (resolution, fps, frame count) and stages for inference.
    """
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported video format '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Prepare storage paths
    upload_dir = Path(settings.UPLOAD_DIR) / "videos"
    processed_dir = Path(settings.UPLOAD_DIR) / "processed"
    upload_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    unique_id = uuid.uuid4().hex[:12]
    safe_filename = f"{unique_id}_{file.filename}"
    file_path = upload_dir / safe_filename
    output_filename = f"annotated_{unique_id}.mp4"
    processed_path = processed_dir / output_filename

    # Save uploaded file to disk
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {e}")
    finally:
        file.file.close()

    file_size = file_path.stat().st_size

    # Extract metadata using OpenCV
    try:
        meta = extract_video_metadata(str(file_path))
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Corrupted or invalid video file: {e}")

    # Record in database
    video_record = Video(
        filename=safe_filename,
        original_filename=file.filename,
        filepath=str(file_path),
        file_size_bytes=file_size,
        duration_seconds=meta.duration_seconds,
        fps=meta.fps,
        total_frames=meta.total_frames,
        processed_frames=0,
        resolution_width=meta.resolution_width,
        resolution_height=meta.resolution_height,
        status=VideoStatus.UPLOADED,
        uploaded_at=datetime.now(timezone.utc),
        uploaded_by=current_user.id,
    )
    session.add(video_record)
    await session.commit()
    await session.refresh(video_record)

    if auto_process:
        background_tasks.add_task(
            process_video_background_task,
            video_record.id,
            str(file_path),
            str(processed_path),
        )

    return format_video_response(video_record)


@router.get("", response_model=List[VideoResponse], summary="List Uploaded Videos")
async def list_videos(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List all uploaded videos sorted by upload date descending."""
    statement = select(Video).order_by(desc(Video.uploaded_at))
    result = await session.execute(statement)
    videos = result.scalars().all()
    return [format_video_response(v) for v in videos]


@router.get("/{video_id}", response_model=VideoResponse, summary="Get Video Details & Progress")
async def get_video(
    video_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Fetch video metadata and real-time processing progress percentage."""
    video = await session.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return format_video_response(video)


@router.post("/{video_id}/process", response_model=VideoResponse, summary="Trigger Video Processing")
async def process_video(
    video_id: int,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(["admin", "operator", "researcher"])),
):
    """Launch asynchronous AI detection and tracking analysis on an uploaded video."""
    video = await session.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    if video.status == VideoStatus.PROCESSING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Video is already being processed")

    processed_dir = Path(settings.UPLOAD_DIR) / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    unique_id = uuid.uuid4().hex[:8]
    output_path = processed_dir / f"annotated_{video.id}_{unique_id}.mp4"

    video.status = VideoStatus.PROCESSING
    video.error_message = None
    session.add(video)
    await session.commit()
    await session.refresh(video)

    background_tasks.add_task(
        process_video_background_task,
        video.id,
        video.filepath,
        str(output_path),
    )

    return format_video_response(video)


@router.get("/{video_id}/stream", summary="Stream Raw or Processed Video")
async def stream_video(
    video_id: int,
    processed: bool = Query(default=True, description="Stream processed video if available, else raw"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Stream video file for HTML5 video player playback."""
    video = await session.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    target_path = video.processed_filepath if (processed and video.processed_filepath) else video.filepath
    path = Path(target_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file not found on disk")

    return FileResponse(path=str(path), media_type="video/mp4", filename=path.name)


@router.delete("/{video_id}", summary="Delete Video")
async def delete_video(
    video_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(["admin", "operator"])),
):
    """Delete video records and remove stored video files from disk."""
    video = await session.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    # Remove files
    if video.filepath and Path(video.filepath).exists():
        Path(video.filepath).unlink(missing_ok=True)
    if video.processed_filepath and Path(video.processed_filepath).exists():
        Path(video.processed_filepath).unlink(missing_ok=True)

    await session.delete(video)
    await session.commit()
    return {"message": f"Video '{video.original_filename}' deleted successfully"}