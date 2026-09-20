#!/usr/bin/env python3
"""
AquaGuard AI - Experiment Comparison Report
Phase 7: Generates a side-by-side comparison table of all experiment runs.
Outputs:
  experiments/results/comparison_report.json
  experiments/results/comparison_table.txt  (paper-ready text table)
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

RUNS = [
    ("lstm_run",       "LSTM (128x2, T=32)  [Proposed]"),
    ("gru_comparison", "GRU  (128x2, T=32)  [Ablation]"),
]


def load_run(run_name):
    results_path = ROOT / "experiments" / "results" / run_name / "test_results.json"
    history_path = ROOT / "experiments" / "results" / run_name / "history.json"
    checkpoint   = ROOT / "experiments" / "results" / run_name / "best_model.pt"

    if not results_path.exists():
        return None, None

    with open(results_path) as f:
        results = json.load(f)

    history = []
    if history_path.exists():
        with open(history_path) as f:
            history = json.load(f)

    # Count params from checkpoint metadata
    try:
        import torch
        ckpt   = torch.load(str(checkpoint), map_location="cpu")
        config = ckpt.get("config", {})
    except Exception:
        config = {}

    return results, {"history": history, "config": config}


def main():
    print("=" * 72)
    print(" AquaGuard AI - Experiment Comparison Report")
    print("=" * 72)

    rows   = []
    report = {}

    for run_name, label in RUNS:
        results, meta = load_run(run_name)
        if results is None:
            print(f"  [SKIP] {run_name}: results not found")
            continue

        history     = meta["history"] if meta else []
        epochs_ran  = len(history)
        best_val_dr = max((h.get("val_drowning_recall", 0) for h in history), default=0)

        row = {
            "run":              run_name,
            "label":            label,
            "epochs_trained":   epochs_ran,
            "test_accuracy":    results.get("accuracy", 0),
            "test_macro_f1":    results.get("macro_f1", 0),
            "test_weighted_f1": results.get("weighted_f1", 0),
            "drowning_recall":  results.get("drowning_recall", 0),
            "drowning_f1":      results.get("drowning_f1", 0),
            "roc_auc_macro":    results.get("roc_auc_macro") or 0,
        }
        rows.append(row)
        report[run_name] = row

    # Print text table
    header = f"{'Model':<40} {'Epochs':>6} {'Acc':>6} {'MacF1':>6} {'DrRec':>7} {'DrF1':>6} {'AUC':>6}"
    sep    = "-" * 72
    print(f"\n{header}")
    print(sep)
    for r in rows:
        print(
            f"{r['label']:<40} {r['epochs_trained']:>6} "
            f"{r['test_accuracy']:>6.4f} {r['test_macro_f1']:>6.4f} "
            f"{r['drowning_recall']:>7.4f} {r['drowning_f1']:>6.4f} "
            f"{r['roc_auc_macro']:>6.4f}"
        )
    print(sep)
    print("DrRec = Drowning Recall (primary safety metric)")
    print()

    # Save report
    out_json = ROOT / "experiments" / "results" / "comparison_report.json"
    with open(out_json, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Saved: {out_json}")

    # Save plain text table (for paper appendix)
    out_txt = ROOT / "experiments" / "results" / "comparison_table.txt"
    with open(out_txt, "w") as f:
        f.write("AquaGuard AI - Experiment Results\n")
        f.write("Data: Synthetic (2000 sequences, seed=42)\n")
        f.write("NOTE: Synthetic data yields perfect separation. ")
        f.write("Real-world scores will differ.\n\n")
        f.write(f"{header}\n{sep}\n")
        for r in rows:
            f.write(
                f"{r['label']:<40} {r['epochs_trained']:>6} "
                f"{r['test_accuracy']:>6.4f} {r['test_macro_f1']:>6.4f} "
                f"{r['drowning_recall']:>7.4f} {r['drowning_f1']:>6.4f} "
                f"{r['roc_auc_macro']:>6.4f}\n"
            )
        f.write(f"{sep}\n")
    print(f"Saved: {out_txt}")


if __name__ == "__main__":
    main()
