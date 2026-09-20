"""
AquaGuard AI - Evaluation Metrics
Phase 7: LSTM Training Pipeline

Research-grade metrics required for the B.Tech paper:
  - Per-class Precision, Recall, F1-Score
  - Macro/Weighted F1
  - Confusion Matrix (absolute + normalized)
  - ROC-AUC (one-vs-rest, micro/macro)
  - Training history curves (loss, accuracy per epoch)

WHY these metrics matter for drowning detection:
  In a safety-critical domain, RECALL for drowning class is paramount.
  A missed drowning (False Negative) is far more dangerous than a
  false alarm (False Positive). The paper should explicitly discuss
  the precision-recall tradeoff and justify the operating threshold.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

CLASS_NAMES = ["normal", "distress", "drowning"]


@dataclass
class ClassMetrics:
    name:      str
    precision: float
    recall:    float
    f1:        float
    support:   int


@dataclass
class EvaluationResult:
    """Complete evaluation result for one model checkpoint."""
    accuracy:        float
    macro_f1:        float
    weighted_f1:     float
    drowning_recall: float          # Most critical metric
    drowning_precision: float
    drowning_f1:     float
    per_class:       List[ClassMetrics]
    confusion_matrix: np.ndarray    # (3, 3) raw counts
    confusion_norm:  np.ndarray     # (3, 3) row-normalized (recall-oriented)
    roc_auc_macro:   Optional[float] = None
    roc_auc_per_class: Optional[Dict[str, float]] = None

    def to_dict(self) -> dict:
        return {
            "accuracy":          round(self.accuracy, 4),
            "macro_f1":          round(self.macro_f1, 4),
            "weighted_f1":       round(self.weighted_f1, 4),
            "drowning_recall":   round(self.drowning_recall, 4),
            "drowning_precision":round(self.drowning_precision, 4),
            "drowning_f1":       round(self.drowning_f1, 4),
            "roc_auc_macro":     round(self.roc_auc_macro, 4) if self.roc_auc_macro else None,
            "per_class": {
                m.name: {
                    "precision": round(m.precision, 4),
                    "recall":    round(m.recall, 4),
                    "f1":        round(m.f1, 4),
                    "support":   m.support,
                }
                for m in self.per_class
            },
            "confusion_matrix": self.confusion_matrix.tolist(),
        }


def compute_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    num_classes: int = 3,
) -> np.ndarray:
    """Compute (num_classes, num_classes) confusion matrix without sklearn."""
    cm = np.zeros((num_classes, num_classes), dtype=np.int64)
    for t, p in zip(y_true, y_pred):
        if 0 <= t < num_classes and 0 <= p < num_classes:
            cm[t, p] += 1
    return cm


def compute_per_class_metrics(cm: np.ndarray) -> List[ClassMetrics]:
    """Compute precision, recall, F1 per class from confusion matrix."""
    metrics = []
    num_classes = cm.shape[0]
    for i in range(num_classes):
        tp = cm[i, i]
        fp = cm[:, i].sum() - tp
        fn = cm[i, :].sum() - tp
        precision = tp / (tp + fp + 1e-9)
        recall    = tp / (tp + fn + 1e-9)
        f1        = 2 * precision * recall / (precision + recall + 1e-9)
        support   = int(cm[i, :].sum())
        metrics.append(ClassMetrics(
            name=CLASS_NAMES[i],
            precision=float(precision),
            recall=float(recall),
            f1=float(f1),
            support=support,
        ))
    return metrics


def compute_macro_f1(per_class: List[ClassMetrics]) -> float:
    return float(np.mean([m.f1 for m in per_class]))


def compute_weighted_f1(per_class: List[ClassMetrics]) -> float:
    total = sum(m.support for m in per_class)
    if total == 0:
        return 0.0
    return float(sum(m.f1 * m.support for m in per_class) / total)


def compute_roc_auc(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    num_classes: int = 3,
) -> Tuple[float, Dict[str, float]]:
    """
    One-vs-Rest ROC-AUC computation without sklearn.
    Uses trapezoidal rule for numerical integration.

    Args:
        y_true:  (N,) integer class labels
        y_proba: (N, num_classes) softmax probabilities

    Returns:
        macro_auc, per_class_auc_dict
    """
    aucs = {}
    for cls in range(num_classes):
        binary_true  = (y_true == cls).astype(float)
        scores       = y_proba[:, cls]

        # Sort by score descending
        sorted_idx = np.argsort(-scores)
        binary_true = binary_true[sorted_idx]

        tp = np.cumsum(binary_true)
        fp = np.cumsum(1 - binary_true)

        tpr = tp / (binary_true.sum() + 1e-9)
        fpr = fp / ((1 - binary_true).sum() + 1e-9)

        # Prepend (0,0)
        tpr = np.concatenate([[0], tpr])
        fpr = np.concatenate([[0], fpr])

        auc = float(np.trapezoid(tpr, fpr) if hasattr(np, 'trapezoid') else np.trapz(tpr, fpr))
        aucs[CLASS_NAMES[cls]] = round(abs(auc), 4)

    macro_auc = float(np.mean(list(aucs.values())))
    return macro_auc, aucs


def evaluate(
    y_true:  np.ndarray,
    y_pred:  np.ndarray,
    y_proba: Optional[np.ndarray] = None,
) -> EvaluationResult:
    """
    Full evaluation from predictions.

    Args:
        y_true:  (N,) true integer labels
        y_pred:  (N,) predicted integer labels
        y_proba: (N, 3) softmax probabilities (optional, for AUC)
    """
    cm       = compute_confusion_matrix(y_true, y_pred)
    per_cls  = compute_per_class_metrics(cm)
    macro_f1 = compute_macro_f1(per_cls)
    wf1      = compute_weighted_f1(per_cls)

    # Row-normalized (recall-oriented): cm_norm[i,j] = fraction of class i predicted as j
    row_sums = cm.sum(axis=1, keepdims=True).astype(float)
    cm_norm  = np.where(row_sums > 0, cm / row_sums, 0.0)

    accuracy = float(np.mean(y_true == y_pred))

    drowning = next(m for m in per_cls if m.name == "drowning")

    roc_auc_macro, roc_auc_per = None, None
    if y_proba is not None:
        roc_auc_macro, roc_auc_per = compute_roc_auc(y_true, y_proba)

    return EvaluationResult(
        accuracy=accuracy,
        macro_f1=macro_f1,
        weighted_f1=wf1,
        drowning_recall=drowning.recall,
        drowning_precision=drowning.precision,
        drowning_f1=drowning.f1,
        per_class=per_cls,
        confusion_matrix=cm,
        confusion_norm=cm_norm,
        roc_auc_macro=roc_auc_macro,
        roc_auc_per_class=roc_auc_per,
    )


def print_report(result: EvaluationResult, title: str = "Evaluation Report"):
    print(f"\n{'='*56}")
    print(f"  {title}")
    print(f"{'='*56}")
    print(f"  Accuracy:          {result.accuracy:.4f}")
    print(f"  Macro F1:          {result.macro_f1:.4f}")
    print(f"  Weighted F1:       {result.weighted_f1:.4f}")
    if result.roc_auc_macro:
        print(f"  ROC-AUC (macro):   {result.roc_auc_macro:.4f}")
    print(f"\n  *** Drowning Class (safety-critical) ***")
    print(f"  Drowning Recall:    {result.drowning_recall:.4f}  (minimize false negatives)")
    print(f"  Drowning Precision: {result.drowning_precision:.4f}")
    print(f"  Drowning F1:        {result.drowning_f1:.4f}")
    print(f"\n  Per-Class Breakdown:")
    print(f"  {'Class':<12} {'Prec':>7} {'Rec':>7} {'F1':>7} {'Support':>9}")
    print(f"  {'-'*44}")
    for m in result.per_class:
        print(f"  {m.name:<12} {m.precision:>7.4f} {m.recall:>7.4f} {m.f1:>7.4f} {m.support:>9}")
    print(f"\n  Confusion Matrix (rows=true, cols=predicted):")
    print(f"  {'':12}", end="")
    for n in CLASS_NAMES:
        print(f"  {n[:8]:>8}", end="")
    print()
    for i, row in enumerate(result.confusion_matrix):
        print(f"  {CLASS_NAMES[i]:<12}", end="")
        for v in row:
            print(f"  {v:>8}", end="")
        print()
    print(f"{'='*56}\n")


def save_results(result: EvaluationResult, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(result.to_dict(), f, indent=2)
    print(f"Results saved: {path}")

