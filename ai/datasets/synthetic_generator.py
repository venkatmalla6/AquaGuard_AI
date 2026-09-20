"""
AquaGuard AI - Synthetic Dataset Generator
Phase 7: LSTM Training Pipeline

WHY synthetic data:
  Real drowning video datasets are extremely scarce, ethically restricted,
  and unavailable for academic download. For the research prototype, we
  generate physiologically-grounded synthetic 16-D feature sequences.
  
  The generator uses documented biomechanical drowning patterns:
  - Instinctive Drowning Response (IDR): vertical posture, arms lateral,
    head tilting back, little or no leg kick (Pia, 1974; Brewster, 2003)
  - Distress: waving, calling out, sustained movement but staying afloat
  - Normal swimming: rhythmic horizontal movement, consistent speed
  
  All sequences are labeled at generation time and clearly documented
  as synthetic in any published experiment results (academic integrity).

Output:
  data/synthetic/sequences.npz  -- (N, 32, 16) float32 + (N,) int labels
  data/synthetic/metadata.json  -- class distribution, generation params

Feature order (must match FeatureScorer.FEATURE_IDX):
  0:cx_norm  1:cy_norm  2:w_norm  3:h_norm  4:aspect_ratio  5:area_norm
  6:displacement  7:vel_x  8:vel_y  9:speed  10:acceleration
  11:dir_sin  12:dir_cos  13:movement_variance  14:vertical_ratio  15:inactivity
"""

import json
import sys
from pathlib import Path
from typing import Tuple

import numpy as np

ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Labels
LABEL_NORMAL   = 0
LABEL_DISTRESS = 1
LABEL_DROWNING = 2
CLASS_NAMES    = ["normal", "distress", "drowning"]

# Feature indices
FI = {
    "cx_norm":0,"cy_norm":1,"w_norm":2,"h_norm":3,"aspect_ratio":4,"area_norm":5,
    "displacement":6,"velocity_x":7,"velocity_y":8,"speed":9,"acceleration":10,
    "direction_sin":11,"direction_cos":12,"movement_variance":13,
    "vertical_ratio":14,"inactivity":15,
}
N_FEATURES = 16
SEQ_LEN    = 32


def _add_noise(seq: np.ndarray, scale: float = 0.02) -> np.ndarray:
    """Add realistic sensor noise to a sequence."""
    return seq + np.random.normal(0, scale, seq.shape).astype(np.float32)


def _smooth(arr: np.ndarray, window: int = 3) -> np.ndarray:
    """Moving-average smoothing to create realistic temporal continuity."""
    out = arr.copy()
    for i in range(window, len(arr)):
        out[i] = arr[max(0,i-window):i+1].mean()
    return out


def generate_normal_sequence(rng: np.random.Generator) -> np.ndarray:
    """
    Simulate a swimmer doing freestyle or breaststroke.
    - Horizontal aspect ratio (wide bbox)
    - Consistent moderate speed with rhythmic oscillation
    - Low inactivity, balanced vertical/horizontal movement
    """
    seq = np.zeros((SEQ_LEN, N_FEATURES), dtype=np.float32)
    
    # Position drifts horizontally across the pool
    cx = rng.uniform(0.2, 0.8)
    cy = rng.uniform(0.3, 0.6)
    
    base_speed = rng.uniform(8, 18)  # px/frame
    angle = rng.uniform(-0.3, 0.3)   # near-horizontal
    
    for t in range(SEQ_LEN):
        # Rhythmic speed (swim stroke oscillation)
        stroke_phase = np.sin(t * 0.6) * 3.0
        speed = max(2.0, base_speed + stroke_phase + rng.normal(0, 1.5))
        
        vx = speed * np.cos(angle) + rng.normal(0, 1)
        vy = speed * np.sin(angle) + rng.normal(0, 0.5)
        
        # Update position (bounded to frame)
        cx = float(np.clip(cx + vx/640, 0.05, 0.95))
        cy = float(np.clip(cy + vy/360, 0.1, 0.9))
        
        # Wide horizontal bbox (swimming posture)
        ar = rng.uniform(1.4, 2.5)
        w_norm = rng.uniform(0.08, 0.18)
        h_norm = w_norm / ar
        
        disp = np.sqrt(vx**2 + vy**2)
        vert = abs(vy) / (abs(vx) + abs(vy) + 1e-6)
        
        seq[t, FI["cx_norm"]]          = cx
        seq[t, FI["cy_norm"]]          = cy
        seq[t, FI["w_norm"]]           = w_norm
        seq[t, FI["h_norm"]]           = h_norm
        seq[t, FI["aspect_ratio"]]     = ar
        seq[t, FI["area_norm"]]        = w_norm * h_norm
        seq[t, FI["displacement"]]     = disp
        seq[t, FI["velocity_x"]]       = vx
        seq[t, FI["velocity_y"]]       = vy
        seq[t, FI["speed"]]            = speed
        seq[t, FI["acceleration"]]     = rng.normal(0, 1.5)
        seq[t, FI["direction_sin"]]    = np.sin(angle)
        seq[t, FI["direction_cos"]]    = np.cos(angle)
        seq[t, FI["movement_variance"]]= rng.uniform(5, 60)
        seq[t, FI["vertical_ratio"]]   = vert
        seq[t, FI["inactivity"]]       = 0.0
    
    return _add_noise(seq, scale=0.015)


def generate_distress_sequence(rng: np.random.Generator) -> np.ndarray:
    """
    Simulate active water distress (pre-drowning struggle).
    - Irregular, erratic movement (thrashing)
    - Increasing vertical bias
    - Speed varies: bursts of movement then slowing
    - Aspect ratio transitions toward vertical
    - NOT yet inert (active distress)
    """
    seq = np.zeros((SEQ_LEN, N_FEATURES), dtype=np.float32)
    
    cx = rng.uniform(0.2, 0.8)
    cy = rng.uniform(0.3, 0.7)
    
    base_speed = rng.uniform(3, 10)
    prev_speed = base_speed
    mv_history = []
    
    for t in range(SEQ_LEN):
        # Irregular speed — energy fading over time
        fade = 1.0 - (t / SEQ_LEN) * 0.4   # slowly decreasing energy
        speed = max(1.0, base_speed * fade + rng.normal(0, 3))
        
        # Erratic direction changes (thrashing)
        angle = rng.uniform(-np.pi, np.pi)
        vx = speed * np.cos(angle) * 0.6   # dampened horizontal
        vy = abs(speed * np.sin(angle))     # mostly upward struggle
        
        cx = float(np.clip(cx + vx/640, 0.05, 0.95))
        cy = float(np.clip(cy - vy/360, 0.05, 0.90))  # struggling upward
        
        # Aspect ratio trends toward 1.0 (squarish — neither swimming nor sinking)
        ar = rng.uniform(0.7, 1.4)
        w_norm = rng.uniform(0.06, 0.14)
        h_norm = w_norm / ar
        
        disp = np.sqrt(vx**2 + vy**2)
        mv_history.append(disp)
        mv_var = float(np.var(mv_history[-8:])) if len(mv_history) >= 3 else 0.0
        vert = abs(vy) / (abs(vx) + abs(vy) + 1e-6)
        accel = speed - prev_speed
        prev_speed = speed
        
        inactivity = 1.0 if speed < 2.5 else 0.0
        
        seq[t, FI["cx_norm"]]          = cx
        seq[t, FI["cy_norm"]]          = cy
        seq[t, FI["w_norm"]]           = w_norm
        seq[t, FI["h_norm"]]           = h_norm
        seq[t, FI["aspect_ratio"]]     = ar
        seq[t, FI["area_norm"]]        = w_norm * h_norm
        seq[t, FI["displacement"]]     = disp
        seq[t, FI["velocity_x"]]       = vx
        seq[t, FI["velocity_y"]]       = vy
        seq[t, FI["speed"]]            = speed
        seq[t, FI["acceleration"]]     = accel
        seq[t, FI["direction_sin"]]    = np.sin(angle)
        seq[t, FI["direction_cos"]]    = np.cos(angle)
        seq[t, FI["movement_variance"]]= mv_var
        seq[t, FI["vertical_ratio"]]   = vert
        seq[t, FI["inactivity"]]       = inactivity
    
    return _add_noise(seq, scale=0.025)


def generate_drowning_sequence(rng: np.random.Generator) -> np.ndarray:
    """
    Simulate Instinctive Drowning Response (IDR).
    Key physiological markers (Pia 1974, Brewster 2003):
      - Person goes vertical (narrow bbox, h >> w)
      - Very little or no leg kick
      - Arms press laterally and downward (low vx, variable vy)
      - Head tilts back (bbox top-heavy)
      - Sinks: cy increases (moving down in frame = lower in water)
      - Sustained inactivity / near-zero speed phases
      - Movement variance: initial thrash then sharp drop
    """
    seq = np.zeros((SEQ_LEN, N_FEATURES), dtype=np.float32)
    
    cx = rng.uniform(0.25, 0.75)
    cy = rng.uniform(0.2, 0.55)
    
    prev_speed = rng.uniform(2, 5)
    mv_history = []
    
    for t in range(SEQ_LEN):
        # Drowning progression: active struggle -> passive sinking
        progress = t / SEQ_LEN                      # 0 -> 1
        energy   = max(0.0, 1.0 - progress * 1.3)  # exhaustion
        
        # Speed: starts low, dips to near-zero after ~20 frames
        speed = max(0.0, rng.uniform(0, 3) * energy + rng.normal(0, 0.5))
        
        # Mostly sinking (positive cy drift = moving down in frame)
        vy = rng.uniform(0.5, 2.0) * (1.0 + progress)   # accelerating sink
        vx = rng.normal(0, 0.5 * energy)                  # minimal horizontal
        
        cx = float(np.clip(cx + vx/640, 0.2, 0.8))
        cy = float(np.clip(cy + vy/360, 0.1, 0.95))
        
        # VERTICAL bbox: h >> w (aspect_ratio < 0.7 → narrow)
        ar = rng.uniform(0.25, 0.65)
        w_norm = rng.uniform(0.04, 0.10)
        h_norm = w_norm / ar
        
        disp = np.sqrt(vx**2 + vy**2)
        mv_history.append(disp)
        mv_var = float(np.var(mv_history[-8:])) if len(mv_history) >= 3 else 0.0
        
        vert_total = abs(vx) + abs(vy) + 1e-6
        vert = abs(vy) / vert_total   # heavily vertical
        
        accel = speed - prev_speed
        prev_speed = speed
        
        angle = np.arctan2(vy, vx) if speed > 0.1 else 0.0
        
        # Inactivity: 1 when speed < threshold (sinking passively)
        inactivity = 1.0 if speed < 2.0 else 0.0
        
        seq[t, FI["cx_norm"]]          = cx
        seq[t, FI["cy_norm"]]          = cy
        seq[t, FI["w_norm"]]           = w_norm
        seq[t, FI["h_norm"]]           = h_norm
        seq[t, FI["aspect_ratio"]]     = ar
        seq[t, FI["area_norm"]]        = w_norm * h_norm
        seq[t, FI["displacement"]]     = disp
        seq[t, FI["velocity_x"]]       = vx
        seq[t, FI["velocity_y"]]       = vy
        seq[t, FI["speed"]]            = speed
        seq[t, FI["acceleration"]]     = accel
        seq[t, FI["direction_sin"]]    = np.sin(angle)
        seq[t, FI["direction_cos"]]    = np.cos(angle)
        seq[t, FI["movement_variance"]]= mv_var
        seq[t, FI["vertical_ratio"]]   = vert
        seq[t, FI["inactivity"]]       = inactivity
    
    return _add_noise(seq, scale=0.01)   # less noise — IDR is consistent


def generate_dataset(
    n_normal:   int = 800,
    n_distress: int = 600,
    n_drowning: int = 600,
    seed:       int = 42,
    output_dir: str = "data/synthetic",
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a full synthetic dataset and save to .npz.
    
    Class imbalance rationale:
      Normal is over-represented in real pool scenarios (most people swim fine).
      Drowning/Distress are under-represented — hence class weights in training.

    Args:
        n_normal:   Number of normal sequences
        n_distress: Number of distress sequences
        n_drowning: Number of drowning sequences
        seed:       Random seed for reproducibility
        output_dir: Directory to save .npz and metadata.json

    Returns:
        sequences: (N, 32, 16) float32
        labels:    (N,)        int64
    """
    rng = np.random.default_rng(seed)
    
    print(f"Generating dataset (seed={seed}):")
    print(f"  Normal:   {n_normal}")
    print(f"  Distress: {n_distress}")
    print(f"  Drowning: {n_drowning}")
    print(f"  Total:    {n_normal + n_distress + n_drowning}")
    
    sequences = []
    labels    = []
    
    for i in range(n_normal):
        sequences.append(generate_normal_sequence(rng))
        labels.append(LABEL_NORMAL)
    
    for i in range(n_distress):
        sequences.append(generate_distress_sequence(rng))
        labels.append(LABEL_DISTRESS)
    
    for i in range(n_drowning):
        sequences.append(generate_drowning_sequence(rng))
        labels.append(LABEL_DROWNING)
    
    sequences = np.array(sequences, dtype=np.float32)  # (N, 32, 16)
    labels    = np.array(labels,    dtype=np.int64)     # (N,)
    
    # Shuffle
    idx = rng.permutation(len(labels))
    sequences = sequences[idx]
    labels    = labels[idx]
    
    # Save
    out_dir = ROOT / output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out_dir / "sequences.npz",
        sequences=sequences,
        labels=labels,
    )
    
    meta = {
        "description": "Synthetically generated 16-D behavioral feature sequences for AquaGuard AI LSTM training",
        "generation_method": "Physiologically-grounded simulation (Pia 1974 IDR model)",
        "disclaimer": "SYNTHETIC DATA - generated for prototype training. Not real drowning incidents.",
        "seed": seed,
        "total_samples": int(len(labels)),
        "class_distribution": {
            "normal":   int(n_normal),
            "distress": int(n_distress),
            "drowning": int(n_drowning),
        },
        "sequence_length": SEQ_LEN,
        "feature_dimensions": N_FEATURES,
        "label_map": {"0": "normal", "1": "distress", "2": "drowning"},
        "split_strategy": "random (video-level split not applicable for synthetic data)",
    }
    with open(out_dir / "metadata.json", "w") as f:
        json.dump(meta, f, indent=2)
    
    print(f"\nSaved: {out_dir / 'sequences.npz'}")
    print(f"Saved: {out_dir / 'metadata.json'}")
    print(f"Shape: sequences={sequences.shape}, labels={labels.shape}")
    return sequences, labels


if __name__ == "__main__":
    generate_dataset()
