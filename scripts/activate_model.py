#!/usr/bin/env python3
"""
AquaGuard AI - Activate Trained LSTM in Live Pipeline
Copies best_model.pt to ai/models/registry/ so LivePipeline auto-loads it.
Run after training to upgrade the scorer from rule-based -> neural.
"""
import sys, shutil
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

src = ROOT / "experiments" / "results" / "lstm_run" / "best_model.pt"
dst_dir = ROOT / "ai" / "models" / "registry"
dst_dir.mkdir(parents=True, exist_ok=True)
dst = dst_dir / "best_model.pt"

if not src.exists():
    print(f"ERROR: {src} not found. Run train_lstm.py first.")
    sys.exit(1)

shutil.copy2(src, dst)
print(f"Copied: {src} -> {dst}")
print("LivePipeline will now use LSTM scorer when started with lstm_model_path set.")
print(f"\nTo activate in API, set in LivePipeline init:")
print(f"  lstm_model_path='ai/models/registry/best_model.pt'")

# Also verify it loads
import torch
from ai.temporal.lstm_model import BehaviorClassifier
model = BehaviorClassifier(input_size=16)
state = torch.load(str(dst), map_location="cpu")
model.load_state_dict(state["model_state"])
model.eval()
print(f"\nVerification: model loaded OK | Params: {sum(p.numel() for p in model.parameters()):,}")
print(f"Checkpoint epoch: {state['epoch']} | metrics: {state['metrics']}")
