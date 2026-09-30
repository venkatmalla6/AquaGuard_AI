"""
AquaGuard AI - Synthetic Video Renderer (Phase 14)
Renders high-definition synthetic pool surveillance videos with animated water caustic ripples,
lane markers, and swimmer avatars exhibiting biomechanically accurate motion and distress.
"""
from __future__ import annotations
import os
import sys
import json
import math
from pathlib import Path
from typing import Dict, Any, List, Optional
import cv2
import numpy as np
from loguru import logger

root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from ai.scenarios.scenario_engine import ScenarioEngine, ScenarioType, SwimmerTrajectory

class SyntheticVideoRenderer:
    """
    Renders realistic synthetic aquatic surveillance video feeds (.mp4).
    """

    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
        fps: float = 30.0
    ):
        self.width = width
        self.height = height
        self.fps = fps

    def render_scenario_to_video(
        self,
        trajectories: List[SwimmerTrajectory],
        output_video_path: str,
        output_json_path: Optional[str] = None,
        draw_ground_truth_boxes: bool = False
    ) -> Dict[str, Any]:
        """
        Renders trajectory list into an MP4 video file with metadata.
        """
        os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
        total_frames = max(len(t.states) for t in trajectories)

        # VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_video_path, fourcc, self.fps, (self.width, self.height))

        # Ground truth annotations
        ground_truth_records = []

        for f in range(total_frames):
            frame = self._render_background(f)
            frame_records = []

            for traj in trajectories:
                if f < len(traj.states):
                    state = traj.states[f]
                    self._render_swimmer(frame, state, traj.track_id)

                    frame_records.append({
                        "track_id": traj.track_id,
                        "behavior": state.behavior_label,
                        "bbox": [
                            max(0, int(state.x - state.width / 2)),
                            max(0, int(state.y - state.height / 2)),
                            min(self.width, int(state.x + state.width / 2)),
                            min(self.height, int(state.y + state.height / 2)),
                        ],
                        "feature_vector": state.feature_vector.tolist()
                    })

                    if draw_ground_truth_boxes:
                        x1 = max(0, int(state.x - state.width / 2))
                        y1 = max(0, int(state.y - state.height / 2))
                        x2 = min(self.width, int(state.x + state.width / 2))
                        y2 = min(self.height, int(state.y + state.height / 2))
                        box_color = (0, 0, 255) if state.behavior_label == "drowning" else (0, 140, 255) if state.behavior_label == "distress" else (0, 255, 0)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)

            # Draw HUD watermark
            self._render_hud(frame, f, total_frames, trajectories)
            writer.write(frame)

            ground_truth_records.append({
                "frame_index": f,
                "timestamp": round(f / self.fps, 3),
                "swimmers": frame_records
            })

        writer.release()

        # Save JSON metadata
        if output_json_path:
            os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
            meta = {
                "total_frames": total_frames,
                "fps": self.fps,
                "resolution": [self.width, self.height],
                "num_swimmers": len(trajectories),
                "scenario_types": [t.scenario_type.value for t in trajectories],
                "annotations": ground_truth_records
            }
            with open(output_json_path, "w", encoding="utf-8") as jf:
                json.dump(meta, jf, indent=2)

        file_size_mb = os.path.getsize(output_video_path) / (1024 * 1024)
        logger.info(f"Rendered synthetic scenario video: {output_video_path} ({file_size_mb:.2f} MB, {total_frames} frames)")

        return {
            "video_path": output_video_path,
            "json_path": output_json_path,
            "total_frames": total_frames,
            "duration_seconds": round(total_frames / self.fps, 2),
            "size_mb": round(file_size_mb, 2)
        }

    def _render_background(self, frame_index: int) -> np.ndarray:
        """Renders turquoise water with caustic light ripples and lane ropes."""
        # Base pool water color gradient (deep cyan to bright pool blue)
        t = frame_index / self.fps
        bg = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        bg[:, :] = (180, 130, 20)  # BGR turquoise pool tone

        # Add pool lane markers
        lane_step = self.height // 4
        for y in range(lane_step, self.height, lane_step):
            cv2.line(bg, (0, y), (self.width, y), (50, 50, 200), 2)  # Red/blue lane rope

        # Caustic ripples (wave modulation)
        xs = np.linspace(0, 10, self.width)
        ys = np.linspace(0, 8, self.height)
        ripple = (np.sin(xs[None, :] + t * 2.0) * np.cos(ys[:, None] + t * 1.5) * 12.0).astype(np.int16)
        bg_int = bg.astype(np.int16) + ripple[:, :, None]
        return np.clip(bg_int, 0, 255).astype(np.uint8)

    def _render_swimmer(self, frame: np.ndarray, state: Any, track_id: int):
        """Draws human swimmer avatar matching behavioral posture."""
        cx, cy = int(state.x), int(state.y)
        w, h = max(10, int(state.width)), max(10, int(state.height))
        lbl = state.behavior_label

        # Water foam/splashing particles if frantic distress
        if lbl == "distress":
            for _ in range(8):
                rx = cx + np.random.randint(-w // 2 - 10, w // 2 + 10)
                ry = cy + np.random.randint(-h // 2 - 10, h // 2 + 10)
                cv2.circle(frame, (rx, ry), np.random.randint(2, 6), (255, 255, 255), -1)

        # Torso ellipse
        torso_color = (60, 130, 200) if lbl == "normal" else (40, 80, 180) if lbl == "distress" else (30, 40, 120)
        cv2.ellipse(frame, (cx, cy), (w // 2, h // 2), 0, 0, 360, torso_color, -1)
        cv2.ellipse(frame, (cx, cy), (w // 2, h // 2), 0, 0, 360, (20, 20, 20), 1)

        # Head circle
        head_radius = max(6, min(w, h) // 4)
        head_y = cy - h // 3 if h > w else cy
        head_x = cx if h > w else cx - w // 3
        cv2.circle(frame, (head_x, head_y), head_radius, (120, 180, 230), -1)  # Skin tone
        cv2.circle(frame, (head_x, head_y), head_radius, (10, 10, 10), 1)

    def _render_hud(self, frame: np.ndarray, frame_index: int, total_frames: int, trajectories: List[SwimmerTrajectory]):
        """Renders simulation telemetry on top of video."""
        cv2.rectangle(frame, (10, 10), (380, 70), (15, 23, 42), -1)
        cv2.rectangle(frame, (10, 10), (380, 70), (0, 180, 220), 1)
        time_str = f"Time: {frame_index / self.fps:.2f}s / {total_frames / self.fps:.2f}s"
        cv2.putText(frame, f"AquaGuard AI | Scenario Engine (Phase 14)", (18, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"Frame: {frame_index} | {time_str} | Swimmers: {len(trajectories)}", (18, 46), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 200), 1, cv2.LINE_AA)
        active_states = [t.states[min(frame_index, len(t.states) - 1)].behavior_label for t in trajectories]
        cv2.putText(frame, f"Active State: {', '.join(set(active_states)).upper()}", (18, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 120), 1, cv2.LINE_AA)
