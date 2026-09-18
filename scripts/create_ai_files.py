import os, pathlib

base = pathlib.Path(r"D:\Btech\PROJECTS\AquaGuard_AI")

files = {
    "ai/features/feature_extractor.py": """# AquaGuard AI - Temporal Feature Extractor
from collections import deque
import math, numpy as np

class FrameData:
    def __init__(self, frame_number, timestamp, cx, cy, w, h, conf, frame_w, frame_h):
        self.frame_number = frame_number
        self.timestamp = timestamp
        self.cx = cx
        self.cy = cy
        self.w = w
        self.h = h
        self.conf = conf
        self.frame_w = frame_w
        self.frame_h = frame_h

class TemporalFeatureVector:
    NUM_FEATURES = 16
    def __init__(self):
        self.cx_norm = self.cy_norm = self.w_norm = self.h_norm = 0.0
        self.aspect_ratio = self.area_norm = 0.0
        self.displacement = self.velocity_x = self.velocity_y = self.speed = 0.0
        self.acceleration = self.direction_sin = 0.0
        self.direction_cos = 1.0
        self.movement_variance = self.vertical_ratio = self.inactivity = 0.0

    def to_numpy(self):
        return np.array([
            self.cx_norm, self.cy_norm, self.w_norm, self.h_norm,
            self.aspect_ratio, self.area_norm,
            self.displacement, self.velocity_x, self.velocity_y, self.speed,
            self.acceleration, self.direction_sin, self.direction_cos,
            self.movement_variance, self.vertical_ratio, self.inactivity,
        ], dtype=np.float32)

class TrackFeatureExtractor:
    def __init__(self, track_id, sequence_length=32, inactivity_threshold=3.0):
        self.track_id = track_id
        self.sequence_length = sequence_length
        self.inactivity_threshold = inactivity_threshold
        self._history = deque(maxlen=sequence_length + 5)
        self._displacement_history = deque(maxlen=10)
        self._prev_frame = None
        self._prev_speed = 0.0

    def update(self, frame_data):
        fv = self._compute_features(frame_data)
        self._history.append(fv)
        self._prev_frame = frame_data
        return fv

    def _compute_features(self, f):
        fv = TemporalFeatureVector()
        fv.cx_norm = f.cx / f.frame_w if f.frame_w > 0 else 0.0
        fv.cy_norm = f.cy / f.frame_h if f.frame_h > 0 else 0.0
        fv.w_norm = f.w / f.frame_w if f.frame_w > 0 else 0.0
        fv.h_norm = f.h / f.frame_h if f.frame_h > 0 else 0.0
        fv.aspect_ratio = (f.w / f.h) if f.h > 0 else 1.0
        fv.area_norm = (f.w * f.h) / (f.frame_w * f.frame_h) if f.frame_w * f.frame_h > 0 else 0.0
        if self._prev_frame is not None:
            dx = f.cx - self._prev_frame.cx
            dy = f.cy - self._prev_frame.cy
            fv.velocity_x = dx
            fv.velocity_y = dy
            fv.speed = math.sqrt(dx**2 + dy**2)
            fv.displacement = fv.speed
            fv.acceleration = fv.speed - self._prev_speed
            angle = math.atan2(dy, dx) if fv.speed > 0 else 0.0
            fv.direction_sin = math.sin(angle)
            fv.direction_cos = math.cos(angle)
            total = abs(dx) + abs(dy) + 1e-6
            fv.vertical_ratio = abs(dy) / total
            fv.inactivity = 1.0 if fv.speed < self.inactivity_threshold else 0.0
            self._displacement_history.append(fv.displacement)
            if len(self._displacement_history) >= 3:
                fv.movement_variance = float(np.var(list(self._displacement_history)))
        self._prev_speed = fv.speed
        return fv

    def get_sequence(self):
        if len(self._history) < self.sequence_length:
            return None
        seq = list(self._history)[-self.sequence_length:]
        return np.stack([fv.to_numpy() for fv in seq])

    @property
    def history_length(self):
        return len(self._history)
""",

    "ai/temporal/lstm_model.py": """# AquaGuard AI - LSTM/GRU Temporal Behavior Model
import torch
import torch.nn as nn

class BehaviorClassifier(nn.Module):
    def __init__(self, input_size=16, hidden_size=128, num_layers=2,
                 num_classes=3, dropout=0.3, model_type="lstm"):
        super().__init__()
        self.model_type = model_type
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        rnn_cls = nn.LSTM if model_type == "lstm" else nn.GRU
        self.rnn = rnn_cls(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True,
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, num_classes),
        )

    def forward(self, x):
        out, _ = self.rnn(x)
        last = out[:, -1, :]
        return self.classifier(last)
""",

    "ai/tracking/__init__.py": "# Tracking module",
    "ai/training/__init__.py": "# Training module",
    "ai/evaluation/__init__.py": "# Evaluation module",
}

for rel_path, content in files.items():
    full_path = base / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    print(f"Written: {rel_path}")

print("All AI files written.")

