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


@router.get("/comparison", summary="Side-by-Side Research Comparison")
async def get_experiments_comparison(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Returns side-by-side benchmark comparison metrics across all experiments (EXP-A through EXP-E).
    Calculates improvements over baseline for academic presentation and thesis defense.
    """
    statement = select(Experiment)
    exp_results = await session.execute(statement)
    experiments = exp_results.scalars().all()

    comparison_data = []
    baseline_f1 = None
    baseline_rec = None

    for exp in experiments:
        m_stmt = select(ExperimentMetrics).where(ExperimentMetrics.experiment_id == exp.id)
        m_res = await session.execute(m_stmt)
        metric = m_res.scalars().first()

        cm = []
        if metric and metric.confusion_matrix_json:
            try:
                cm = json.loads(metric.confusion_matrix_json)
            except Exception:
                cm = []

        item = {
            "id": exp.id,
            "name": exp.name,
            "model_type": exp.model_type,
            "status": exp.status,
            "precision": metric.precision if metric else 0.0,
            "recall": metric.recall if metric else 0.0,
            "f1_score": metric.f1_score if metric else 0.0,
            "drowning_precision": metric.precision_drowning if metric else 0.0,
            "drowning_recall": metric.recall_drowning if metric else 0.0,
            "drowning_f1": metric.f1_drowning if metric else 0.0,
            "avg_fps": metric.avg_fps if metric else 0.0,
            "avg_inference_latency_ms": metric.avg_inference_latency_ms if metric else 0.0,
            "avg_alert_latency_ms": metric.avg_alert_latency_ms if metric else 0.0,
            "false_positive_rate": metric.false_positive_rate if metric else 0.0,
            "false_negative_rate": metric.false_negative_rate if metric else 0.0,
            "confusion_matrix": cm,
        }

        if "EXP-A" in exp.name and metric:
            baseline_f1 = metric.f1_score
            baseline_rec = metric.recall

        comparison_data.append(item)

    # Compute improvements relative to EXP-A baseline
    for item in comparison_data:
        f1 = item["f1_score"]
        rec = item["recall"]
        item["improvement_f1_pct"] = round(((f1 - baseline_f1) / max(0.01, baseline_f1)) * 100.0, 1) if baseline_f1 else 0.0
        item["improvement_recall_pct"] = round(((rec - baseline_rec) / max(0.01, baseline_rec)) * 100.0, 1) if baseline_rec else 0.0

    return comparison_data


@router.post("/run-all", summary="Execute Automated Research Benchmark Suite")
async def run_benchmark_suite(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(["admin", "researcher"])),
):
    """
    Executes all 5 empirical experiments (EXP-A through EXP-E) on the evaluation dataset,
    re-computes all metrics, updates database records, and outputs comparison reports.
    """
    from ai.evaluation.benchmark_suite import BenchmarkSuite

    suite = BenchmarkSuite()
    results = suite.run_all()

    exp_id_map = {
        "exp_a": 1,
        "exp_b": 2,
        "exp_c": 3,
        "exp_d": 4,
        "exp_e": 5,
    }

    now = datetime.now(timezone.utc)

    for key, res in results.items():
        exp_id = exp_id_map.get(key)
        if not exp_id:
            continue

        exp = await session.get(Experiment, exp_id)
        if exp:
            exp.status = ExperimentStatus.COMPLETED
            exp.completed_at = now
            session.add(exp)

        m_stmt = select(ExperimentMetrics).where(ExperimentMetrics.experiment_id == exp_id)
        m_res = await session.execute(m_stmt)
        metric = m_res.scalars().first()

        cm_json = json.dumps(res.get("confusion_matrix", []))

        if not metric:
            metric = ExperimentMetrics(experiment_id=exp_id)

        metric.precision = res["precision"]
        metric.recall = res["recall"]
        metric.f1_score = res["f1_score"]
        metric.precision_normal = res["precision_normal"]
        metric.precision_distress = res["precision_distress"]
        metric.precision_drowning = res["precision_drowning"]
        metric.recall_normal = res["recall_normal"]
        metric.recall_distress = res["recall_distress"]
        metric.recall_drowning = res["recall_drowning"]
        metric.f1_normal = res["f1_normal"]
        metric.f1_distress = res["f1_distress"]
        metric.f1_drowning = res["f1_drowning"]
        metric.false_positive_rate = res["false_positive_rate"]
        metric.false_negative_rate = res["false_negative_rate"]
        metric.avg_fps = res["avg_fps"]
        metric.avg_inference_latency_ms = res["avg_inference_latency_ms"]
        metric.avg_alert_latency_ms = res["avg_alert_latency_sec"] * 1000.0
        metric.id_switches = res["id_switches"]
        metric.confusion_matrix_json = cm_json
        metric.computed_at = now
        session.add(metric)

    await session.commit()
    return {"status": "success", "message": "All 5 benchmark experiments executed and synced successfully", "results": results}


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

