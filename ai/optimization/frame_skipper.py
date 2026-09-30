# AquaGuard AI - Adaptive Frame Skipping Engine for Edge Surveillance (Phase 12)
from __future__ import annotations
import time
from collections import deque
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from loguru import logger

@dataclass
class SkipperStats:
    total_frames: int = 0
    processed_frames: int = 0
    skipped_frames: int = 0
    average_processing_ms: float = 0.0
    effective_fps: float = 0.0
    cpu_reduction_percent: float = 0.0
    current_stride: int = 1
    burst_mode_active: bool = False

class AdaptiveFrameSkipper:
    def __init__(
        self,
        target_fps: float = 30.0,
        min_stride: int = 1,
        max_stride: int = 4,
        idle_stride: int = 3,
        latency_window_size: int = 15,
        enabled: bool = True
    ):
        self.target_fps = target_fps
        self.frame_budget_ms = 1000.0 / target_fps
        self.min_stride = min_stride
        self.max_stride = max_stride
        self.idle_stride = idle_stride
        self.enabled = enabled

        self._frame_index = 0
        self._latency_history = deque(maxlen=latency_window_size)
        self._current_stride = min_stride
        self._burst_active = False
        self._burst_cooldown_frames = 0
        self._BURST_COOLDOWN_WINDOW = int(target_fps * 2)

        self.stats = SkipperStats(current_stride=self._current_stride)

    def should_process_frame(
        self,
        frame_number: Optional[int] = None,
        active_threat: bool = False,
        track_count: int = 0
    ) -> Tuple[bool, int]:
        if frame_number is not None:
            self._frame_index = frame_number
        else:
            self._frame_index += 1

        self.stats.total_frames += 1

        if not self.enabled:
            self.stats.processed_frames += 1
            self.stats.current_stride = 1
            self.stats.burst_mode_active = False
            return True, 1

        # 1. Active Threat Burst Overrides: Never skip when a life is at risk
        if active_threat:
            self._burst_active = True
            self._burst_cooldown_frames = self._BURST_COOLDOWN_WINDOW

        if self._burst_cooldown_frames > 0:
            self._burst_cooldown_frames -= 1
            self._burst_active = True
            self._current_stride = 1
        else:
            self._burst_active = False

        # 2. If burst mode is not active, determine adaptive stride
        if not self._burst_active:
            if track_count == 0:
                self._current_stride = self.idle_stride
            elif len(self._latency_history) >= 5:
                avg_ms = float(np.mean(self._latency_history))
                if avg_ms > self.frame_budget_ms * 1.15:
                    self._current_stride = min(self.max_stride, self._current_stride + 1)
                elif avg_ms < self.frame_budget_ms * 0.75:
                    self._current_stride = max(self.min_stride, self._current_stride - 1)

        # 3. Stride decision
        process_now = (self._frame_index % self._current_stride == 0)

        if process_now:
            self.stats.processed_frames += 1
        else:
            self.stats.skipped_frames += 1

        self.stats.current_stride = self._current_stride
        self.stats.burst_mode_active = self._burst_active
        if self.stats.total_frames > 0:
            self.stats.cpu_reduction_percent = round(
                (self.stats.skipped_frames / self.stats.total_frames) * 100.0, 1
            )

        return process_now, self._current_stride

    def record_latency(self, elapsed_ms: float):
        self._latency_history.append(elapsed_ms)
        self.stats.average_processing_ms = round(float(np.mean(self._latency_history)), 2)

    def get_status_dict(self) -> Dict[str, Any]:
        return {
            'enabled': self.enabled,
            'target_fps': self.target_fps,
            'frame_budget_ms': round(self.frame_budget_ms, 2),
            'current_stride': self.stats.current_stride,
            'burst_mode_active': self.stats.burst_mode_active,
            'total_frames': self.stats.total_frames,
            'processed_frames': self.stats.processed_frames,
            'skipped_frames': self.stats.skipped_frames,
            'cpu_reduction_percent': self.stats.cpu_reduction_percent,
            'average_processing_ms': self.stats.average_processing_ms
        }

    def reset(self):
        self._frame_index = 0
        self._latency_history.clear()
        self._current_stride = self.min_stride
        self._burst_active = False
        self._burst_cooldown_frames = 0
        self.stats = SkipperStats(current_stride=self._current_stride)

if __name__ == '__main__':
    skipper = AdaptiveFrameSkipper(target_fps=30.0, min_stride=1, max_stride=3, idle_stride=3)
    for i in range(60):
        # First 30 frames: idle pool
        process, stride = skipper.should_process_frame(frame_number=i, active_threat=False, track_count=0)
        skipper.record_latency(15.0)
    print('Idle stats:', skipper.get_status_dict())

    # Frame 60-90: Threat emerges!
    for i in range(60, 90):
        process, stride = skipper.should_process_frame(frame_number=i, active_threat=True, track_count=1)
        skipper.record_latency(28.0)
    print('Threat burst stats:', skipper.get_status_dict())
