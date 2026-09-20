"""
AquaGuard AI - Database Models (SQLModel)

WHY one file initially: Keeps the model graph visible in one place during development.
Split into separate files per feature area when the codebase grows.

DESIGN PRINCIPLE: These models define the actual database schema.
Changes here require a database migration (Alembic) in production.
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
import uuid


# ============================================================
# Enumerations
# ============================================================

class BehaviorClass(str, Enum):
    """
    The three behavior classes used throughout the system.
    These definitions must match exactly with training annotations.
    """
    NORMAL = "normal"
    DISTRESS = "distress"
    POTENTIAL_DROWNING = "potential_drowning"


class AlertSeverity(str, Enum):
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    FALSE_ALARM = "false_alarm"


class CameraStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


class ModelType(str, Enum):
    YOLO_BASELINE = "yolo_baseline"
    YOLO_TRACKING = "yolo_tracking"
    YOLO_TRACKING_LSTM = "yolo_tracking_lstm"
    YOLO_TRACKING_GRU = "yolo_tracking_gru"
    YOLO_TRACKING_TRANSFORMER = "yolo_tracking_transformer"


class ExperimentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================
# User
# ============================================================

class User(SQLModel, table=True):
    """System users (operators, researchers, admins)."""
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str
    role: str = Field(default="operator")  # operator | researcher | admin
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None


# ============================================================
# Camera
# ============================================================

class Camera(SQLModel, table=True):
    """Physical or virtual cameras connected to the system."""
    __tablename__ = "cameras"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    location: str
    stream_url: str  # RTSP, webcam index, or video file path
    status: CameraStatus = Field(default=CameraStatus.OFFLINE)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: Optional[datetime] = None
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None
    fps: Optional[float] = None
    notes: Optional[str] = None


# ============================================================
# Detection
# ============================================================

class Detection(SQLModel, table=True):
    """
    A single person detection result from one video frame.
    Represents the output of the YOLO detector.
    """
    __tablename__ = "detections"

    id: Optional[int] = Field(default=None, primary_key=True)
    camera_id: Optional[int] = Field(default=None, foreign_key="cameras.id")
    experiment_id: Optional[int] = Field(default=None, foreign_key="experiments.id")
    frame_number: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # YOLO detection output
    bbox_x1: float
    bbox_y1: float
    bbox_x2: float
    bbox_y2: float
    confidence: float
    class_id: int = Field(default=0)  # 0 = person

    # Frame dimensions for normalization
    frame_width: int
    frame_height: int


# ============================================================
# Tracked Person
# ============================================================

class TrackedPerson(SQLModel, table=True):
    """
    A tracked individual across multiple frames.
    Represents a continuous track assigned by ByteTrack.
    """
    __tablename__ = "tracked_persons"

    id: Optional[int] = Field(default=None, primary_key=True)
    track_id: int = Field(index=True)  # ByteTrack-assigned ID
    camera_id: Optional[int] = Field(default=None, foreign_key="cameras.id")
    experiment_id: Optional[int] = Field(default=None, foreign_key="experiments.id")

    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    total_frames: int = Field(default=0)
    is_active: bool = Field(default=True)

    # Latest position
    last_cx: Optional[float] = None
    last_cy: Optional[float] = None

    # Current behavior classification
    current_behavior: BehaviorClass = Field(default=BehaviorClass.NORMAL)
    behavior_confidence: Optional[float] = None


# ============================================================
# Behavior Event
# ============================================================

class BehaviorEvent(SQLModel, table=True):
    """
    A classified behavior state for a tracked person at a specific time.
    This is the output of the temporal model.
    """
    __tablename__ = "behavior_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    track_id: int = Field(index=True)
    camera_id: Optional[int] = Field(default=None, foreign_key="cameras.id")
    experiment_id: Optional[int] = Field(default=None, foreign_key="experiments.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    frame_number: int

    # Classification output
    behavior: BehaviorClass
    confidence_normal: float
    confidence_distress: float
    confidence_drowning: float

    # Sequence used
    sequence_length: int
    model_used: str  # lstm | gru | transformer


# ============================================================
# Alert
# ============================================================

class Alert(SQLModel, table=True):
    """
    An alert generated by the alert engine when drowning/distress is detected.
    """
    __tablename__ = "alerts"

    id: Optional[int] = Field(default=None, primary_key=True)
    alert_uid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True)
    track_id: int
    camera_id: Optional[int] = Field(default=None, foreign_key="cameras.id")
    experiment_id: Optional[int] = Field(default=None, foreign_key="experiments.id")

    severity: AlertSeverity
    status: AlertStatus = Field(default=AlertStatus.ACTIVE)
    behavior: BehaviorClass
    confidence: float

    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = Field(default=None, foreign_key="users.id")

    # Alert details
    consecutive_frames: int = Field(default=0)
    alert_latency_ms: Optional[float] = None  # Time from event to alert
    frame_snapshot_path: Optional[str] = None  # Path to saved snapshot
    notes: Optional[str] = None


# ============================================================
# Incident
# ============================================================

class Incident(SQLModel, table=True):
    """
    A complete incident record grouping related alerts for one event.
    Prevents duplicate alerts for the same drowning event.
    """
    __tablename__ = "incidents"

    id: Optional[int] = Field(default=None, primary_key=True)
    incident_uid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True)
    track_id: int
    camera_id: Optional[int] = Field(default=None, foreign_key="cameras.id")

    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    peak_severity: AlertSeverity = Field(default=AlertSeverity.WARNING)
    status: AlertStatus = Field(default=AlertStatus.ACTIVE)

    timeline_json: Optional[str] = None  # JSON string of behavior timeline
    video_clip_path: Optional[str] = None


# ============================================================
# Experiment
# ============================================================

class Experiment(SQLModel, table=True):
    """
    An experiment configuration record.
    Stores all parameters needed to reproduce an experiment run.
    
    WHY: Research reproducibility requires that every run can be exactly
    recreated. Storing config + seed + hardware info satisfies this.
    """
    __tablename__ = "experiments"

    id: Optional[int] = Field(default=None, primary_key=True)
    experiment_uid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True)
    name: str
    description: Optional[str] = None

    # Configuration (stored as JSON strings)
    detector_config: str  # JSON
    tracker_config: Optional[str] = None  # JSON
    temporal_config: Optional[str] = None  # JSON
    augmentation_config: Optional[str] = None  # JSON

    model_type: ModelType
    dataset_id: Optional[int] = Field(default=None, foreign_key="datasets.id")

    # Reproducibility fields
    random_seed: int = Field(default=42)
    code_version: Optional[str] = None
    hardware_info: Optional[str] = None  # JSON
    software_env: Optional[str] = None  # JSON

    status: ExperimentStatus = Field(default=ExperimentStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    created_by: Optional[int] = Field(default=None, foreign_key="users.id")


# ============================================================
# Experiment Metrics
# ============================================================

class ExperimentMetrics(SQLModel, table=True):
    """
    Measured performance metrics for a completed experiment.
    
    IMPORTANT: These values must come from actual experiments.
    Never manually insert values here to make results look better.
    """
    __tablename__ = "experiment_metrics"

    id: Optional[int] = Field(default=None, primary_key=True)
    experiment_id: int = Field(foreign_key="experiments.id", unique=True)
    computed_at: datetime = Field(default_factory=datetime.utcnow)

    # Detection metrics
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    map_50: Optional[float] = None      # mAP@0.5
    map_50_95: Optional[float] = None   # mAP@0.5:0.95

    # Classification per-class
    precision_normal: Optional[float] = None
    precision_distress: Optional[float] = None
    precision_drowning: Optional[float] = None
    recall_normal: Optional[float] = None
    recall_distress: Optional[float] = None
    recall_drowning: Optional[float] = None
    f1_normal: Optional[float] = None
    f1_distress: Optional[float] = None
    f1_drowning: Optional[float] = None

    # Error rates
    false_positive_rate: Optional[float] = None
    false_negative_rate: Optional[float] = None

    # Performance
    avg_fps: Optional[float] = None
    avg_inference_latency_ms: Optional[float] = None
    avg_alert_latency_ms: Optional[float] = None

    # Tracking (optional)
    id_switches: Optional[int] = None

    # Confusion matrix (stored as JSON)
    confusion_matrix_json: Optional[str] = None

    # Path to saved figures
    figures_dir: Optional[str] = None


# ============================================================
# AI Model Registry
# ============================================================

class AIModel(SQLModel, table=True):
    """Registry of trained AI models."""
    __tablename__ = "models"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    version: str
    architecture: ModelType
    description: Optional[str] = None

    training_date: Optional[datetime] = None
    dataset_id: Optional[int] = Field(default=None, foreign_key="datasets.id")
    experiment_id: Optional[int] = Field(default=None, foreign_key="experiments.id")

    # File paths
    weights_path: Optional[str] = None
    config_path: Optional[str] = None

    # Params
    parameters_count: Optional[int] = None
    input_size: Optional[str] = None

    is_active: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# Dataset
# ============================================================

class Dataset(SQLModel, table=True):
    """Dataset registry for reproducible experiments."""
    __tablename__ = "datasets"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    version: str
    description: Optional[str] = None
    source: Optional[str] = None  # URL or reference

    # Split info
    total_videos: Optional[int] = None
    total_frames: Optional[int] = None
    train_videos: Optional[int] = None
    val_videos: Optional[int] = None
    test_videos: Optional[int] = None

    # Class distribution (JSON)
    class_distribution_json: Optional[str] = None

    split_strategy: str = Field(default="video_level")  # video_level | frame_level
    annotation_format: Optional[str] = None
    data_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# System Log
# ============================================================

class SystemLog(SQLModel, table=True):
    """Structured system event log."""
    __tablename__ = "system_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str  # DEBUG | INFO | WARNING | ERROR | CRITICAL
    component: str  # detector | tracker | temporal | alert | api | system
    message: str
    details: Optional[str] = None  # JSON
    camera_id: Optional[int] = None
    experiment_id: Optional[int] = None


# ============================================================
# IoT Device
# ============================================================

class IoTDevice(SQLModel, table=True):
    """ESP32 or other IoT alert hardware."""
    __tablename__ = "iot_devices"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    device_type: str  # esp32 | raspberry_pi | simulation
    location: Optional[str] = None
    mqtt_topic: Optional[str] = None
    is_simulation: bool = Field(default=True)

    status: str = Field(default="offline")  # online | offline | error
    last_seen: Optional[datetime] = None

    # Current state
    siren_active: bool = Field(default=False)
    led_active: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ============================================================
# Video
# ============================================================

class VideoStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Video(SQLModel, table=True):
    """Uploaded pool surveillance footage and benchmark test videos."""
    __tablename__ = "videos"

    id: Optional[int] = Field(default=None, primary_key=True)
    video_uid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True)
    filename: str
    original_filename: str
    filepath: str
    processed_filepath: Optional[str] = None
    file_size_bytes: int
    duration_seconds: Optional[float] = None
    fps: Optional[float] = None
    total_frames: Optional[int] = None
    processed_frames: int = Field(default=0)
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None
    status: VideoStatus = Field(default=VideoStatus.UPLOADED)
    error_message: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    uploaded_by: Optional[int] = Field(default=None, foreign_key="users.id")