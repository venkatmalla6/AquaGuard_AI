#!/usr/bin/env python3
"""
AquaGuard AI - Phase 6 Integration Test
Tests: TrackFeatureExtractor (16-D), FeatureScorer, AlertEngine, broadcast dict

Run: python scripts/test_live_pipeline.py
"""
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def test_feature_extractor():
    print("\n[1] Testing TrackFeatureExtractor (16-D)...")
    from ai.features.feature_extractor import TrackFeatureExtractor, FrameData
    ext = TrackFeatureExtractor(track_id=1, sequence_length=32)
    for i in range(35):
        fd = FrameData(
            frame_number=i, timestamp=float(i)/30.0,
            cx=320+i*0.5, cy=200+np.sin(i/5)*10,
            w=80, h=120, conf=0.85, frame_w=640, frame_h=360)
        fv = ext.update(fd)
        vec = fv.to_numpy()
        assert vec.shape == (16,), f"Expected 16 features, got {vec.shape}"
    seq = ext.get_sequence()
    assert seq is not None, "Sequence should be ready after 35 frames"
    assert seq.shape == (32,16), f"Sequence shape wrong: {seq.shape}"
    print(f"   PASS  Feature dim=16, sequence shape={seq.shape}")
    return True


def test_feature_scorer():
    print("\n[2] Testing FeatureScorer rule-based scoring...")
    from ai.pipeline.live_pipeline import FeatureScorer
    scorer = FeatureScorer()

    # Drowning: ALL signals max — inactivity, narrow aspect, high variance, vertical
    drown_fv = np.zeros(16, dtype=np.float32)
    drown_fv[4]  = 0.2   # aspect_ratio (very narrow -> vertical sinking posture)
    drown_fv[9]  = 0.1   # speed (near zero)
    drown_fv[13] = 600.0 # movement_variance (thrashing)
    drown_fv[14] = 0.9   # vertical_ratio (mostly vertical displacement)
    drown_fv[15] = 1.0   # inactivity flag
    c_n, c_d, c_drown = scorer.score(drown_fv)
    label = scorer.behavior_label(c_n, c_d, c_drown)
    print(f"   Drowning: normal={c_n:.3f} distress={c_d:.3f} drowning={c_drown:.3f} -> {label}")
    # With all signals active, risk >= 0.70 -> drowning confidence must exceed normal
    assert (c_drown + c_d) > c_n, "Drowning/distress signals must dominate normal confidence"

    # Normal: wide aspect, active speed
    norm_fv = np.zeros(16, dtype=np.float32)
    norm_fv[4]  = 1.8   # aspect_ratio (wide -> swimming)
    norm_fv[9]  = 15.0  # speed (active)
    norm_fv[15] = 0.0   # active
    c_n2, c_d2, c_drown2 = scorer.score(norm_fv)
    label2 = scorer.behavior_label(c_n2, c_d2, c_drown2)
    print(f"   Normal:   normal={c_n2:.3f} distress={c_d2:.3f} drowning={c_drown2:.3f} -> {label2}")
    assert c_n2 > c_drown2, "Normal scenario must score higher normal confidence"
    print("   PASS  Rule-based scorer produces correct relative confidences")
    return True


def test_alert_engine():
    print("\n[3] Testing AlertEngine consecutive-frame filter...")
    from ai.evaluation.alert_engine import AlertEngine
    eng = AlertEngine(
        distress_confidence=0.55, drowning_confidence=0.75,
        consecutive_frames=3, cooldown_seconds=0)

    for i in range(2):
        r = eng.process(1, "drowning", 0.0, 0.05, 0.92)
        assert r is None, f"Alert should not fire before {3} consecutive frames"

    alert = eng.process(1, "drowning", 0.0, 0.05, 0.92)
    assert alert is not None, "Alert must fire at consecutive_frames=3"
    assert alert["level"] == "critical", f"Expected critical, got {alert['level']}"
    print(f"   PASS  Alert fired at frame 3, level={alert['level']}")
    return True


def test_broadcast_dict():
    print("\n[4] Testing to_broadcast_dict JSON serialisation...")
    from ai.pipeline.live_pipeline import LivePipeline, FrameResult, TrackFeatureResult, FeatureScorer
    from ai.tracking.tracker import TrackResult

    trk = TrackResult(track_id=5, bbox_x1=100, bbox_y1=80, bbox_x2=180, bbox_y2=240, confidence=0.88)
    fv  = np.random.rand(16).astype(np.float32)
    tfr = TrackFeatureResult(
        track=trk, feature_vector=fv, sequence_ready=True,
        confidence_normal=0.05, confidence_distress=0.15,
        confidence_drowning=0.80, behavior_label="drowning")
    result = FrameResult(frame_number=42, timestamp=1234567890.0,
                         tracks=[tfr], alert_count=0, processing_ms=18.5)

    # Build pipeline stub without loading YOLO
    pipeline = object.__new__(LivePipeline)
    pipeline._total_frames = 100
    pipeline._total_alerts = 2
    pipeline._extractors   = {}
    pipeline._start_time   = 0.0
    pipeline._is_running   = True
    pipeline.scorer        = FeatureScorer()

    d = pipeline.to_broadcast_dict(result)
    assert d["type"] == "frame_result"
    assert len(d["tracks"]) == 1
    assert len(d["tracks"][0]["feature_vector"]) == 16
    assert d["tracks"][0]["behavior"] == "drowning"
    print(f"   PASS  broadcast_dict keys={list(d.keys())}")
    print(f"         feature_vector length={len(d['tracks'][0]['feature_vector'])}")
    return True


def test_16d_feature_names():
    print("\n[5] Verifying 16-D feature name index alignment...")
    from ai.pipeline.live_pipeline import FeatureScorer
    from ai.features.feature_extractor import TemporalFeatureVector
    scorer_keys = list(FeatureScorer.FEATURE_IDX.keys())
    expected_order = [
        "cx_norm","cy_norm","w_norm","h_norm","aspect_ratio","area_norm",
        "displacement","velocity_x","velocity_y","speed","acceleration",
        "direction_sin","direction_cos","movement_variance","vertical_ratio","inactivity",
    ]
    assert scorer_keys == expected_order, f"Feature index mismatch:\n  got:      {scorer_keys}\n  expected: {expected_order}"
    assert len(expected_order) == TemporalFeatureVector.NUM_FEATURES == 16
    print(f"   PASS  All 16 feature names match TemporalFeatureVector order")
    return True


def main():
    print("=" * 62)
    print(" AquaGuard AI - Phase 6 Integration Tests")
    print("=" * 62)
    tests = [test_feature_extractor, test_feature_scorer,
             test_alert_engine, test_broadcast_dict, test_16d_feature_names]
    results = []
    for fn in tests:
        try:
            ok = fn()
            results.append((fn.__name__, True, None))
        except Exception as e:
            results.append((fn.__name__, False, str(e)))
            print(f"   FAIL  {fn.__name__}: {e}")

    print("\n" + "=" * 62)
    passed = sum(1 for _, ok, _ in results if ok)
    print(f" Results: {passed}/{len(results)} tests passed")
    for name, ok, err in results:
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {name}" + (f"  -- {err}" if err else ""))
    print("=" * 62)
    return passed == len(results)


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)

