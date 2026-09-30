"""
AquaGuard AI - Scenario Evaluation Engine (Phase 14)
Runs the end-to-end AI detection & alert logic against synthetic scenarios
to calculate Time-to-Detect (TTD), False Alarm Rate (FAR), and Alert Precision.
"""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from loguru import logger

root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from ai.scenarios.scenario_engine import ScenarioEngine, ScenarioType, SwimmerTrajectory
from ai.pipeline.live_pipeline import FeatureScorer
from ai.evaluation.alert_engine import AlertEngine, AlertLevel

class ScenarioEvaluator:
    """
    Evaluates AquaGuard AI behavioral detection on synthetic ground truth.
    """

    def __init__(self, edge_backend: str = "onnx"):
        self.scorer = FeatureScorer(edge_backend=edge_backend)
        self.alert_engine = AlertEngine(
            distress_confidence=0.55,
            drowning_confidence=0.75,
            consecutive_frames=5,
            cooldown_seconds=30
        )

    def evaluate_trajectory(
        self,
        trajectory: SwimmerTrajectory,
        onset_second: float = 3.0
    ) -> Dict[str, Any]:
        """
        Processes each frame state through the AI classifier and alert engine.
        """
        self.alert_engine.reset()
        alerts_triggered = []
        frame_predictions = []

        history_buffer = []

        for state in trajectory.states:
            history_buffer.append(state.feature_vector)
            seq_np = np.array(history_buffer[-30:]) if len(history_buffer) >= 5 else None

            # Score using Edge AI
            c_norm, c_dist, c_drown = self.scorer.score(state.feature_vector, sequence=seq_np)
            pred_label = self.scorer.behavior_label(c_norm, c_dist, c_drown)

            alert = self.alert_engine.process(
                track_id=trajectory.track_id,
                behavior=pred_label,
                confidence_normal=c_norm,
                confidence_distress=c_dist,
                confidence_drowning=c_drown
            )

            if alert:
                alerts_triggered.append({
                    "frame_index": state.frame_index,
                    "timestamp": state.timestamp,
                    "level": alert["level"],
                    "behavior": alert.get("behavior", "")
                })

            frame_predictions.append({
                "frame_index": state.frame_index,
                "timestamp": state.timestamp,
                "ground_truth": state.behavior_label,
                "predicted": pred_label,
                "c_drowning": round(c_drown, 3),
                "c_distress": round(c_dist, 3),
                "c_normal": round(c_norm, 3)
            })

        # Calculate academic performance metrics
        correct_frames = sum(1 for p in frame_predictions if p["ground_truth"] == p["predicted"])
        frame_accuracy = round(correct_frames / max(1, len(frame_predictions)), 4)

        first_alert = alerts_triggered[0] if alerts_triggered else None
        time_to_detect = round(first_alert["timestamp"] - onset_second, 2) if first_alert and trajectory.primary_label == "drowning" else None

        false_alarms = sum(1 for a in alerts_triggered if a["timestamp"] < onset_second)

        return {
            "track_id": trajectory.track_id,
            "scenario_type": trajectory.scenario_type.value,
            "total_frames": len(trajectory.states),
            "ground_truth_label": trajectory.primary_label,
            "frame_accuracy": frame_accuracy,
            "alerts_count": len(alerts_triggered),
            "first_alert": first_alert,
            "time_to_detect_seconds": time_to_detect,
            "false_alarms_before_onset": false_alarms,
            "predictions_sample": frame_predictions[::10] # Every 10th frame sample
        }
