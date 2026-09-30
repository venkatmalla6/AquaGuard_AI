"""
AquaGuard AI - Physics & Biomechanics-Grounded Aquatic Scenario Engine (Phase 14)
Generates parameterized realistic multi-swimmer trajectories, physiological behaviors,
and 16-D kinematic feature vectors for normal swimming, distress, IDR drowning, and sinking.
"""
from __future__ import annotations
import math
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from loguru import logger

class ScenarioType(str, Enum):
    NORMAL_LAP_SWIMMING = "normal_lap_swimming"
    FRANTIC_DISTRESS = "frantic_distress"
    INSTINCTIVE_DROWNING = "instinctive_drowning"
    SUBMERSION_IMMOBILITY = "submersion_immobility"
    PLAYFUL_SPLASHING = "playful_splashing"
    MULTI_SWIMMER_CROWD = "multi_swimmer_crowd"

@dataclass
class SwimmerFrameState:
    frame_index: int
    timestamp: float
    x: float          # Center X (pixels or normalized)
    y: float          # Center Y
    width: float      # Bounding box width
    height: float     # Bounding box height
    aspect_ratio: float
    behavior_label: str  # "normal", "distress", "drowning"
    feature_vector: np.ndarray  # 16-D feature vector

@dataclass
class SwimmerTrajectory:
    track_id: int
    scenario_type: ScenarioType
    primary_label: str
    states: List[SwimmerFrameState] = field(default_factory=list)

    @property
    def feature_matrix(self) -> np.ndarray:
        return np.array([s.feature_vector for s in self.states], dtype=np.float32)

class ScenarioEngine:
    """
    Simulates high-fidelity human swimming biomechanics in an aquatic environment.
    """

    def __init__(
        self,
        frame_width: int = 1280,
        frame_height: int = 720,
        fps: float = 30.0,
        random_seed: Optional[int] = 42
    ):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.fps = fps
        self.dt = 1.0 / fps
        self.rng = np.random.default_rng(random_seed)

    def generate_scenario(
        self,
        scenario_type: ScenarioType = ScenarioType.INSTINCTIVE_DROWNING,
        duration_seconds: float = 10.0,
        num_swimmers: int = 1,
        distress_onset_second: float = 3.0
    ) -> List[SwimmerTrajectory]:
        """
        Generates trajectories for one or more swimmers under specified scenario conditions.
        """
        total_frames = int(duration_seconds * self.fps)
        onset_frame = int(distress_onset_second * self.fps)
        trajectories: List[SwimmerTrajectory] = []

        if scenario_type == ScenarioType.MULTI_SWIMMER_CROWD:
            num_swimmers = max(3, num_swimmers)

        for track_id in range(1, num_swimmers + 1):
            # For multi-swimmer crowd: 1 swimmer experiences distress/drowning, others swim normally
            if scenario_type == ScenarioType.MULTI_SWIMMER_CROWD:
                swimmer_scenario = ScenarioType.INSTINCTIVE_DROWNING if track_id == 1 else ScenarioType.NORMAL_LAP_SWIMMING
            else:
                swimmer_scenario = scenario_type

            traj = self._generate_single_swimmer(
                track_id=track_id,
                scenario_type=swimmer_scenario,
                total_frames=total_frames,
                onset_frame=onset_frame
            )
            trajectories.append(traj)

        return trajectories

    def _generate_single_swimmer(
        self,
        track_id: int,
        scenario_type: ScenarioType,
        total_frames: int,
        onset_frame: int
    ) -> SwimmerTrajectory:
        primary_label = "normal"
        if scenario_type in (ScenarioType.INSTINCTIVE_DROWNING, ScenarioType.SUBMERSION_IMMOBILITY):
            primary_label = "drowning"
        elif scenario_type == ScenarioType.FRANTIC_DISTRESS:
            primary_label = "distress"

        # Initial random position in pool
        margin = 120
        cx = self.rng.uniform(margin, self.frame_width - margin)
        cy = self.rng.uniform(margin, self.frame_height - margin)
        vx = self.rng.uniform(-40.0, 40.0) # pixels/sec
        vy = self.rng.uniform(-20.0, 20.0)

        states: List[SwimmerFrameState] = []
        prev_cx, prev_cy = cx, cy

        for f in range(total_frames):
            ts = f * self.dt
            is_distressed_phase = (f >= onset_frame)

            # Determine posture and kinematics based on behavioral regime
            if not is_distressed_phase or scenario_type == ScenarioType.NORMAL_LAP_SWIMMING:
                # Normal horizontal swimming
                label = "normal"
                w = 110.0 + 8.0 * math.sin(ts * 3.5) # Arm stroke extension
                h = 55.0 + 4.0 * math.cos(ts * 3.5)
                # Steady velocity
                cx += vx * self.dt
                cy += vy * self.dt
                # Pool boundary bounce
                if cx < margin or cx > self.frame_width - margin:
                    vx = -vx
                if cy < margin or cy > self.frame_height - margin:
                    vy = -vy

                vert_ratio = 0.20 + 0.05 * math.sin(ts)
                inactivity = 0.05
                mv_variance = 35.0 + 5.0 * math.sin(ts * 2.0)

            elif scenario_type == ScenarioType.FRANTIC_DISTRESS:
                # Active splashing, high movement variance, waving
                label = "distress"
                w = 75.0 + 15.0 * self.rng.uniform(-1, 1)
                h = 85.0 + 15.0 * self.rng.uniform(-1, 1)
                cx += self.rng.normal(0.0, 35.0) * self.dt
                cy += self.rng.normal(0.0, 25.0) * self.dt
                vert_ratio = 0.65 + 0.1 * math.sin(ts * 5.0)
                inactivity = 0.10
                mv_variance = 250.0 + 50.0 * self.rng.uniform(0, 1)

            elif scenario_type == ScenarioType.INSTINCTIVE_DROWNING:
                # Pia (1974) Instinctive Drowning Response: Vertical body, no forward progress, lateral arm press
                label = "drowning"
                w = 50.0 + 5.0 * math.sin(ts * 1.5)  # Narrow horizontal profile
                h = 100.0 + 8.0 * math.sin(ts * 1.5) # Tall vertical posture
                # Minimal translation, bobbing vertically
                cx += self.rng.normal(0.0, 4.0) * self.dt
                cy += (2.0 + 3.0 * math.sin(ts * 2.0)) * self.dt
                vert_ratio = 0.88 + 0.05 * math.sin(ts * 2.0)
                inactivity = 0.70 + 0.15 * min(1.0, (f - onset_frame) / 60.0)
                mv_variance = 15.0 + 5.0 * self.rng.uniform(0, 1)

            elif scenario_type == ScenarioType.SUBMERSION_IMMOBILITY:
                # Silent drowning / unconscious submersion: shrinking bounding box, sinking
                label = "drowning"
                sink_factor = max(0.2, 1.0 - 0.015 * (f - onset_frame))
                w = 60.0 * sink_factor
                h = 60.0 * sink_factor
                cx += 0.0
                cy += 4.0 * self.dt # Constant sinking downwards
                vert_ratio = 0.50
                inactivity = 0.95
                mv_variance = 1.5

            else:
                # Playful splashing: high movement variance but horizontal posture (safe)
                label = "normal"
                w = 95.0 + 10.0 * math.sin(ts * 4.0)
                h = 60.0 + 8.0 * math.cos(ts * 4.0)
                cx += vx * 0.3 * self.dt
                cy += vy * 0.3 * self.dt
                vert_ratio = 0.30
                inactivity = 0.08
                mv_variance = 180.0

            # Kinematic vector computation
            disp = math.sqrt((cx - prev_cx)**2 + (cy - prev_cy)**2)
            speed = disp / self.dt
            vel_x = (cx - prev_cx) / self.dt
            vel_y = (cy - prev_cy) / self.dt
            angle = math.atan2(vel_y, vel_x + 1e-6)
            dir_sin = math.sin(angle)
            dir_cos = math.cos(angle)
            aspect_ratio = w / max(1.0, h)
            area_norm = (w * h) / (self.frame_width * self.frame_height)

            # Assemble 16-D feature vector matching TrackFeatureExtractor
            fv = np.zeros(16, dtype=np.float32)
            fv[0] = cx / self.frame_width      # cx_norm
            fv[1] = cy / self.frame_height     # cy_norm
            fv[2] = w / self.frame_width       # w_norm
            fv[3] = h / self.frame_height      # h_norm
            fv[4] = aspect_ratio               # aspect_ratio
            fv[5] = area_norm                  # area_norm
            fv[6] = disp / self.frame_width    # displacement
            fv[7] = vel_x / self.frame_width   # velocity_x
            fv[8] = vel_y / self.frame_height  # velocity_y
            fv[9] = speed                      # speed
            fv[10] = 0.0                       # acceleration proxy
            fv[11] = dir_sin                   # direction_sin
            fv[12] = dir_cos                   # direction_cos
            fv[13] = mv_variance               # movement_variance
            fv[14] = vert_ratio                # vertical_ratio
            fv[15] = inactivity                # inactivity

            state = SwimmerFrameState(
                frame_index=f,
                timestamp=ts,
                x=round(cx, 1),
                y=round(cy, 1),
                width=round(w, 1),
                height=round(h, 1),
                aspect_ratio=round(aspect_ratio, 3),
                behavior_label=label,
                feature_vector=fv
            )
            states.append(state)
            prev_cx, prev_cy = cx, cy

        traj = SwimmerTrajectory(
            track_id=track_id,
            scenario_type=scenario_type,
            primary_label=primary_label,
            states=states
        )
        return traj
