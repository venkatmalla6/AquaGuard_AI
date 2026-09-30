from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
import torch
from loguru import logger

root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from ai.temporal.lstm_model import BehaviorClassifier

DEFAULT_CHECKPOINT = os.path.join(root_dir, 'ai', 'models', 'registry', 'best_model.pt')
DEFAULT_TORCHSCRIPT = os.path.join(root_dir, 'ai', 'models', 'registry', 'behavior_lstm.torchscript.pt')
DEFAULT_ONNX = os.path.join(root_dir, 'ai', 'models', 'registry', 'behavior_lstm.onnx')

def load_trained_model(checkpoint_path: str = DEFAULT_CHECKPOINT) -> Tuple[BehaviorClassifier, Dict[str, Any]]:
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f'Checkpoint not found at: {checkpoint_path}')

    ckpt = torch.load(checkpoint_path, map_location='cpu')
    config = ckpt.get('config', {})
    
    input_size = config.get('input_size', 16)
    hidden_size = config.get('hidden_size', 128)
    num_layers = config.get('num_layers', 2)
    num_classes = config.get('num_classes', 3)
    dropout = config.get('dropout', 0.3)
    model_type = config.get('model_type', 'lstm')

    model = BehaviorClassifier(
        input_size=input_size,
        hidden_size=hidden_size,
        num_layers=num_layers,
        num_classes=num_classes,
        dropout=dropout,
        model_type=model_type
    )

    state_dict = ckpt.get('model_state', ckpt.get('state_dict', ckpt))
    model.load_state_dict(state_dict)
    model.eval()
    logger.info(f'Loaded BehaviorClassifier from {checkpoint_path}')
    return model, config

def export_to_torchscript(
    model: BehaviorClassifier,
    output_path: str = DEFAULT_TORCHSCRIPT,
    seq_len: int = 30,
    input_size: int = 16
) -> str:
    model.eval()
    dummy_input = torch.randn(1, seq_len, input_size, dtype=torch.float32)

    with torch.no_grad():
        traced_model = torch.jit.trace(model, dummy_input)
        optimized_model = torch.jit.freeze(traced_model)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    optimized_model.save(output_path)
    file_size_kb = os.path.getsize(output_path) / 1024
    logger.info(f'Exported TorchScript model to {output_path} ({file_size_kb:.1f} KB)')
    return output_path

def export_to_onnx(
    model: BehaviorClassifier,
    output_path: str = DEFAULT_ONNX,
    seq_len: int = 30,
    input_size: int = 16,
    opset_version: int = 17
) -> str:
    import onnx
    model.eval()
    dummy_input = torch.randn(1, seq_len, input_size, dtype=torch.float32)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=['feature_sequence'],
        output_names=['logits'],
        dynamic_axes={
            'feature_sequence': {0: 'batch_size'},
            'logits': {0: 'batch_size'}
        },
        dynamo=False
    )

    onnx_model = onnx.load(output_path)
    onnx.checker.check_model(onnx_model)
    file_size_kb = os.path.getsize(output_path) / 1024
    logger.info(f'Exported and validated ONNX model at {output_path} ({file_size_kb:.1f} KB)')
    return output_path

def verify_exports(
    checkpoint_path: str = DEFAULT_CHECKPOINT,
    torchscript_path: str = DEFAULT_TORCHSCRIPT,
    onnx_path: str = DEFAULT_ONNX,
    batch_size: int = 4,
    seq_len: int = 30,
    input_size: int = 16
) -> Dict[str, Any]:
    import onnxruntime as ort

    model, _ = load_trained_model(checkpoint_path)
    model.eval()

    np.random.seed(42)
    test_np = np.random.randn(batch_size, seq_len, input_size).astype(np.float32)
    test_tensor = torch.from_numpy(test_np)

    with torch.no_grad():
        pytorch_logits = model(test_tensor).numpy()

    ts_model = torch.jit.load(torchscript_path)
    ts_model.eval()
    with torch.no_grad():
        ts_logits = ts_model(test_tensor).numpy()

    ort_session = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
    input_name = ort_session.get_inputs()[0].name
    ort_outputs = ort_session.run(None, {input_name: test_np})
    onnx_logits = ort_outputs[0]

    ts_diff = float(np.max(np.abs(pytorch_logits - ts_logits)))
    onnx_diff = float(np.max(np.abs(pytorch_logits - onnx_logits)))

    ts_verified = ts_diff < 1e-4
    onnx_verified = onnx_diff < 1e-4

    results = {
        'status': 'verified' if (ts_verified and onnx_verified) else 'error',
        'torchscript_verified': ts_verified,
        'torchscript_max_diff': ts_diff,
        'onnx_verified': onnx_verified,
        'onnx_max_diff': onnx_diff,
        'batch_size': batch_size,
        'sequence_length': seq_len,
        'pytorch_shape': list(pytorch_logits.shape),
        'onnx_shape': list(onnx_logits.shape)
    }

    logger.info(f'Verification Results: TS max diff={ts_diff:.2e}, ONNX max diff={onnx_diff:.2e}')
    return results

def run_export_pipeline() -> Dict[str, Any]:
    model, config = load_trained_model()
    ts_path = export_to_torchscript(model)
    onnx_path = export_to_onnx(model)
    verification = verify_exports()
    return {
        'torchscript_path': ts_path,
        'onnx_path': onnx_path,
        'verification': verification
    }

if __name__ == '__main__':
    res = run_export_pipeline()
    print('Export Pipeline Complete:', res)
