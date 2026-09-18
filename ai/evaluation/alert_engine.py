# AquaGuard AI - Alert Engine
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
