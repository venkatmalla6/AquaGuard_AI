"""
AquaGuard AI - Video Ingestion & Processing Pipeline
Extracts video metadata and processes video frames through spatial detection,
multi-person tracking, and behavioral annotation.
"""
from dataclasses import dataclass
from pathlib import Path
import sys
import time
from typing import Callable, Optional, Dict, Any, List
import cv2
import numpy as np
from loguru import logger

# Ensure root is in path
root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from ai.detection.detector import YOLODetector, PersonDetection
from ai.tracking.tracker import PersonTracker, TrackResult


@dataclass
class VideoMetadata:
    """Extracted technical parameters from video file."""
    duration_seconds: float
    fps: float
    total_frames: int
    resolution_width: int
    resolution_height: int


def extract_video_metadata(filepath: str) -> VideoMetadata:
    """
    Open video via OpenCV and extract resolution, frame rate, and duration.
    Raises ValueError if video cannot be opened or is corrupted.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {filepath}")

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"OpenCV could not open video file: {filepath}")

    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)
        duration = total_frames / fps if fps > 0 else 0.0

        return VideoMetadata(
            duration_seconds=round(duration, 2),
            fps=round(fps, 2),
            total_frames=total_frames,
            resolution_width=width,
            resolution_height=height,
        )
    finally:
        cap.release()


class VideoProcessor:
    """
    Asynchronous video processor that runs person detection, tracking,
    and behavior state annotation over a video file.
    """

    def __init__(
        self,
        conf_threshold: float = 0.35,
        target_size: tuple = (640, 360),
    ):
        self.conf_threshold = conf_threshold
        self.target_size = target_size
        self.tracker = PersonTracker(confidence=conf_threshold)

    def process_file(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
        frame_interval: int = 1,
    ) -> Dict[str, Any]:
        """
        Processes the input video and writes an annotated video to output_path.
        Calls progress_callback(current_frame, total_frames, percent) periodically.
        """
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open input video: {input_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)

        # Output video writer (mp4v codec)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        frame_count = 0
        unique_track_ids = set()
        alert_events = 0
        start_time = time.time()

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1

                # Track swimmers across frames
                tracks, _ = self.tracker.track(frame, frame_number=frame_count)

                has_drowning_threat = False

                for trk in tracks:
                    unique_track_ids.add(trk.track_id)
                    x1, y1 = int(trk.bbox_x1), int(trk.bbox_y1)
                    x2, y2 = int(trk.bbox_x2), int(trk.bbox_y2)
                    box_w = max(1, x2 - x1)
                    box_h = max(1, y2 - y1)

                    # Posture heuristic:
                    # w/h < 0.6 correlates with vertical sinking/distress posture
                    is_vertical = (box_w / box_h) < 0.6
                    if is_vertical:
                        color = (0, 0, 255)  # Red - Potential Drowning
                        state_label = "DROWNING RISK"
                        has_drowning_threat = True
                        alert_events += 1
                    else:
                        color = (0, 255, 0)  # Green - Normal
                        state_label = "NORMAL"

                    # Bounding Box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                    # Label tag
                    label = f"ID:{trk.track_id} {state_label} {trk.confidence:.2f}"
                    (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                    cv2.rectangle(frame, (x1, max(0, y1 - 20)), (x1 + lw + 6, max(0, y1)), color, -1)
                    cv2.putText(
                        frame,
                        label,
                        (x1 + 3, max(14, y1 - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.42,
                        (255, 255, 255),
                        1,
                        cv2.LINE_AA,
                    )

                # Overlay HUD / Telemetry
                cv2.rectangle(frame, (10, 10), (330, 75), (0, 0, 0), -1)
                cv2.rectangle(frame, (10, 10), (330, 75), (0, 180, 212), 1)
                cv2.putText(
                    frame,
                    f"AquaGuard AI | Frame: {frame_count}/{total_frames}",
                    (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.48,
                    (0, 255, 255),
                    1,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    frame,
                    f"Active: {len(tracks)} | Total Tracked: {len(unique_track_ids)}",
                    (20, 48),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.42,
                    (200, 200, 200),
                    1,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    frame,
                    f"FPS: {fps:.1f} | Edge CPU Inference",
                    (20, 66),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.40,
                    (150, 150, 150),
                    1,
                    cv2.LINE_AA,
                )

                # Alert strobe banner
                if has_drowning_threat:
                    cv2.rectangle(frame, (width // 2 - 200, 10), (width // 2 + 200, 50), (0, 0, 220), -1)
                    cv2.putText(
                        frame,
                        "CRITICAL: DISTRESS DETECTED",
                        (width // 2 - 180, 38),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.65,
                        (255, 255, 255),
                        2,
                        cv2.LINE_AA,
                    )

                out.write(frame)

                if progress_callback and (frame_count % 10 == 0 or frame_count == total_frames):
                    pct = round((frame_count / total_frames) * 100, 1) if total_frames > 0 else 0.0
                    progress_callback(frame_count, total_frames, pct)

        finally:
            cap.release()
            out.release()

        elapsed = time.time() - start_time
        processed_fps = frame_count / elapsed if elapsed > 0 else 0.0

        return {
            "total_frames_processed": frame_count,
            "unique_swimmers_tracked": len(unique_track_ids),
            "alert_events_count": alert_events,
            "processing_time_seconds": round(elapsed, 2),
            "average_processing_fps": round(processed_fps, 1),
            "output_video_path": output_path,
        }