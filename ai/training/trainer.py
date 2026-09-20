"""
AquaGuard AI - LSTM Trainer
Phase 7: LSTM Training Pipeline

Full training loop with:
  - Cross-entropy loss with class weights (handle imbalance)
  - AdamW optimizer + cosine LR scheduler
  - Early stopping (patience-based on val loss)
  - Per-epoch metric logging to CSV
  - Best-model checkpointing (drowning_recall prioritized over accuracy)
  - Gradient clipping for RNN stability

WHY drowning_recall as the primary checkpoint metric:
  In a safety-critical system, failing to detect a drowning event (FN) is
  catastrophically worse than a false alarm (FP). The checkpoint saves the
  model with the highest drowning recall on the validation set, not the
  highest accuracy. This is a deliberate research design decision to be
  documented in the paper's methodology section.
"""
import csv
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from loguru import logger


@dataclass
class TrainingConfig:
    # Model
    model_type:    str   = "lstm"   # "lstm" or "gru"
    input_size:    int   = 16
    hidden_size:   int   = 128
    num_layers:    int   = 2
    dropout:       float = 0.3
    num_classes:   int   = 3

    # Training
    epochs:        int   = 50
    batch_size:    int   = 32
    learning_rate: float = 1e-3
    weight_decay:  float = 1e-4
    grad_clip:     float = 1.0      # gradient clipping norm
    early_stopping_patience: int = 10

    # Scheduler
    lr_scheduler:  str   = "cosine"  # "cosine" | "step" | "none"

    # Checkpointing
    checkpoint_metric: str = "drowning_recall"  # primary best-model metric
    output_dir:  str = "experiments/results"
    run_name:    str = "lstm_run"
    seed:        int = 42

    # Hardware
    device:      str = "cpu"


@dataclass
class EpochLog:
    epoch:          int
    train_loss:     float
    val_loss:       float
    val_accuracy:   float
    val_macro_f1:   float
    val_drowning_recall:    float
    val_drowning_f1:        float
    lr:             float
    epoch_time_s:   float


class Trainer:
    """
    Encapsulates the full LSTM training procedure.

    Usage:
        config  = TrainingConfig(epochs=50, run_name="lstm_baseline")
        trainer = Trainer(config, model, train_loader, val_loader)
        history = trainer.train()
        results = trainer.evaluate(test_loader)
    """

    def __init__(
        self,
        config:       TrainingConfig,
        model:        nn.Module,
        train_loader: DataLoader,
        val_loader:   DataLoader,
    ):
        self.config = config
        self.model  = model.to(config.device)
        self.train_loader = train_loader
        self.val_loader   = val_loader

        # Class weights for imbalanced dataset
        self.criterion = nn.CrossEntropyLoss(
            weight=self._compute_class_weights(train_loader)
        )
        self.optimizer = optim.AdamW(
            model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
        )
        self.scheduler = self._build_scheduler()

        self.out_dir = Path(config.output_dir) / config.run_name
        self.out_dir.mkdir(parents=True, exist_ok=True)

        self.history: List[EpochLog] = []
        self._best_metric = -1.0
        self._no_improve  = 0
        self._best_path   = self.out_dir / "best_model.pt"

        # CSV log
        self._csv_path = self.out_dir / "training_log.csv"
        self._init_csv()

        torch.manual_seed(config.seed)
        np.random.seed(config.seed)

    # ---- Setup helpers ----

    def _compute_class_weights(self, loader: DataLoader) -> torch.Tensor:
        """
        Inverse-frequency class weights to penalize majority-class over-confidence.
        WHY: Our dataset has more normal samples; without weights the model ignores drowning.
        """
        counts = torch.zeros(self.config.num_classes)
        for _, y in loader:
            for cls in range(self.config.num_classes):
                counts[cls] += (y == cls).sum()
        total   = counts.sum()
        weights = total / (self.config.num_classes * counts + 1e-6)
        logger.info(f"Class weights: {weights.tolist()}")
        return weights.to(self.config.device)

    def _build_scheduler(self):
        if self.config.lr_scheduler == "cosine":
            return optim.lr_scheduler.CosineAnnealingLR(
                self.optimizer, T_max=self.config.epochs, eta_min=1e-6)
        elif self.config.lr_scheduler == "step":
            return optim.lr_scheduler.StepLR(
                self.optimizer, step_size=10, gamma=0.5)
        return None

    def _init_csv(self):
        with open(self._csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "epoch","train_loss","val_loss","val_accuracy",
                "val_macro_f1","val_drowning_recall","val_drowning_f1",
                "lr","epoch_time_s",
            ])
            writer.writeheader()

    def _append_csv(self, log: EpochLog):
        with open(self._csv_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "epoch","train_loss","val_loss","val_accuracy",
                "val_macro_f1","val_drowning_recall","val_drowning_f1",
                "lr","epoch_time_s",
            ])
            writer.writerow({
                "epoch":               log.epoch,
                "train_loss":          round(log.train_loss, 5),
                "val_loss":            round(log.val_loss, 5),
                "val_accuracy":        round(log.val_accuracy, 4),
                "val_macro_f1":        round(log.val_macro_f1, 4),
                "val_drowning_recall": round(log.val_drowning_recall, 4),
                "val_drowning_f1":     round(log.val_drowning_f1, 4),
                "lr":                  round(log.lr, 8),
                "epoch_time_s":        round(log.epoch_time_s, 2),
            })

    # ---- Training loop ----

    def train(self) -> List[EpochLog]:
        logger.info(f"Training: {self.config.run_name} | device={self.config.device}")
        logger.info(f"Checkpoint metric: {self.config.checkpoint_metric}")

        for epoch in range(1, self.config.epochs + 1):
            t0 = time.time()

            train_loss = self._train_epoch()
            val_loss, val_metrics = self._validate_epoch()

            lr = self.optimizer.param_groups[0]["lr"]
            if self.scheduler:
                self.scheduler.step()

            log = EpochLog(
                epoch=epoch,
                train_loss=train_loss,
                val_loss=val_loss,
                val_accuracy=val_metrics["accuracy"],
                val_macro_f1=val_metrics["macro_f1"],
                val_drowning_recall=val_metrics["drowning_recall"],
                val_drowning_f1=val_metrics["drowning_f1"],
                lr=lr,
                epoch_time_s=time.time() - t0,
            )
            self.history.append(log)
            self._append_csv(log)

            logger.info(
                f"Ep {epoch:3d}/{self.config.epochs} | "
                f"TrLoss={train_loss:.4f} ValLoss={val_loss:.4f} | "
                f"Acc={val_metrics['accuracy']:.3f} F1={val_metrics['macro_f1']:.3f} | "
                f"DrowRecall={val_metrics['drowning_recall']:.3f} | LR={lr:.6f}"
            )

            # Early stopping + checkpointing
            metric_val = val_metrics.get(self.config.checkpoint_metric, val_metrics["macro_f1"])
            if metric_val > self._best_metric:
                self._best_metric = metric_val
                self._no_improve  = 0
                self._save_checkpoint(epoch, val_metrics)
            else:
                self._no_improve += 1
                if self._no_improve >= self.config.early_stopping_patience:
                    logger.info(f"Early stopping at epoch {epoch} (no improvement for {self._no_improve} epochs)")
                    break

        self._save_history()
        logger.info(f"Training complete. Best {self.config.checkpoint_metric}={self._best_metric:.4f}")
        logger.info(f"Best model: {self._best_path}")
        return self.history

    def _train_epoch(self) -> float:
        self.model.train()
        total_loss = 0.0
        for x, y in self.train_loader:
            x = x.to(self.config.device)
            y = y.to(self.config.device)
            self.optimizer.zero_grad()
            logits = self.model(x)
            loss   = self.criterion(logits, y)
            loss.backward()
            nn.utils.clip_grad_norm_(self.model.parameters(), self.config.grad_clip)
            self.optimizer.step()
            total_loss += loss.item() * len(y)
        return total_loss / max(len(self.train_loader.dataset), 1)

    def _validate_epoch(self) -> Tuple[float, dict]:
        from ai.evaluation.metrics import evaluate
        self.model.eval()
        total_loss = 0.0
        all_pred, all_true, all_proba = [], [], []
        with torch.no_grad():
            for x, y in self.val_loader:
                x = x.to(self.config.device)
                y = y.to(self.config.device)
                logits = self.model(x)
                loss   = self.criterion(logits, y)
                total_loss += loss.item() * len(y)
                proba = torch.softmax(logits, dim=-1).cpu().numpy()
                pred  = np.argmax(proba, axis=1)
                all_proba.append(proba)
                all_pred.extend(pred.tolist())
                all_true.extend(y.cpu().numpy().tolist())

        val_loss = total_loss / max(len(self.val_loader.dataset), 1)
        result   = evaluate(
            np.array(all_true), np.array(all_pred), np.vstack(all_proba))

        return val_loss, {
            "accuracy":        result.accuracy,
            "macro_f1":        result.macro_f1,
            "drowning_recall": result.drowning_recall,
            "drowning_f1":     result.drowning_f1,
        }

    # ---- Evaluation on test set ----

    def evaluate(self, test_loader: DataLoader):
        """Full evaluation on the test set using the BEST saved model."""
        from ai.evaluation.metrics import evaluate, print_report, save_results

        logger.info(f"Loading best model from {self._best_path}")
        state = torch.load(self._best_path, map_location=self.config.device)
        self.model.load_state_dict(state["model_state"])
        self.model.eval()

        all_pred, all_true, all_proba = [], [], []
        with torch.no_grad():
            for x, y in test_loader:
                x      = x.to(self.config.device)
                logits = self.model(x)
                proba  = torch.softmax(logits, dim=-1).cpu().numpy()
                pred   = np.argmax(proba, axis=1)
                all_proba.append(proba)
                all_pred.extend(pred.tolist())
                all_true.extend(y.numpy().tolist())

        result = evaluate(
            np.array(all_true), np.array(all_pred), np.vstack(all_proba))
        print_report(result, title=f"Test Set Results - {self.config.run_name}")
        save_results(result, str(self.out_dir / "test_results.json"))
        return result

    # ---- Persistence ----

    def _save_checkpoint(self, epoch: int, metrics: dict):
        torch.save({
            "epoch":        epoch,
            "model_state":  self.model.state_dict(),
            "optimizer":    self.optimizer.state_dict(),
            "metrics":      metrics,
            "config":       vars(self.config),
            "best_metric":  self._best_metric,
        }, self._best_path)
        logger.info(f"  Checkpoint saved (epoch {epoch}, {self.config.checkpoint_metric}={self._best_metric:.4f})")

    def _save_history(self):
        history_path = self.out_dir / "history.json"
        data = [vars(log) for log in self.history]
        with open(history_path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"History saved: {history_path}")
