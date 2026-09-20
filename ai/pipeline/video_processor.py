# AquaGuard AI - Video File Processor
# Phase 6 Upgrade: 16-D Feature Integration
"""
Processes a video file frame-by-frame using:
  ByteTrack person tracking -> TrackFeatureExtractor (16-D) -> FeatureScorer -> annotation

WHY this module is separate from live_pipeline.py:
  - File processing is synchronous, blocking, CPU-intensive.
  - Live pipeline is designed for async/real-time frame dispatch.
  - Both share the same FeatureScorer and TrackFeatureExtractor internals.
"""
from dataclasses import dataclass
from pathlib import Path
import sys, time
from typing import Callable, Optional, Dict, Any, List
import cv2, numpy as np
from loguru import logger

root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from ai.tracking.tracker import PersonTracker, TrackResult
from ai.features.feature_extractor import TrackFeatureExtractor, FrameData
from ai.pipeline.live_pipeline import FeatureScorer
from ai.evaluation.alert_engine import AlertEngine


@dataclass
class VideoMetadata:
    duration_seconds: float
    fps: float
    total_frames: int
    resolution_width: int
    resolution_height: int


def extract_video_metadata(filepath: str) -> VideoMetadata:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {filepath}")
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"OpenCV could not open video file: {filepath}")
    try:
        fps         = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames= int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width       = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)  or 1280)
        height      = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)
        duration    = total_frames / fps if fps > 0 else 0.0
        return VideoMetadata(round(duration,2), round(fps,2), total_frames, width, height)
    finally:
        cap.release()


class VideoProcessor:
    """
    Synchronous video processor for uploaded files.

    Processing stack:
      OpenCV reader -> PersonTracker (ByteTrack) -> TrackFeatureExtractor (16-D)
      -> FeatureScorer (rule-based / LSTM) -> AlertEngine -> annotated output

    WHY FeatureScorer here vs posture heuristic (Phase 5):
      The Phase 5 posture heuristic (width/height < 0.6) only uses 1 dimension.
      The 16-D feature vector integrates temporal motion, velocity, inactivity,
      and aspect ratio — producing research-grade behavioral features that match
      the MASTER_REFERENCE specification.
    """
    def __init__(self, conf_threshold=0.35, sequence_length=32):
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

    def _get_color(self, label: str):
        return (0,0,255) if label=="drowning" else \
               (0,140,255) if label=="distress" else (0,200,80)

    def process_file(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int,int,float],None]] = None,
        frame_interval: int = 1,
    ) -> Dict[str, Any]:
        """
        Process video file and write annotated output.
        Returns analysis statistics dict.
        """
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open input video: {input_path}")

        fps         = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames= int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width       = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)  or 1280)
        height      = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)

        # Lazy-load tracker model
        if not self.tracker._is_loaded:
            self.tracker.load()

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out    = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        frame_count      = 0
        unique_track_ids = set()
        alert_events     = 0
        drowning_frames  = 0
        distress_frames  = 0
        normal_frames    = 0
        start_time       = time.time()

        # Per-track feature extractors (track_id -> TrackFeatureExtractor)
        extractors: Dict[int, TrackFeatureExtractor] = {}

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                frame_count += 1

                # -- Tracking --
                tracks, _ = self.tracker.track(frame, frame_number=frame_count)

                frame_has_alert = False
                frame_dominant  = "normal"
                max_risk        = 0.0

                for trk in tracks:
                    unique_track_ids.add(trk.track_id)

                    # Lazy-create per-track extractor
                    if trk.track_id not in extractors:
                        extractors[trk.track_id] = TrackFeatureExtractor(
                            track_id=trk.track_id,
                            sequence_length=self.sequence_length)
                    ext = extractors[trk.track_id]

                    # Build FrameData
                    fd = FrameData(
                        frame_number=frame_count,
                        timestamp=time.time(),
                        cx=trk.center_x, cy=trk.center_y,
                        w=trk.width, h=trk.height,
                        conf=trk.confidence,
                        frame_w=width, frame_h=height)

                    # Compute 16-D features
                    fv_np = ext.update(fd).to_numpy()

                    # Score
                    c_norm, c_dist, c_drown = self.scorer.score(fv_np)
                    behavior = self.scorer.behavior_label(c_norm, c_dist, c_drown)

                    # Alert engine
                    alert = self.alert_engine.process(
                        track_id=trk.track_id, behavior=behavior,
                        confidence_normal=c_norm,
                        confidence_distress=c_dist,
                        confidence_drowning=c_drown)
                    if alert:
                        alert_events += 1
                        frame_has_alert = True

                    # Track dominant risk
                    risk = c_drown*1.0 + c_dist*0.5
                    if risk > max_risk:
                        max_risk = risk
                        frame_dominant = behavior

                    # -- Annotation --
                    color = self._get_color(behavior)
                    x1,y1 = int(trk.bbox_x1),int(trk.bbox_y1)
                    x2,y2 = int(trk.bbox_x2),int(trk.bbox_y2)
                    cv2.rectangle(frame,(x1,y1),(x2,y2),color,2)

                    # Confidence micro-bar above bbox
                    bar_w = x2-x1
                    if bar_w>4:
                        fill=int(bar_w*c_drown) or int(bar_w*c_dist)
                        bcol=(0,0,255) if c_drown>c_dist else (0,140,255)
                        cv2.rectangle(frame,(x1,max(0,y1-5)),(x2,max(0,y1-2)),(50,50,50),-1)
                        if fill:
                            cv2.rectangle(frame,(x1,max(0,y1-5)),(x1+fill,max(0,y1-2)),bcol,-1)
                        else:
                            cv2.rectangle(frame,(x1,max(0,y1-5)),(x2,max(0,y1-2)),(0,200,80),-1)

                    lbl_map={"drowning":"DROWNING","distress":"DISTRESS","normal":"NORMAL"}
                    label=f"ID:{trk.track_id} {lbl_map[behavior]} {trk.confidence:.2f}"
                    (lw,lh),_=cv2.getTextSize(label,cv2.FONT_HERSHEY_SIMPLEX,0.44,1)
                    ly=max(lh+2,y1-8)
                    cv2.rectangle(frame,(x1,ly-lh-2),(x1+lw+4,ly+2),color,-1)
                    cv2.putText(frame,label,(x1+2,ly),cv2.FONT_HERSHEY_SIMPLEX,
                                0.44,(255,255,255),1,cv2.LINE_AA)

                # Track frame-level behavior counts
                if frame_dominant=="drowning":   drowning_frames+=1
                elif frame_dominant=="distress": distress_frames+=1
                else:                            normal_frames+=1

                # Prune stale extractors
                active_ids={t.track_id for t in tracks}
                for tid in [tid for tid in extractors if tid not in active_ids]:
                    del extractors[tid]

                # HUD
                cv2.rectangle(frame,(8,8),(340,82),(10,10,10),-1)
                cv2.rectangle(frame,(8,8),(340,82),(0,180,212),1)
                elapsed=time.time()-start_time
                proc_fps=frame_count/elapsed if elapsed>0 else 0
                hud=[f"AquaGuard AI | Frame:{frame_count}/{total_frames}",
                     f"Active:{len(tracks)} Tracked:{len(unique_track_ids)}",
                     f"Alerts:{alert_events} | 16-D Feat | {proc_fps:.1f} FPS"]
                hud_c=[(0,255,255),(180,180,180),(150,200,150)]
                for i,(l,c) in enumerate(zip(hud,hud_c)):
                    cv2.putText(frame,l,(18,28+i*18),cv2.FONT_HERSHEY_SIMPLEX,0.43,c,1,cv2.LINE_AA)

                if frame_has_alert:
                    bx1,bx2=width//2-210,width//2+210
                    cv2.rectangle(frame,(bx1,8),(bx2,48),(0,0,200),-1)
                    cv2.putText(frame,"!! CRITICAL: DROWNING RISK !!",(bx1+20,34),
                                cv2.FONT_HERSHEY_SIMPLEX,0.65,(255,255,255),2,cv2.LINE_AA)

                out.write(frame)

                if progress_callback and (frame_count%10==0 or frame_count==total_frames):
                    pct=round((frame_count/total_frames)*100,1) if total_frames>0 else 0.0
                    progress_callback(frame_count, total_frames, pct)

        finally:
            cap.release()
            out.release()

        elapsed=time.time()-start_time
        return {
            "total_frames_processed":  frame_count,
            "unique_swimmers_tracked": len(unique_track_ids),
            "alert_events_count":      alert_events,
            "drowning_frames":         drowning_frames,
            "distress_frames":         distress_frames,
            "normal_frames":           normal_frames,
            "processing_time_seconds": round(elapsed,2),
            "average_processing_fps":  round(frame_count/elapsed,1) if elapsed>0 else 0.0,
            "output_video_path":       output_path,
            "feature_dimensions":      16,
            "scorer_mode":             "lstm" if self.scorer.lstm_model else "rule-based",
        }
