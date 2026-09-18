# AquaGuard AI - Person Tracker (ByteTrack wrapper)
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
