import pathlib, os

base = pathlib.Path(r'D:\Btech\PROJECTS\AquaGuard_AI')

files = {}

# Alert Engine
files['ai/tracking/tracker.py'] = '''# AquaGuard AI - Person Tracker (ByteTrack wrapper)
# Phase 5 - Uses Ultralytics built-in ByteTrack via YOLO track mode

from typing import List, Dict, Optional
import numpy as np
from loguru import logger


class TrackResult:
    def __init__(self, track_id, bbox_x1, bbox_y1, bbox_x2, bbox_y2, confidence):
        self.track_id = track_id
        self.bbox_x1 = bbox_x1
        self.bbox_y1 = bbox_y1
        self.bbox_x2 = bbox_x2
        self.bbox_y2 = bbox_y2
        self.confidence = confidence

    @property
    def center_x(self): return (self.bbox_x1 + self.bbox_x2) / 2
    @property
    def center_y(self): return (self.bbox_y1 + self.bbox_y2) / 2
    @property
    def width(self): return self.bbox_x2 - self.bbox_x1
    @property
    def height(self): return self.bbox_y2 - self.bbox_y1

    def to_dict(self):
        return {
            "track_id": self.track_id,
            "bbox": [self.bbox_x1, self.bbox_y1, self.bbox_x2, self.bbox_y2],
            "center": [self.center_x, self.center_y],
            "confidence": self.confidence,
        }


class PersonTracker:
    """
    ByteTrack person tracker using Ultralytics built-in tracking.
    WHY ByteTrack: State-of-the-art MOT algorithm, fast, ID-consistent.
    WHY Ultralytics built-in: Avoids extra dependencies; well-maintained.
    ALTERNATIVES: BoT-SORT, DeepSORT, StrongSORT.
    """
    def __init__(self, model_path="yolov8n.pt", confidence=0.5, device="cpu"):
        self.model_path = model_path
        self.confidence = confidence
        self.device = device
        self.model = None
        self._is_loaded = False
        self._id_switch_count = 0

    def load(self):
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
            self.model.to(self.device)
            self._is_loaded = True
            logger.info(f"Tracker loaded: {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Tracker load failed: {e}")
            return False

    def track(self, frame, frame_number=0):
        if not self._is_loaded:
            return [], 0.0
        import time
        t0 = time.perf_counter()
        try:
            results = self.model.track(
                frame,
                persist=True,
                conf=self.confidence,
                classes=[0],
                tracker="bytetrack.yaml",
                verbose=False,
            )
            ms = (time.perf_counter() - t0) * 1000
            tracks = []
            if results and results[0].boxes is not None:
                boxes = results[0].boxes
                if boxes.id is not None:
                    for box, tid in zip(boxes, boxes.id):
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        tracks.append(TrackResult(
                            track_id=int(tid),
                            bbox_x1=x1, bbox_y1=y1,
                            bbox_x2=x2, bbox_y2=y2,
                            confidence=float(box.conf[0]),
                        ))
            return tracks, ms
        except Exception as e:
            logger.error(f"Track error frame {frame_number}: {e}")
            return [], 0.0
'''

# Alert Engine
files['ai/evaluation/alert_engine.py'] = '''# AquaGuard AI - Alert Engine
# Phase 8 - Converts behavior classifications into alerts with persistence filter

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import time
from loguru import logger


class AlertLevel(str, Enum):
    NONE = "none"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class AlertState:
    track_id: int
    current_level: AlertLevel = AlertLevel.NONE
    consecutive_count: int = 0
    last_alert_time: float = 0.0
    is_active: bool = False


class AlertEngine:
    """
    Converts temporal model classifications into deduplicated alerts.

    WHY consecutive_frames filter:
    A single frame mis-classification should not trigger an alert.
    Requiring N consecutive frames reduces false positives significantly.
    The optimal N is an experimental research parameter.

    WHY cooldown:
    Prevents alert flooding when a person stays in distress.
    One incident = one alert cluster.
    """
    def __init__(
        self,
        distress_confidence=0.6,
        drowning_confidence=0.8,
        consecutive_frames=5,
        cooldown_seconds=30,
    ):
        self.distress_confidence = distress_confidence
        self.drowning_confidence = drowning_confidence
        self.consecutive_frames = consecutive_frames
        self.cooldown_seconds = cooldown_seconds
        self._track_states: Dict[int, AlertState] = {}

    def process(self, track_id, behavior, confidence_normal,
                confidence_distress, confidence_drowning):
        if track_id not in self._track_states:
            self._track_states[track_id] = AlertState(track_id=track_id)

        state = self._track_states[track_id]
        now = time.time()

        # Determine classification
        if confidence_drowning >= self.drowning_confidence:
            level = AlertLevel.CRITICAL
        elif confidence_distress >= self.distress_confidence:
            level = AlertLevel.WARNING
        else:
            level = AlertLevel.NONE
            state.consecutive_count = 0
            return None

        state.consecutive_count += 1

        if state.consecutive_count < self.consecutive_frames:
            return None

        if now - state.last_alert_time < self.cooldown_seconds:
            return None

        state.last_alert_time = now
        state.current_level = level
        state.is_active = True

        alert = {
            "track_id": track_id,
            "level": level.value,
            "behavior": behavior,
            "confidence_drowning": confidence_drowning,
            "confidence_distress": confidence_distress,
            "consecutive_frames": state.consecutive_count,
            "timestamp": datetime.utcnow().isoformat(),
        }
        logger.warning(f"ALERT [{level.value.upper()}] Track {track_id} - {behavior}")
        return alert
'''

# README
files['README.md'] = """# AquaGuard AI

## Real-Time Drowning Detection Using Person Tracking and Temporal Behavior Analysis with Edge AI

**B.Tech CSE Final-Year Research Project**

---

## Research Objective

> "Can temporal behavior analysis combined with person tracking improve the
> reliability of real-time drowning detection compared with frame-level YOLO detection?"

---

## System Architecture

`
Camera/Video → YOLOv8 → ByteTrack → Feature Extraction → LSTM → Alert
`

---

## Technology Stack

- **Frontend**: React + Vite + TypeScript + Tailwind CSS + Recharts
- **Backend**: Python + FastAPI + SQLModel + WebSocket
- **AI**: YOLOv8 + ByteTrack + PyTorch LSTM/GRU
- **Database**: SQLite (dev) → PostgreSQL (production)

---

## Quick Start

### Backend

`ash
cd backend
pip install -r requirements.txt
python run.py
`

API docs: http://localhost:8000/docs

### Frontend

`ash
cd frontend
npm install
npm run dev
`

App: http://localhost:5173

---

## Research Experiments

| ID | Name | Detector | Tracker | Temporal |
|---|---|---|---|---|
| EXP-A | Baseline | YOLOv8 | None | None |
| EXP-B | +Tracking | YOLOv8 | ByteTrack | None |
| EXP-C | Proposed | YOLOv8 | ByteTrack | LSTM |

---

## Project Structure

`
AquaGuard_AI/
├── frontend/          React dashboard
├── backend/           FastAPI server
├── ai/                CV & AI modules
├── experiments/       Experiment configs & results
├── data/              Datasets
├── config/            Configuration files
├── docs/              Documentation
└── research/          Research outputs
`

---

## Important Research Notes

- **No fabricated results**: All metrics come from actual experiments.
- **Simulated scenarios**: No real drowning experiments performed.
- **Ethical use**: This prototype supplements, not replaces, lifeguards.

---

*AquaGuard AI © 2026 — B.Tech CSE Research Project*
"""

# Experiment configs
files['experiments/configs/exp_a_baseline.yaml'] = """# Experiment A - YOLOv8 Baseline
name: "EXP-A: YOLOv8 Baseline"
description: "Frame-level YOLO detection only. No tracking. No temporal model."
detector:
  model: yolov8n.pt
  confidence: 0.5
  iou: 0.45
tracker: null
temporal: null
random_seed: 42
status: pending
"""

files['experiments/configs/exp_c_proposed.yaml'] = """# Experiment C - Proposed System (LSTM)
name: "EXP-C: YOLOv8 + ByteTrack + LSTM (Proposed)"
description: "Proposed system: YOLO detection + ByteTrack + LSTM temporal analysis."
detector:
  model: yolov8n.pt
  confidence: 0.5
  iou: 0.45
tracker:
  algorithm: bytetrack
temporal:
  model: lstm
  sequence_length: 32
  hidden_size: 128
  num_layers: 2
  dropout: 0.3
random_seed: 42
status: pending
"""

files['docs/research/RESEARCH_GAP.md'] = """# Research Gap

## Previous System (Baseline)

The senior/previous project used a YOLOv8-based frame-level detection approach:

Camera → YOLO → Drowning Detection → Alert

**Limitation**: Frame-level detection treats each frame independently.
It cannot distinguish between similar instantaneous postures such as:
- A person floating (normal) vs. a person face-down (potential drowning)
- A person jumping in vs. a person who has stopped moving

## Identified Research Gap

Frame-level object detection may not fully capture the temporal nature
of drowning-related behavior. Drowning is a process, not a single frame.

Key behaviors that require temporal analysis:
1. Progressive reduction in movement over time
2. Transition from normal → distress → drowning
3. Duration of inactivity
4. Change in body posture over time (aspect ratio change)

## Proposed Solution

Combining:
1. YOLO person detection (spatial information)
2. ByteTrack multi-object tracking (identity continuity)
3. Temporal feature extraction (motion history)
4. LSTM temporal model (sequential pattern recognition)

## Research Hypothesis

> Temporal behavior analysis combined with person tracking will provide
> more reliable drowning detection than frame-level detection alone.

**This is a hypothesis — not a conclusion.**
The experimental results will determine whether this hypothesis holds.

## Evaluation Plan

Experiments A vs C:
- EXP-A: YOLOv8 baseline (frame-level)
- EXP-C: YOLOv8 + ByteTrack + LSTM (temporal)

Comparison metrics: Precision, Recall, F1, FPR, FNR, FPS, Latency
"""

for rel, content in files.items():
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')
    print(f'Written: {rel}')

print('All files created successfully.')
