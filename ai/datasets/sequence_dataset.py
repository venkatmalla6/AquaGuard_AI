"""
AquaGuard AI - PyTorch Sequence Dataset
Phase 7: LSTM Training Pipeline

Loads (N, 32, 16) float32 sequences + (N,) int64 labels from .npz files.
Handles train/val/test split at dataset level (not video-level since data is synthetic).
For real data acquired from video, split_by='video' should be enforced in the loader.
"""
import json
from pathlib import Path
from typing import Optional, Tuple, List
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler

CLASS_NAMES = ["normal", "distress", "drowning"]


class BehaviorSequenceDataset(Dataset):
    """
    PyTorch Dataset for 16-D temporal behavior sequences.

    Args:
        sequences: (N, T, 16) float32 array
        labels:    (N,)       int64 array
        transform: optional callable applied to each sequence tensor
    """
    def __init__(
        self,
        sequences: np.ndarray,
        labels:    np.ndarray,
        transform=None,
    ):
        assert len(sequences) == len(labels), "sequences/labels length mismatch"
        assert sequences.ndim == 3 and sequences.shape[2] == 16, \
            f"Expected (N, T, 16), got {sequences.shape}"
        self.sequences = torch.tensor(sequences, dtype=torch.float32)
        self.labels    = torch.tensor(labels,    dtype=torch.long)
        self.transform = transform

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        x = self.sequences[idx]   # (T, 16)
        y = self.labels[idx]      # scalar
        if self.transform:
            x = self.transform(x)
        return x, y

    @property
    def class_counts(self) -> dict:
        counts = {}
        for i, name in enumerate(CLASS_NAMES):
            counts[name] = int((self.labels == i).sum())
        return counts


def load_dataset_splits(
    npz_path:   str,
    val_split:  float = 0.15,
    test_split: float = 0.15,
    seed:       int   = 42,
) -> Tuple["BehaviorSequenceDataset", "BehaviorSequenceDataset", "BehaviorSequenceDataset"]:
    """
    Load sequences.npz and split into train / val / test datasets.
    Splitting is stratified by class to maintain class balance in each split.

    Returns: (train_ds, val_ds, test_ds)
    """
    data = np.load(npz_path)
    sequences = data["sequences"]  # (N, 32, 16)
    labels    = data["labels"]     # (N,)

    rng = np.random.default_rng(seed)
    n   = len(labels)

    # Stratified split: process each class independently then merge
    train_idx, val_idx, test_idx = [], [], []
    for cls in range(3):
        cls_idx = np.where(labels == cls)[0]
        rng.shuffle(cls_idx)
        n_cls  = len(cls_idx)
        n_test = max(1, int(n_cls * test_split))
        n_val  = max(1, int(n_cls * val_split))
        test_idx.extend(cls_idx[:n_test])
        val_idx.extend(cls_idx[n_test:n_test + n_val])
        train_idx.extend(cls_idx[n_test + n_val:])

    train_idx = np.array(train_idx)
    val_idx   = np.array(val_idx)
    test_idx  = np.array(test_idx)

    train_ds = BehaviorSequenceDataset(sequences[train_idx], labels[train_idx])
    val_ds   = BehaviorSequenceDataset(sequences[val_idx],   labels[val_idx])
    test_ds  = BehaviorSequenceDataset(sequences[test_idx],  labels[test_idx])

    print(f"Dataset split (stratified):")
    print(f"  Train: {len(train_ds):4d}  {train_ds.class_counts}")
    print(f"  Val:   {len(val_ds):4d}  {val_ds.class_counts}")
    print(f"  Test:  {len(test_ds):4d}  {test_ds.class_counts}")
    return train_ds, val_ds, test_ds


def make_weighted_sampler(dataset: "BehaviorSequenceDataset") -> WeightedRandomSampler:
    """
    WHY weighted sampling:
    Class imbalance (normal >> drowning) would cause the model to
    over-predict normal. Weighted sampling ensures the training loop
    sees equal representation of all three classes per epoch.
    This is the standard technique for imbalanced medical datasets.
    """
    labels = dataset.labels.numpy()
    class_counts = np.bincount(labels, minlength=3)
    class_weights = 1.0 / (class_counts + 1e-6)
    sample_weights = class_weights[labels]
    return WeightedRandomSampler(
        weights=torch.tensor(sample_weights, dtype=torch.float32),
        num_samples=len(labels),
        replacement=True,
    )


def make_dataloaders(
    train_ds: "BehaviorSequenceDataset",
    val_ds:   "BehaviorSequenceDataset",
    test_ds:  "BehaviorSequenceDataset",
    batch_size:      int  = 32,
    num_workers:     int  = 0,
    weighted_sample: bool = True,
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """Create train/val/test DataLoaders with optional weighted sampling."""
    sampler = make_weighted_sampler(train_ds) if weighted_sample else None
    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        sampler=sampler,
        shuffle=(sampler is None),
        num_workers=num_workers,
        pin_memory=False,
    )
    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    test_loader = DataLoader(
        test_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    return train_loader, val_loader, test_loader
