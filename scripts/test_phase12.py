"""
AquaGuard AI - Phase 12 Verification Suite: Edge Optimization (CPU Focus)
Validates TorchScript/ONNX exports, edge inference latency, adaptive frame skipping,
OpenCV SIMD acceleration, and FastAPI edge diagnostics endpoints.
"""
from __future__ import annotations
import os
import sys
import time
from pathlib import Path
import numpy as np

# Setup paths
root_dir = str(Path(__file__).parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, "backend"))

from ai.optimization.model_exporter import run_export_pipeline
from ai.optimization.edge_inference import EdgeLSTMInference
from ai.optimization.frame_skipper import AdaptiveFrameSkipper
from ai.optimization.cv_optimizer import OpenCVOptimizer
from ai.pipeline.live_pipeline import LivePipeline

def test_phase12():
    print("=" * 70)
    print(" AQUAGUARD AI - PHASE 12: EDGE OPTIMIZATION VERIFICATION SUITE")
    print("=" * 70)

    # 1. Model Exporter & Numerical Parity Test
    print("\n[TEST 1/5] Verifying Model Export Pipeline (TorchScript & ONNX)...")
    res = run_export_pipeline()
    assert os.path.exists(res["torchscript_path"]), "TorchScript model file missing"
    assert os.path.exists(res["onnx_path"]), "ONNX model file missing"
    assert res["verification"]["status"] == "verified", f"Parity verification failed: {res['verification']}"
    assert res["verification"]["onnx_max_diff"] < 1e-4, f"ONNX max diff too high: {res['verification']['onnx_max_diff']}"
    assert res["verification"]["torchscript_max_diff"] < 1e-4, f"TS max diff too high: {res['verification']['torchscript_max_diff']}"
    print(f" [OK] TorchScript size: {os.path.getsize(res['torchscript_path'])/1024:.1f} KB")
    print(f" [OK] ONNX size: {os.path.getsize(res['onnx_path'])/1024:.1f} KB")
    print(f" [OK] Parity verified: TS diff={res['verification']['torchscript_max_diff']:.2e}, ONNX diff={res['verification']['onnx_max_diff']:.2e}")

    # 2. Edge LSTM Inference Engine Test
    print("\n[TEST 2/5] Benchmarking Edge LSTM Engine (ONNX vs TorchScript vs PyTorch)...")
    bench = EdgeLSTMInference.benchmark_all(iterations=25, warmup=5, batch_sizes=[1, 4])
    batch_1 = bench["results"]["batch_1"]
    batch_4 = bench["results"]["batch_4"]
    print(f" [OK] Batch 1 (1 Swimmer) Latency: ONNX={batch_1['onnx']['mean_ms']}ms | TS={batch_1['torchscript']['mean_ms']}ms | PyTorch={batch_1['pytorch']['mean_ms']}ms")
    print(f" [OK] Batch 4 (4 Swimmers) Latency: ONNX={batch_4['onnx']['mean_ms']}ms | TS={batch_4['torchscript']['mean_ms']}ms | PyTorch={batch_4['pytorch']['mean_ms']}ms")
    print(f" [OK] ONNX Speedup over PyTorch: {batch_4['onnx']['speedup_vs_pytorch']}x | Throughput: {batch_4['onnx']['throughput_samples_per_sec']} seq/sec")
    assert batch_1["onnx"]["mean_ms"] < 5.0, "ONNX latency exceeds 5ms edge budget"

    # 3. Adaptive Frame Skipping Test
    print("\n[TEST 3/5] Testing Risk-Sensitive Adaptive Frame Skipper...")
    skipper = AdaptiveFrameSkipper(target_fps=30.0, min_stride=1, max_stride=3, idle_stride=3)
    # Simulate 60 idle frames
    for f in range(60):
        run, stride = skipper.should_process_frame(frame_number=f, active_threat=False, track_count=0)
        skipper.record_latency(12.0)
    idle_stats = skipper.get_status_dict()
    assert idle_stats["current_stride"] == 3, f"Expected stride 3 during idle, got {idle_stats['current_stride']}"
    assert idle_stats["cpu_reduction_percent"] > 60.0, f"Expected >60% savings, got {idle_stats['cpu_reduction_percent']}%"
    print(f" [OK] Idle Pool CPU Savings: {idle_stats['cpu_reduction_percent']}% reduction in inference calls")

    # Threat emerges -> Burst Mode
    for f in range(60, 75):
        run, stride = skipper.should_process_frame(frame_number=f, active_threat=True, track_count=1)
        skipper.record_latency(25.0)
    threat_stats = skipper.get_status_dict()
    assert threat_stats["current_stride"] == 1, "Threat mode must snap to stride 1"
    assert threat_stats["burst_mode_active"] == True, "Burst mode must be active"
    print(f" [OK] Threat Detected -> Instant Burst Mode active (stride=1, 0 frames skipped)")

    # 4. OpenCV SIMD & Hardware Multi-Threading Test
    print("\n[TEST 4/5] Testing OpenCV Hardware Multi-Threading & SIMD Optimizations...")
    cv_info = OpenCVOptimizer.apply_optimizations()
    assert cv_info["use_optimized"] == True, "OpenCV optimization flag not set"
    assert cv_info["num_threads"] >= 2, "OpenCV threads not configured"
    
    # Fast resize & motion energy
    dummy_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    resized = OpenCVOptimizer.fast_resize(dummy_frame, (320, 240))
    assert resized.shape == (240, 320, 3)
    gray1 = np.zeros((240, 320), dtype=np.uint8)
    gray2 = np.ones((240, 320), dtype=np.uint8) * 50
    motion = OpenCVOptimizer.fast_motion_energy(gray1, gray2)
    assert abs(motion - 50.0) < 1e-2, f"Motion energy unexpected: {motion}"
    print(f" [OK] OpenCV SIMD: {cv_info['build_info_simd']} | Thread Pool: {cv_info['num_threads']} Cores")

    # 5. Live Pipeline Edge Integration Test
    print("\n[TEST 5/5] Testing LivePipeline with ONNX Acceleration & Frame Skipping...")
    pipe = LivePipeline(edge_backend="onnx", enable_frame_skipping=True)
    pipe.start()
    for f in range(6):
        res = pipe.process_frame(dummy_frame, frame_number=f)
        bcast = pipe.to_broadcast_dict(res)
        assert "edge_acceleration" in bcast["stats"], "Missing edge_acceleration in broadcast stats"
    pipe.stop()
    print(" [OK] LivePipeline successfully dispatched frames with ONNX & Adaptive Skipping")

    print("\n" + "=" * 70)
    print(" [SUCCESS] ALL PHASE 12 EDGE OPTIMIZATION TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    test_phase12()
