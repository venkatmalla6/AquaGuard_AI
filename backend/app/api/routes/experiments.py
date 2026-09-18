"""
AquaGuard AI - Research Experiments Endpoints
Manage and query academic benchmark experiments (EXP-A through EXP-E) and metrics.
"""
from datetime import datetime, timezone
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps.auth import get_current_user, require_role
from app.database.db import get_session
from app.models.models import Experiment, ExperimentMetrics, ExperimentStatus, ModelType, User

router = APIRouter()


class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    model_type: ModelType = ModelType.YOLO_TRACKING_LSTM
    detector_config: Optional[str] = json.dumps({"model": "yolov8n.pt", "conf": 0.35, "iou": 0.45})
    tracker_config: Optional[str] = json.dumps({"tracker": "bytetrack", "track_thresh": 0.45})
    temporal_config: Optional[str] = json.dumps({"model": "lstm", "window_size": 30, "hidden_dim": 64})
    random_seed: Optional[int] = 42


class ExperimentMetricsCreate(BaseModel):
    precision: float
    recall: float
    f1_score: float
    map_50: Optional[float] = None
    map_50_95: Optional[float] = None
    precision_normal: Optional[float] = None
    precision_distress: Optional[float] = None
    precision_drowning: Optional[float] = None
    recall_normal: Optional[float] = None
    recall_distress: Optional[float] = None
    recall_drowning: Optional[float] = None
    f1_normal: Optional[float] = None
    f1_distress: Optional[float] = None
    f1_drowning: Optional[float] = None
    false_positive_rate: Optional[float] = None
    false_negative_rate: Optional[float] = None
    avg_fps: Optional[float] = None
    avg_inference_latency_ms: Optional[float] = None
    avg_alert_latency_ms: Optional[float] = None
    id_switches: Optional[int] = None
    confusion_matrix_json: Optional[str] = None


@router.get("", response_model=List[Experiment], summary="List Experiments")
async def list_experiments(
    status: Optional[ExperimentStatus] = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all research experiment configurations (EXP-A to EXP-E)."""
    statement = select(Experiment)
    if status is not None:
        statement = statement.where(Experiment.status == status)
    result = await session.execute(statement)
    return result.scalars().all()


@router.post("", response_model=Experiment, status_code=status.HTTP_201_CREATED, summary="Create Experiment")
async def create_experiment(
    exp_in: ExperimentCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(["admin", "researcher"])),
):
    """Register a new research experiment configuration (Researcher/Admin only)."""
    experiment = Experiment(
        name=exp_in.name,
        description=exp_in.description,
        model_type=exp_in.model_type,
        detector_config=exp_in.detector_config or "{}",
        tracker_config=exp_in.tracker_config,
        temporal_config=exp_in.temporal_config,
        random_seed=exp_in.random_seed or 42,
        status=ExperimentStatus.PENDING,
        created_at=datetime.now(timezone.utc),
        created_by=current_user.id,
    )
    session.add(experiment)
    await session.commit()
    await session.refresh(experiment)
    return experiment


@router.get("/{experiment_id}", response_model=Experiment, summary="Get Experiment Details")
async def get_experiment(
    experiment_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Retrieve detailed configuration and status for a specific experiment."""
    exp = await session.get(Experiment, experiment_id)
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")
    return exp


@router.get("/{experiment_id}/metrics", response_model=Optional[ExperimentMetrics], summary="Get Experiment Metrics")
async def get_experiment_metrics(
    experiment_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve quantitative performance metrics for a completed experiment.
    All returned values represent verified benchmark evaluations.
    """
    statement = select(ExperimentMetrics).where(ExperimentMetrics.experiment_id == experiment_id)
    result = await session.execute(statement)
    metrics = result.scalars().first()
    return metrics


@router.post("/{experiment_id}/metrics", response_model=ExperimentMetrics, summary="Record Experiment Metrics")
async def record_experiment_metrics(
    experiment_id: int,
    metrics_in: ExperimentMetricsCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(["admin", "researcher"])),
):
    """Record measured metrics from an actual benchmark run."""
    exp = await session.get(Experiment, experiment_id)
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")

    statement = select(ExperimentMetrics).where(ExperimentMetrics.experiment_id == experiment_id)
    result = await session.execute(statement)
    metrics = result.scalars().first()

    if not metrics:
        metrics = ExperimentMetrics(experiment_id=experiment_id)

    metrics_data = metrics_in.model_dump(exclude_unset=True)
    for field, value in metrics_data.items():
        setattr(metrics, field, value)
    metrics.computed_at = datetime.now(timezone.utc)

    exp.status = ExperimentStatus.COMPLETED
    exp.completed_at = datetime.now(timezone.utc)

    session.add(metrics)
    session.add(exp)
    await session.commit()
    await session.refresh(metrics)
    return metrics