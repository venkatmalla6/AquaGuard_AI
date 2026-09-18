from datetime import datetime, timezone
import json
from loguru import logger
from sqlmodel import select

from app.database.db import AsyncSessionLocal
from app.models.models import User, Camera, CameraStatus, Experiment, ExperimentStatus, ModelType
from app.api.deps.auth import get_password_hash

async def seed_initial_data():
    async with AsyncSessionLocal() as session:
        # 1. Seed Users
        r = await session.execute(select(User))
        if not r.scalars().first():
            logger.info('Seeding default demo users...')
            session.add_all([
                User(email='admin@aquaguard.ai', hashed_password=get_password_hash('admin123'), full_name='System Administrator', role='admin', is_active=True, created_at=datetime.now(timezone.utc)),
                User(email='operator@aquaguard.ai', hashed_password=get_password_hash('operator123'), full_name='Head Lifeguard (Operator)', role='operator', is_active=True, created_at=datetime.now(timezone.utc)),
                User(email='researcher@aquaguard.ai', hashed_password=get_password_hash('research123'), full_name='AI Research Engineer', role='researcher', is_active=True, created_at=datetime.now(timezone.utc)),
            ])
            await session.commit()
            logger.info('Demo users seeded.')

        # 2. Seed Cameras
        r = await session.execute(select(Camera))
        if not r.scalars().first():
            logger.info('Seeding default cameras...')
            session.add_all([
                Camera(name='Main Competition Pool (CCTV-01)', location='North Olympic Basin', stream_url='0', status=CameraStatus.ONLINE, is_active=True, resolution_width=1280, resolution_height=720, fps=30.0, created_at=datetime.now(timezone.utc), last_seen=datetime.now(timezone.utc)),
                Camera(name='Diving Well & Deep End (CCTV-02)', location='South Deep Zone', stream_url='sample_diving.mp4', status=CameraStatus.ONLINE, is_active=True, resolution_width=1280, resolution_height=720, fps=30.0, created_at=datetime.now(timezone.utc), last_seen=datetime.now(timezone.utc)),
            ])
            await session.commit()
            logger.info('Default cameras seeded.')

        # 3. Seed Experiments
        r = await session.execute(select(Experiment))
        if not r.scalars().first():
            logger.info('Seeding research experiments...')
            session.add_all([
                Experiment(name='EXP-A: Baseline Spatial YOLOv8n', description='Standard frame-by-frame object detection baseline', model_type=ModelType.YOLO_BASELINE, detector_config=json.dumps({'model': 'yolov8n.pt', 'conf': 0.35, 'iou': 0.45}), status=ExperimentStatus.PENDING, created_at=datetime.now(timezone.utc)),
                Experiment(name='EXP-B: YOLOv8n + ByteTrack Heuristics', description='Spatial detection with ByteTrack tracking and rules', model_type=ModelType.YOLO_TRACKING, detector_config=json.dumps({'model': 'yolov8n.pt', 'conf': 0.35}), tracker_config=json.dumps({'tracker': 'bytetrack', 'track_thresh': 0.45}), status=ExperimentStatus.PENDING, created_at=datetime.now(timezone.utc)),
                Experiment(name='EXP-C: Proposed YOLOv8n + ByteTrack + Bi-LSTM', description='Full proposed architecture with 16-D temporal features and Bi-LSTM', model_type=ModelType.YOLO_TRACKING_LSTM, detector_config=json.dumps({'model': 'yolov8n.pt', 'conf': 0.35}), tracker_config=json.dumps({'tracker': 'bytetrack'}), temporal_config=json.dumps({'model': 'lstm', 'window_size': 30, 'hidden_dim': 64}), status=ExperimentStatus.PENDING, created_at=datetime.now(timezone.utc)),
                Experiment(name='EXP-D: Ablation Study (GRU Sequence Model)', description='Ablation using GRU instead of Bi-LSTM', model_type=ModelType.YOLO_TRACKING_GRU, detector_config=json.dumps({'model': 'yolov8n.pt', 'conf': 0.35}), tracker_config=json.dumps({'tracker': 'bytetrack'}), temporal_config=json.dumps({'model': 'gru', 'window_size': 30, 'hidden_dim': 64}), status=ExperimentStatus.PENDING, created_at=datetime.now(timezone.utc)),
                Experiment(name='EXP-E: Temporal Window Size Ablation', description='Window size sensitivity analysis (T=15, 30, 60)', model_type=ModelType.YOLO_TRACKING_LSTM, detector_config=json.dumps({'model': 'yolov8n.pt', 'conf': 0.35}), tracker_config=json.dumps({'tracker': 'bytetrack'}), temporal_config=json.dumps({'model': 'lstm', 'window_sizes': [15, 30, 60]}), status=ExperimentStatus.PENDING, created_at=datetime.now(timezone.utc)),
            ])
            await session.commit()
            logger.info('Research experiments seeded.')
