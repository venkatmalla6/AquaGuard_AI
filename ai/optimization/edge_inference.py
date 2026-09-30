# AquaGuard AI - High Performance Edge Inference Engine (Phase 12)
from __future__ import annotations
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
from loguru import logger

root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

DEFAULT_CHECKPOINT = os.path.join(root_dir, 'ai', 'models', 'registry', 'best_model.pt')
DEFAULT_TORCHSCRIPT = os.path.join(root_dir, 'ai', 'models', 'registry', 'behavior_lstm.torchscript.pt')
DEFAULT_ONNX = os.path.join(root_dir, 'ai', 'models', 'registry', 'behavior_lstm.onnx')

def _softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    e_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
    return e_x / np.sum(e_x, axis=axis, keepdims=True)

class EdgeLSTMInference:
    BACKENDS = ('onnx', 'torchscript', 'pytorch')

    def __init__(
        self,
        backend: str = 'onnx',
        onnx_path: str = DEFAULT_ONNX,
        torchscript_path: str = DEFAULT_TORCHSCRIPT,
        pytorch_path: str = DEFAULT_CHECKPOINT,
        num_threads: Optional[int] = None
    ):
        self.preferred_backend = backend.lower()
        self.active_backend = None
        self.onnx_path = onnx_path
        self.torchscript_path = torchscript_path
        self.pytorch_path = pytorch_path
        self.num_threads = num_threads or max(1, (os.cpu_count() or 4) // 2)

        self._onnx_session = None
        self._onnx_input_name = None
        self._ts_model = None
        self._pytorch_model = None

        self._init_backend()

    def _init_backend(self):
        backend = self.preferred_backend

        if backend == 'onnx' and os.path.exists(self.onnx_path):
            try:
                import onnxruntime as ort
                opts = ort.SessionOptions()
                opts.intra_op_num_threads = self.num_threads
                opts.inter_op_num_threads = 1
                opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
                opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                self._onnx_session = ort.InferenceSession(
                    self.onnx_path,
                    sess_options=opts,
                    providers=['CPUExecutionProvider']
                )
                self._onnx_input_name = self._onnx_session.get_inputs()[0].name
                self.active_backend = 'onnx'
                logger.info(f'Edge LSTM Engine initialized with ONNX Runtime (threads={self.num_threads})')
                return
            except Exception as e:
                logger.warning(f'Failed to load ONNX backend ({e}), falling back to TorchScript.')

        if backend in ('onnx', 'torchscript') and os.path.exists(self.torchscript_path):
            try:
                import torch
                torch.set_num_threads(self.num_threads)
                self._ts_model = torch.jit.load(self.torchscript_path, map_location='cpu')
                self._ts_model.eval()
                self.active_backend = 'torchscript'
                logger.info(f'Edge LSTM Engine initialized with TorchScript (threads={self.num_threads})')
                return
            except Exception as e:
                logger.warning(f'Failed to load TorchScript backend ({e}), falling back to PyTorch.')

        # Fallback to standard PyTorch Eager
        from ai.optimization.model_exporter import load_trained_model
        self._pytorch_model, _ = load_trained_model(self.pytorch_path)
        self._pytorch_model.eval()
        self.active_backend = 'pytorch'
        logger.info('Edge LSTM Engine initialized with PyTorch Eager fallback')

    def predict_proba(self, sequence: np.ndarray) -> np.ndarray:
        if sequence.ndim == 2:
            x = np.expand_dims(sequence, axis=0).astype(np.float32)
            squeeze_output = True
        elif sequence.ndim == 3:
            x = sequence.astype(np.float32)
            squeeze_output = False
        else:
            raise ValueError(f'Expected sequence shape (seq_len, 16) or (batch, seq_len, 16), got {sequence.shape}')

        if self.active_backend == 'onnx':
            logits = self._onnx_session.run(None, {self._onnx_input_name: x})[0]
            probs = _softmax(logits, axis=-1)
        elif self.active_backend == 'torchscript':
            import torch
            with torch.no_grad():
                tensor_in = torch.from_numpy(x)
                logits = self._ts_model(tensor_in).numpy()
                probs = _softmax(logits, axis=-1)
        else:
            import torch
            with torch.no_grad():
                tensor_in = torch.from_numpy(x)
                logits = self._pytorch_model(tensor_in).numpy()
                probs = _softmax(logits, axis=-1)

        return probs[0] if squeeze_output else probs

    def score_single(self, sequence: np.ndarray) -> Tuple[float, float, float]:
        probs = self.predict_proba(sequence)
        return float(probs[0]), float(probs[1]), float(probs[2])

    @classmethod
    def benchmark_all(
        cls,
        iterations: int = 100,
        warmup: int = 15,
        batch_sizes: List[int] = [1, 4, 16],
        seq_len: int = 30,
        input_size: int = 16
    ) -> Dict[str, Any]:
        results = {}
        np.random.seed(42)

        # Initialize engines
        engines = {}
        for b in cls.BACKENDS:
            try:
                eng = cls(backend=b)
                if eng.active_backend == b:
                    engines[b] = eng
            except Exception as err:
                logger.warning(f'Could not load {b} for benchmark: {err}')

        for batch in batch_sizes:
            test_data = np.random.randn(batch, seq_len, input_size).astype(np.float32)
            batch_res = {}

            for name, eng in engines.items():
                # Warmup
                for _ in range(warmup):
                    eng.predict_proba(test_data)

                # Timing
                latencies = []
                for _ in range(iterations):
                    t0 = time.perf_counter()
                    eng.predict_proba(test_data)
                    latencies.append((time.perf_counter() - t0) * 1000.0)

                lat_arr = np.array(latencies)
                mean_ms = float(np.mean(lat_arr))
                std_ms = float(np.std(lat_arr))
                p50 = float(np.percentile(lat_arr, 50))
                p95 = float(np.percentile(lat_arr, 95))
                p99 = float(np.percentile(lat_arr, 99))
                throughput = float((batch * 1000.0) / mean_ms) if mean_ms > 0 else 0.0

                batch_res[name] = {
                    'mean_ms': round(mean_ms, 3),
                    'std_ms': round(std_ms, 3),
                    'p50_ms': round(p50, 3),
                    'p95_ms': round(p95, 3),
                    'p99_ms': round(p99, 3),
                    'min_ms': round(float(np.min(lat_arr)), 3),
                    'max_ms': round(float(np.max(lat_arr)), 3),
                    'throughput_samples_per_sec': round(throughput, 1)
                }

            # Calculate relative speedups vs PyTorch
            py_mean = batch_res.get('pytorch', {}).get('mean_ms', 1.0)
            for name in batch_res:
                speedup = round(py_mean / batch_res[name]['mean_ms'], 2) if batch_res[name]['mean_ms'] > 0 else 1.0
                batch_res[name]['speedup_vs_pytorch'] = speedup

            results[f'batch_{batch}'] = batch_res

        return {
            'benchmark_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'iterations': iterations,
            'warmup': warmup,
            'results': results,
            'summary': {
                'recommended_backend': 'onnx' if 'onnx' in engines else 'torchscript',
                'tested_backends': list(engines.keys())
            }
        }

if __name__ == '__main__':
    eng = EdgeLSTMInference(backend='onnx')
    dummy = np.random.randn(30, 16)
    p_norm, p_dist, p_drown = eng.score_single(dummy)
    print(f'Test prediction: normal={p_norm:.4f}, distress={p_dist:.4f}, drowning={p_drown:.4f}')

    print('Running quick benchmark...')
    bench = EdgeLSTMInference.benchmark_all(iterations=30, warmup=5, batch_sizes=[1, 4])
    import json
    print(json.dumps(bench, indent=2))
