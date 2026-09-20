#!/usr/bin/env python3
"""
AquaGuard AI - Dataset Generation Script
Phase 7: Generates synthetic training data

Usage:
  python scripts/generate_dataset.py
  python scripts/generate_dataset.py --normal 1200 --distress 900 --drowning 900

Outputs:
  data/synthetic/sequences.npz
  data/synthetic/metadata.json
"""
import sys, argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--normal",   type=int, default=800)
    p.add_argument("--distress", type=int, default=600)
    p.add_argument("--drowning", type=int, default=600)
    p.add_argument("--seed",     type=int, default=42)
    args = p.parse_args()

    from ai.datasets.synthetic_generator import generate_dataset
    sequences, labels = generate_dataset(
        n_normal=args.normal,
        n_distress=args.distress,
        n_drowning=args.drowning,
        seed=args.seed,
    )
    print(f"\nDone. sequences.shape={sequences.shape}, labels.shape={labels.shape}")


if __name__ == "__main__":
    main()
