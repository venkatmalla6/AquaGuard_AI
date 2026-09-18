# Research Gap

## Previous System (Baseline)

The senior/previous project used a YOLOv8-based frame-level detection approach:

Camera → YOLO → Drowning Detection → Alert

**Limitation**: Frame-level detection treats each frame independently.
It cannot distinguish between similar instantaneous postures such as:
- A person floating (normal) vs. a person face-down (potential drowning)
- A person jumping in vs. a person who has stopped moving

## Identified Research Gap

Frame-level object detection may not fully capture the temporal nature
of drowning-related behavior. Drowning is a process, not a single frame.

Key behaviors that require temporal analysis:
1. Progressive reduction in movement over time
2. Transition from normal → distress → drowning
3. Duration of inactivity
4. Change in body posture over time (aspect ratio change)

## Proposed Solution

Combining:
1. YOLO person detection (spatial information)
2. ByteTrack multi-object tracking (identity continuity)
3. Temporal feature extraction (motion history)
4. LSTM temporal model (sequential pattern recognition)

## Research Hypothesis

> Temporal behavior analysis combined with person tracking will provide
> more reliable drowning detection than frame-level detection alone.

**This is a hypothesis — not a conclusion.**
The experimental results will determine whether this hypothesis holds.

## Evaluation Plan

Experiments A vs C:
- EXP-A: YOLOv8 baseline (frame-level)
- EXP-C: YOLOv8 + ByteTrack + LSTM (temporal)

Comparison metrics: Precision, Recall, F1, FPR, FNR, FPS, Latency
