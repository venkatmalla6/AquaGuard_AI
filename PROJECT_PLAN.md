# AquaGuard AI — Project Plan

> **Real-Time Drowning Detection Using Person Tracking and Temporal Behavior Analysis with Edge AI**
> B.Tech CSE Final-Year Research Project & Prototype

---

## 1. Research Question

> "Can temporal behavior analysis combined with person tracking improve the reliability of real-time drowning detection compared with frame-level YOLO detection?"

This is a RESEARCH HYPOTHESIS, not a predetermined conclusion. Experimental results will determine the answer.

---

## 2. Dual Project Goals

1. **Working Prototype** — A deployable, demonstrable AI safety monitoring application.
2. **Research Validation** — Experimentally measured evidence for a B.Tech CSE final-year research paper.

---

## 3. System Architecture

```
CAMERA / VIDEO
    |
VIDEO INGESTION
    |
YOLOv8 PERSON DETECTOR
    |
PERSON TRACKER (ByteTrack)
    |
TRACK HISTORY BUFFER
    |
TEMPORAL FEATURE EXTRACTION
    |
TEMPORAL BEHAVIOR MODEL (LSTM / GRU / Transformer)
    |
BEHAVIOR CLASSIFIER
    |
+----------+----------+
|          |          |
NORMAL   DISTRESS  POTENTIAL DROWNING
                       |
                   ALERT ENGINE
                       |
         +-------------+-------------+
         |             |             |
     Dashboard     Buzzer/LED   Notification
```

---

## 4. Behavior Classes

| Class | Code | Definition |
|---|---|---|
| Normal | 0 | Regular swimming, floating — no distress signs |
| Distress | 1 | Irregular movement, unusual posture, early distress |
| Potential Drowning | 2 | Vertical body, minimal movement, head submerging |

---

## 5. Technology Stack

**Frontend**: React + Vite + TypeScript + Tailwind CSS + shadcn/ui + Recharts + Lucide + Zustand

**Backend**: Python + FastAPI + Pydantic v2 + SQLModel + PostgreSQL + JWT + WebSocket

**AI/CV**: Ultralytics YOLOv8 + ByteTrack + PyTorch (LSTM/GRU/Transformer) + OpenCV + NumPy

**Infrastructure**: Git + Docker (when available) + .env config + loguru

---

## 6. Experiments

| ID | Name | Detector | Tracker | Temporal |
|---|---|---|---|---|
| EXP-A | Baseline | YOLOv8 | None | None |
| EXP-B | +Tracking | YOLOv8 | ByteTrack | None |
| EXP-C | Proposed | YOLOv8 | ByteTrack | LSTM |
| EXP-D | +GRU | YOLOv8 | ByteTrack | GRU |
| EXP-E | +Transformer (optional) | YOLOv8 | ByteTrack | Transformer |

---

## 7. Development Phases

Phase 1: Architecture & Planning (IN PROGRESS)
Phase 2: Backend foundation
Phase 3: YOLO baseline detector
Phase 4: Video processing pipeline
Phase 5: Person tracking
Phase 6: Temporal feature extraction
Phase 7: LSTM/GRU temporal model
Phase 8: Alert engine
Phase 9: React dashboard
Phase 10: Research experiment module
Phase 11: Database integration
Phase 12: IoT simulation
Phase 13: Testing
Phase 14: Performance optimization
Phase 15: Research evaluation
Phase 16: Documentation

---

## 8. Research Ethics

- This is a safety prototype, NOT a replacement for trained lifeguards.
- No guaranteed drowning prevention is claimed.
- All experiments use simulated/publicly available data.
- No fabricated results in any form.

---

*Created: 2026-09-18 | AquaGuard AI*
