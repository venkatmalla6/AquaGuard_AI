"""
AquaGuard AI - Alert Management Endpoints
Incident triage, live alert feeds, operator acknowledgment, and resolution.
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc

from app.api.deps.auth import get_current_user
from app.database.db import get_session
from app.models.models import Alert, AlertSeverity, AlertStatus, BehaviorClass, User

router = APIRouter()


class AlertCreate(BaseModel):
    track_id: int
    camera_id: Optional[int] = None
    experiment_id: Optional[int] = None
    severity: AlertSeverity = AlertSeverity.CRITICAL
    behavior: BehaviorClass = BehaviorClass.POTENTIAL_DROWNING
    confidence: float
    consecutive_frames: int = 8
    alert_latency_ms: Optional[float] = 120.0
    frame_snapshot_path: Optional[str] = None
    notes: Optional[str] = None


class AlertActionRequest(BaseModel):
    notes: Optional[str] = None


@router.get("", response_model=List[Alert], summary="List Alerts")
async def list_alerts(
    status: Optional[AlertStatus] = None,
    severity: Optional[AlertSeverity] = None,
    camera_id: Optional[int] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve incident alerts sorted by triggered timestamp descending.
    Allows filtering by status (active, acknowledged, resolved, false_alarm) and severity.
    """
    statement = select(Alert).order_by(desc(Alert.triggered_at)).offset(offset).limit(limit)
    if status is not None:
        statement = statement.where(Alert.status == status)
    if severity is not None:
        statement = statement.where(Alert.severity == severity)
    if camera_id is not None:
        statement = statement.where(Alert.camera_id == camera_id)

    result = await session.execute(statement)
    return result.scalars().all()


@router.get("/{alert_id}", response_model=Alert, summary="Get Alert Details")
async def get_alert(
    alert_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Fetch specific alert incident record by ID."""
    alert = await session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return alert


@router.post("", response_model=Alert, status_code=status.HTTP_201_CREATED, summary="Create Alert")
async def create_alert(
    alert_in: AlertCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Record an alert triggered by the AI Alert Engine or testing harness."""
    alert = Alert(
        track_id=alert_in.track_id,
        camera_id=alert_in.camera_id,
        experiment_id=alert_in.experiment_id,
        severity=alert_in.severity,
        status=AlertStatus.ACTIVE,
        behavior=alert_in.behavior,
        confidence=alert_in.confidence,
        consecutive_frames=alert_in.consecutive_frames,
        alert_latency_ms=alert_in.alert_latency_ms,
        frame_snapshot_path=alert_in.frame_snapshot_path,
        notes=alert_in.notes,
        triggered_at=datetime.now(timezone.utc),
    )
    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return alert


@router.post("/{alert_id}/acknowledge", response_model=Alert, summary="Acknowledge Alert")
async def acknowledge_alert(
    alert_id: int,
    action: Optional[AlertActionRequest] = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Mark an active alert as acknowledged by the on-duty lifeguard or operator."""
    alert = await session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_at = datetime.now(timezone.utc)
    alert.acknowledged_by = current_user.id
    if action and action.notes:
        alert.notes = f"{alert.notes or ''}\n[Ack]: {action.notes}".strip()

    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return alert


@router.post("/{alert_id}/resolve", response_model=Alert, summary="Resolve Alert")
async def resolve_alert(
    alert_id: int,
    action: Optional[AlertActionRequest] = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Mark an alert incident as resolved after swimmer safety is assured."""
    alert = await session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    alert.status = AlertStatus.RESOLVED
    alert.resolved_at = datetime.now(timezone.utc)
    if action and action.notes:
        alert.notes = f"{alert.notes or ''}\n[Resolved]: {action.notes}".strip()

    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return alert


@router.post("/{alert_id}/false-alarm", response_model=Alert, summary="Mark False Alarm")
async def mark_false_alarm(
    alert_id: int,
    action: Optional[AlertActionRequest] = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Classify an alert as a False Positive for research metrics calculation."""
    alert = await session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    alert.status = AlertStatus.FALSE_ALARM
    alert.resolved_at = datetime.now(timezone.utc)
    if action and action.notes:
        alert.notes = f"{alert.notes or ''}\n[False Alarm]: {action.notes}".strip()

    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return alert