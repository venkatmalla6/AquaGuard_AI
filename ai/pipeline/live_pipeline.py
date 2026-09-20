# AquaGuard AI - Live Detection Pipeline
# Phase 6: Live Tracking + 16-D Feature Integration
"""
Architecture:
  Frame -> PersonTracker (ByteTrack) -> TrackFeatureExtractor (16-D)
        -> FeatureScorer (rule-based, LSTM-ready) -> AlertEngine -> WebSocket
"""
from __future__ import annotations
import sys, time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import cv2, numpy as np
from loguru import logger

root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from ai.tracking.tracker import PersonTracker, TrackResult
from ai.features.feature_extractor import TrackFeatureExtractor, FrameData
from ai.evaluation.alert_engine import AlertEngine, AlertLevel


# ============================================================
# Data Containers
# ============================================================

@dataclass
class TrackFeatureResult:
    track: TrackResult
    feature_vector: Optional[np.ndarray]
    sequence_ready: bool
    confidence_normal: float = 1.0
    confidence_distress: float = 0.0
    confidence_drowning: float = 0.0
    behavior_label: str = "normal"
    alert: Optional[Dict[str, Any]] = None


@dataclass
class FrameResult:
    frame_number: int
    timestamp: float
    tracks: List[TrackFeatureResult]
    alert_count: int
    processing_ms: float
    annotated_frame: Optional[np.ndarray] = None


# ============================================================
# Feature-Based Behavior Scorer
# ============================================================

class FeatureScorer:
    """
    Converts a 16-D feature vector into (normal, distress, drowning) confidences.

    WHY rule-based first:
      - LSTM needs training data collected by this pipeline.
      - Rules are interpretable and serve as the academic baseline.
      - When lstm_model is set, neural inference replaces rules seamlessly.

    Feature index map (must match TrackFeatureExtractor.to_numpy() order):
      0:cx_norm  1:cy_norm  2:w_norm   3:h_norm   4:aspect_ratio  5:area_norm
      6:displacement  7:vel_x  8:vel_y  9:speed  10:acceleration
      11:dir_sin  12:dir_cos  13:movement_variance  14:vertical_ratio  15:inactivity
    """
    FEATURE_IDX = {
        "cx_norm":0,"cy_norm":1,"w_norm":2,"h_norm":3,"aspect_ratio":4,"area_norm":5,
        "displacement":6,"velocity_x":7,"velocity_y":8,"speed":9,"acceleration":10,
        "direction_sin":11,"direction_cos":12,"movement_variance":13,
        "vertical_ratio":14,"inactivity":15,
    }

    def __init__(self, lstm_model=None):
        self.lstm_model = lstm_model

    def score(self, feature_vector: np.ndarray):
        if self.lstm_model is not None:
            return self._score_lstm(feature_vector)
        return self._score_rules(feature_vector)

    def _score_rules(self, fv: np.ndarray):
        idx = self.FEATURE_IDX
        inactivity   = float(fv[idx["inactivity"]])
        aspect_ratio = float(fv[idx["aspect_ratio"]])
        speed        = float(fv[idx["speed"]])
        mv_variance  = float(fv[idx["movement_variance"]])
        vert_ratio   = float(fv[idx["vertical_ratio"]])

        # Component scores (0-1 each)
        inactivity_score = inactivity
        posture_score    = max(0.0, min(1.0, (0.65 - aspect_ratio) / 0.65))
        thrash_score     = min(1.0, mv_variance / 500.0)
        vert_score       = max(0.0, vert_ratio - 0.5) * 2.0
        low_speed_score  = max(0.0, 1.0 - speed / 5.0) if speed < 5.0 else 0.0

        risk = (
            0.35 * inactivity_score +
            0.25 * posture_score    +
            0.15 * thrash_score     +
            0.15 * vert_score       +
            0.10 * low_speed_score
        )
        risk = float(np.clip(risk, 0.0, 1.0))

        if risk >= 0.70:
            c_drowning = risk
            c_distress = 1.0 - risk
            c_normal   = 0.0
        elif risk >= 0.40:
            c_distress = risk
            c_drowning = max(0.0, risk - 0.40)
            c_normal   = 1.0 - c_distress - c_drowning
        else:
            c_normal   = 1.0 - risk
            c_distress = risk * 0.5
            c_drowning = 0.0

        total = c_normal + c_distress + c_drowning + 1e-9
        return c_normal/total, c_distress/total, c_drowning/total

    def _score_lstm(self, sequence: np.ndarray):
        import torch, torch.nn.functional as F
        self.lstm_model.eval()
        with torch.no_grad():
            x = torch.tensor(sequence, dtype=torch.float32).unsqueeze(0)
            logits = self.lstm_model(x)
            probs  = F.softmax(logits, dim=-1).squeeze(0).numpy()
        return float(probs[0]), float(probs[1]), float(probs[2])

    def behavior_label(self, c_normal, c_distress, c_drowning) -> str:
        if c_drowning >= 0.5:  return "drowning"
        if c_distress >= 0.4:  return "distress"
        return "normal"


# ============================================================
# Live Pipeline
# ============================================================

class LivePipeline:
    """
    Real-time drowning detection pipeline.

    Per-frame call:  result = pipeline.process_frame(frame, frame_number)
    Broadcast:       pipeline.to_broadcast_dict(result)  -> JSON-safe dict
    """
    def __init__(self, conf_threshold=0.35, sequence_length=32, lstm_model_path=None):
        self.conf_threshold  = conf_threshold
        self.sequence_length = sequence_length
        self.tracker         = PersonTracker(confidence=conf_threshold)
        self.scorer          = FeatureScorer()
        self.alert_engine    = AlertEngine(
            distress_confidence=0.55,
            drowning_confidence=0.75,
            consecutive_frames=5,
            cooldown_seconds=30,
        )
        self._extractors: Dict[int, TrackFeatureExtractor] = {}
        self._total_frames  = 0
        self._total_alerts  = 0
        self._start_time    = 0.0
        self._is_running    = False
        if lstm_model_path:
            self._load_lstm(lstm_model_path)

    # ---------- lifecycle ----------

    def start(self) -> bool:
        if self._is_running:
            return True
        ok = self.tracker.load()
        if not ok:
            logger.error("LivePipeline: tracker failed to load.")
            return False
        self._start_time = time.time()
        self._is_running = True
        logger.info("LivePipeline started (rule-based scorer).")
        return True

    def stop(self):
        self._is_running = False
        self._extractors.clear()
        logger.info("LivePipeline stopped.")

    # ---------- core ----------

    def process_frame(self, frame: np.ndarray, frame_number: int,
                      timestamp: Optional[float] = None,
                      annotate: bool = True) -> FrameResult:
        if not self._is_running:
            logger.warning("process_frame() called on stopped pipeline.")
            return FrameResult(frame_number, time.time(), [], 0, 0.0)

        t0 = time.perf_counter()
        ts = timestamp or time.time()
        self._total_frames += 1
        h, w = frame.shape[:2]
        output_frame = frame.copy() if annotate else None

        tracks, _ = self.tracker.track(frame, frame_number=frame_number)
        track_results: List[TrackFeatureResult] = []
        frame_has_alert = False

        for trk in tracks:
            if trk.track_id not in self._extractors:
                self._extractors[trk.track_id] = TrackFeatureExtractor(
                    track_id=trk.track_id, sequence_length=self.sequence_length)
            extractor = self._extractors[trk.track_id]

            fd = FrameData(frame_number=frame_number, timestamp=ts,
                           cx=trk.center_x, cy=trk.center_y,
                           w=trk.width, h=trk.height,
                           conf=trk.confidence, frame_w=w, frame_h=h)

            fv_obj = extractor.update(fd)
            fv_np  = fv_obj.to_numpy()

            c_normal, c_distress, c_drowning = self.scorer.score(fv_np)
            behavior = self.scorer.behavior_label(c_normal, c_distress, c_drowning)

            alert = self.alert_engine.process(
                track_id=trk.track_id, behavior=behavior,
                confidence_normal=c_normal,
                confidence_distress=c_distress,
                confidence_drowning=c_drowning)
            if alert:
                self._total_alerts += 1
                frame_has_alert = True

            seq_ready = extractor.history_length >= self.sequence_length
            tfr = TrackFeatureResult(
                track=trk, feature_vector=fv_np, sequence_ready=seq_ready,
                confidence_normal=c_normal, confidence_distress=c_distress,
                confidence_drowning=c_drowning, behavior_label=behavior, alert=alert)
            track_results.append(tfr)
            if annotate and output_frame is not None:
                self._annotate_track(output_frame, tfr)

        # Prune stale extractors
        active_ids = {t.track_id for t in tracks}
        for tid in [tid for tid in self._extractors if tid not in active_ids]:
            del self._extractors[tid]

        if annotate and output_frame is not None:
            self._draw_hud(output_frame, frame_number, len(tracks), frame_has_alert, w)

        return FrameResult(
            frame_number=frame_number, timestamp=ts, tracks=track_results,
            alert_count=sum(1 for t in track_results if t.alert),
            processing_ms=round((time.perf_counter() - t0)*1000, 1),
            annotated_frame=output_frame)

    # ---------- annotation ----------

    def _annotate_track(self, frame: np.ndarray, tfr: TrackFeatureResult):
        trk = tfr.track
        x1,y1,x2,y2 = int(trk.bbox_x1),int(trk.bbox_y1),int(trk.bbox_x2),int(trk.bbox_y2)
        color = (0,0,255) if tfr.behavior_label=="drowning" else \
                (0,140,255) if tfr.behavior_label=="distress" else (0,200,80)
        cv2.rectangle(frame,(x1,y1),(x2,y2),color,2)
        bar_w = x2-x1
        if bar_w>4:
            fill = int(bar_w*tfr.confidence_drowning) or int(bar_w*tfr.confidence_distress)
            bar_col = (0,0,255) if tfr.confidence_drowning>tfr.confidence_distress else (0,140,255)
            cv2.rectangle(frame,(x1,max(0,y1-5)),(x2,max(0,y1-2)),(50,50,50),-1)
            if fill:
                cv2.rectangle(frame,(x1,max(0,y1-5)),(x1+fill,max(0,y1-2)),bar_col,-1)
            else:
                cv2.rectangle(frame,(x1,max(0,y1-5)),(x2,max(0,y1-2)),(0,200,80),-1)
        lbl_map={"drowning":"DROWNING","distress":"DISTRESS","normal":"NORMAL"}
        label=f"ID:{trk.track_id} {lbl_map[tfr.behavior_label]} {trk.confidence:.2f}"
        (lw,lh),_=cv2.getTextSize(label,cv2.FONT_HERSHEY_SIMPLEX,0.44,1)
        ly=max(lh+2,y1-8)
        cv2.rectangle(frame,(x1,ly-lh-2),(x1+lw+4,ly+2),color,-1)
        cv2.putText(frame,label,(x1+2,ly),cv2.FONT_HERSHEY_SIMPLEX,0.44,(255,255,255),1,cv2.LINE_AA)

    def _draw_hud(self, frame, frame_no, n_tracks, has_alert, w):
        cv2.rectangle(frame,(8,8),(340,82),(10,10,10),-1)
        cv2.rectangle(frame,(8,8),(340,82),(0,180,212),1)
        uptime=time.time()-self._start_time
        fps=self._total_frames/max(uptime,0.001)
        lines=[f"AquaGuard AI | Frame:{frame_no}",
               f"Tracked:{n_tracks} | FPS:{fps:.1f}",
               f"Alerts:{self._total_alerts} | 16-D Features Active"]
        cols=[(0,255,255),(180,180,180),(150,200,150)]
        for i,(ln,co) in enumerate(zip(lines,cols)):
            cv2.putText(frame,ln,(18,28+i*18),cv2.FONT_HERSHEY_SIMPLEX,0.43,co,1,cv2.LINE_AA)
        if has_alert:
            bx1,bx2=w//2-210,w//2+210
            cv2.rectangle(frame,(bx1,8),(bx2,48),(0,0,200),-1)
            cv2.putText(frame,"!! CRITICAL: DROWNING RISK DETECTED !!",(bx1+10,34),
                        cv2.FONT_HERSHEY_SIMPLEX,0.60,(255,255,255),2,cv2.LINE_AA)

    # ---------- LSTM hot-swap ----------

    def _load_lstm(self, model_path: str):
        try:
            import torch
            from ai.temporal.lstm_model import BehaviorClassifier
            model=BehaviorClassifier(input_size=16)
            model.load_state_dict(torch.load(model_path, map_location="cpu"))
            model.eval()
            self.scorer.lstm_model=model
            logger.info(f"LSTM loaded from {model_path}")
        except Exception as e:
            logger.warning(f"LSTM load failed ({e}); using rule-based scorer.")

    # ---------- stats / broadcast ----------

    def get_stats(self):
        uptime=time.time()-self._start_time if self._is_running else 0.0
        return {
            "is_running":    self._is_running,
            "total_frames":  self._total_frames,
            "total_alerts":  self._total_alerts,
            "active_tracks": len(self._extractors),
            "uptime_seconds":round(uptime,1),
            "session_fps":   round(self._total_frames/max(uptime,0.001),1),
            "scorer_mode":   "lstm" if self.scorer.lstm_model else "rule-based",
        }

    def to_broadcast_dict(self, result: FrameResult):
        return {
            "type": "frame_result",
            "frame_number": result.frame_number,
            "timestamp":    result.timestamp,
            "processing_ms":result.processing_ms,
            "alert_count":  result.alert_count,
            "tracks":[{
                "track_id":  tfr.track.track_id,
                "bbox":      [tfr.track.bbox_x1,tfr.track.bbox_y1,
                              tfr.track.bbox_x2,tfr.track.bbox_y2],
                "center":    [tfr.track.center_x, tfr.track.center_y],
                "confidence":round(tfr.track.confidence,3),
                "behavior":  tfr.behavior_label,
                "c_normal":  round(tfr.confidence_normal,3),
                "c_distress":round(tfr.confidence_distress,3),
                "c_drowning":round(tfr.confidence_drowning,3),
                "feature_vector": tfr.feature_vector.tolist() if tfr.feature_vector is not None else None,
                "sequence_ready": tfr.sequence_ready,
                "alert":     tfr.alert,
            } for tfr in result.tracks],
            "stats": self.get_stats(),
        }
