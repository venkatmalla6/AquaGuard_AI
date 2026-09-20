#!/usr/bin/env python3
"""
AquaGuard AI - LSTM Training Script
Phase 7: LSTM Training Pipeline

Usage:
  python scripts/train_lstm.py
  python scripts/train_lstm.py --model gru --epochs 30 --run_name gru_ablation

Research experiments this script supports:
  EXP-C: Proposed system (YOLO + ByteTrack + LSTM) -- default
  EXP-D: GRU vs LSTM comparison   -- --model gru
  EXP-E: Temporal window ablation -- --seq_len 15|30|60

All results are saved to experiments/results/<run_name>/
Paper figures are generated automatically in experiments/figures/
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def parse_args():
    p = argparse.ArgumentParser(description="AquaGuard AI LSTM Trainer")
    p.add_argument("--model",       default="lstm",  choices=["lstm","gru"])
    p.add_argument("--epochs",      type=int,   default=50)
    p.add_argument("--batch_size",  type=int,   default=32)
    p.add_argument("--hidden_size", type=int,   default=128)
    p.add_argument("--num_layers",  type=int,   default=2)
    p.add_argument("--dropout",     type=float, default=0.3)
    p.add_argument("--lr",          type=float, default=1e-3)
    p.add_argument("--seq_len",     type=int,   default=32)
    p.add_argument("--patience",    type=int,   default=10)
    p.add_argument("--seed",        type=int,   default=42)
    p.add_argument("--run_name",    default="lstm_run")
    p.add_argument("--data_path",   default="data/synthetic/sequences.npz")
    p.add_argument("--no_plots",    action="store_true")
    return p.parse_args()


def main():
    args = parse_args()

    print("=" * 62)
    print(" AquaGuard AI - Phase 7: LSTM Training Pipeline")
    print("=" * 62)
    print(f" Model:       {args.model.upper()}")
    print(f" Epochs:      {args.epochs}")
    print(f" Batch:       {args.batch_size}")
    print(f" Hidden:      {args.hidden_size} x {args.num_layers} layers")
    print(f" Seq Length:  {args.seq_len}")
    print(f" Run name:    {args.run_name}")
    print(f" Data:        {args.data_path}")
    print("=" * 62)

    data_path = ROOT / args.data_path
    if not data_path.exists():
        print(f"\n[!] Dataset not found: {data_path}")
        print(f"    Run first:  python scripts/generate_dataset.py")
        sys.exit(1)

    # ---- 1. Load dataset ----
    print("\n[1] Loading dataset...")
    from ai.datasets.sequence_dataset import load_dataset_splits, make_dataloaders
    train_ds, val_ds, test_ds = load_dataset_splits(
        str(data_path), val_split=0.15, test_split=0.15, seed=args.seed)
    train_loader, val_loader, test_loader = make_dataloaders(
        train_ds, val_ds, test_ds,
        batch_size=args.batch_size,
        weighted_sample=True,
    )

    # ---- 2. Build model ----
    print("\n[2] Building model...")
    from ai.temporal.lstm_model import BehaviorClassifier
    model = BehaviorClassifier(
        input_size=16,
        hidden_size=args.hidden_size,
        num_layers=args.num_layers,
        num_classes=3,
        dropout=args.dropout,
        model_type=args.model,
    )
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"   Model: {args.model.upper()} | Params: {total_params:,}")
    print(f"   Architecture: 16 -> LSTM({args.hidden_size}x{args.num_layers}) -> 64 -> 3")

    # ---- 3. Configure trainer ----
    from ai.training.trainer import Trainer, TrainingConfig
    config = TrainingConfig(
        model_type=args.model,
        hidden_size=args.hidden_size,
        num_layers=args.num_layers,
        dropout=args.dropout,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        early_stopping_patience=args.patience,
        checkpoint_metric="drowning_recall",
        output_dir="experiments/results",
        run_name=args.run_name,
        seed=args.seed,
        device="cpu",
    )
    trainer = Trainer(config, model, train_loader, val_loader)

    # ---- 4. Train ----
    print(f"\n[3] Training ({args.epochs} epochs max, early stop patience={args.patience})...")
    print(f"    Primary checkpoint metric: drowning_recall (safety-critical)\n")
    history = trainer.train()

    # ---- 5. Test evaluation ----
    print("\n[4] Evaluating on test set...")
    result = trainer.evaluate(test_loader)

    # ---- 6. Generate figures ----
    if not args.no_plots:
        print("\n[5] Generating paper figures...")
        try:
            from ai.evaluation.plot_results import generate_all_plots
            run_dir = str(ROOT / "experiments" / "results" / args.run_name)
            generate_all_plots(run_dir)
        except Exception as e:
            print(f"   Plot generation failed: {e} (install matplotlib to enable)")

    # ---- Summary ----
    print("\n" + "=" * 62)
    print(" Training Complete - Summary")
    print("=" * 62)
    print(f"  Epochs trained:      {len(history)}")
    print(f"  Best drowning recall: {max(h['val_drowning_recall'] for h in [vars(h) for h in history]):.4f}")
    print(f"  Test accuracy:        {result.accuracy:.4f}")
    print(f"  Test macro F1:        {result.macro_f1:.4f}")
    print(f"  Test drowning recall: {result.drowning_recall:.4f}  *** KEY METRIC ***")
    print(f"  Test drowning F1:     {result.drowning_f1:.4f}")
    if result.roc_auc_macro:
        print(f"  Test ROC-AUC (macro): {result.roc_auc_macro:.4f}")
    print(f"\n  Outputs: experiments/results/{args.run_name}/")
    print(f"           experiments/figures/")
    print("=" * 62)


if __name__ == "__main__":
    main()
