"""
AquaGuard AI - 16-D Feature Extractor & Alert Engine CV Tests
"""
import pytest
import numpy as np
from ai.features.feature_extractor import TrackFeatureExtractor, FrameData
from ai.pipeline.live_pipeline import FeatureScorer
from ai.evaluation.alert_engine import AlertEngine, AlertLevel

def test_feature_extractor_update():
    """Test 16-D feature extraction from sequential tracking points."""
    extractor = TrackFeatureExtractor(track_id=1, sequence_length=30)
    for i in range(10):
        fd = FrameData(
            frame_number=i,
            timestamp=1000.0 + i * 0.033,
            cx=100.0 + i * 2.0,
            cy=200.0 + i * 1.5,
            w=50.0,
            h=80.0,
            conf=0.9,
            frame_w=640,
            frame_h=480
        )
        fv = extractor.update(fd)

    np_fv = fv.to_numpy()
    assert len(np_fv) == 16
    assert 0.0 <= np_fv[0] <= 1.0  # cx_norm
    assert 0.0 <= np_fv[1] <= 1.0  # cy_norm
    assert np_fv[9] > 0.0          # speed

def test_feature_scorer_classification(synthetic_drowning_features: np.ndarray, synthetic_normal_features: np.ndarray):
    """Test rule-based and neural behavior scoring."""
    scorer = FeatureScorer(edge_backend="rules")
    
    # Normal swimmer
    c_norm, c_dist, c_drown = scorer.score(synthetic_normal_features)
    assert c_norm > c_drown
    assert scorer.behavior_label(c_norm, c_dist, c_drown) == "normal"

    # Drowning victim
    c_norm_d, c_dist_d, c_drown_d = scorer.score(synthetic_drowning_features)
    assert c_drown_d > 0.5
    assert scorer.behavior_label(c_norm_d, c_dist_d, c_drown_d) == "drowning"

def test_alert_engine_hysteresis():
    """Test alert engine persistence frames and cooldown trigger."""
    engine = AlertEngine(
        distress_confidence=0.5,
        drowning_confidence=0.7,
        consecutive_frames=3,
        cooldown_seconds=10
    )

    # Frame 1: Drowning detected but under persistence threshold (consecutive_frames=3)
    a1 = engine.process(track_id=42, behavior="drowning", confidence_normal=0.0, confidence_distress=0.1, confidence_drowning=0.9)
    assert a1 is None, "Alert triggered prematurely before persistence threshold"

    # Frame 2
    a2 = engine.process(track_id=42, behavior="drowning", confidence_normal=0.0, confidence_distress=0.1, confidence_drowning=0.9)
    assert a2 is None

    # Frame 3: Threshold met -> Trigger ALERT!
    a3 = engine.process(track_id=42, behavior="drowning", confidence_normal=0.0, confidence_distress=0.1, confidence_drowning=0.9)
    assert a3 is not None
    assert a3["level"] == AlertLevel.CRITICAL.value

    # Frame 4: Immediate cooldown suppression
    a4 = engine.process(track_id=42, behavior="drowning", confidence_normal=0.0, confidence_distress=0.1, confidence_drowning=0.9)
    assert a4 is None, "Cooldown must suppress redundant alert storm"
