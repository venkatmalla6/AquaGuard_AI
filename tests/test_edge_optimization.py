"""
AquaGuard AI - Edge AI Optimization Unit Tests (Phase 13)
"""
import os
import pytest
import numpy as np
from ai.optimization.edge_inference import EdgeLSTMInference
from ai.optimization.frame_skipper import AdaptiveFrameSkipper
from ai.optimization.cv_optimizer import OpenCVOptimizer
from ai.optimization.model_exporter import DEFAULT_ONNX, DEFAULT_TORCHSCRIPT

def test_onnx_model_inference():
    """Test ONNX Runtime CPU inference correctness and output probabilities."""
    assert os.path.exists(DEFAULT_ONNX), "ONNX model artifact must exist"
    engine = EdgeLSTMInference(backend="onnx")
    assert engine.active_backend == "onnx"

    seq = np.random.randn(30, 16).astype(np.float32)
    probs = engine.predict_proba(seq)
    assert probs.shape == (3,)
    assert abs(float(np.sum(probs)) - 1.0) < 1e-4

def test_torchscript_model_inference():
    """Test TorchScript JIT inference correctness."""
    assert os.path.exists(DEFAULT_TORCHSCRIPT), "TorchScript model artifact must exist"
    engine = EdgeLSTMInference(backend="torchscript")
    assert engine.active_backend == "torchscript"

    batch = np.random.randn(4, 30, 16).astype(np.float32)
    probs = engine.predict_proba(batch)
    assert probs.shape == (4, 3)

def test_adaptive_frame_skipper_logic():
    """Test dynamic stride transitions and threat override."""
    skipper = AdaptiveFrameSkipper(target_fps=30.0, min_stride=1, max_stride=4, idle_stride=3)
    
    # Idle pool simulation
    for f in range(30):
        process, stride = skipper.should_process_frame(frame_number=f, active_threat=False, track_count=0)
    stats = skipper.get_status_dict()
    assert stats["current_stride"] == 3
    assert stats["cpu_reduction_percent"] >= 60.0

    # Threat burst
    process, stride = skipper.should_process_frame(frame_number=31, active_threat=True, track_count=1)
    assert stride == 1
    assert process is True

def test_opencv_optimizer():
    """Test OpenCV SIMD initialization and multi-threading."""
    info = OpenCVOptimizer.apply_optimizations()
    assert info["use_optimized"] is True
    assert info["num_threads"] >= 2
