# AquaGuard AI

## Real-Time Drowning Detection Using Person Tracking and Temporal Behavior Analysis with Edge AI

**B.Tech CSE Final-Year Research Project & Prototype**

> 📘 **MASTER SPECIFICATION & TRACKER:**
> For the comprehensive master prompt, research methodology, full 16-phase roadmap,
> codebase inventory, and build/verification guide, see **[MASTER_REFERENCE.md](MASTER_REFERENCE.md)**.

---

## Research Objective

> "Can temporal behavior analysis combined with person tracking improve the
> reliability of real-time drowning detection compared with frame-level YOLO detection?"

---

## System Architecture

```
Camera / Video Stream
        │
     YOLOv8n (Spatial Person Detection)
        │
    ByteTrack (Multi-Person Tracking)
        │
16-D Feature Extraction (Velocities, Posture, Submersion, Motion)
        │
   Bi-LSTM / GRU (Behavior Sequence Classifier)
        │
   Alert Engine (Multi-Frame Hysteresis & Cooldown)
        │
┌───────┴───────┐
▼               ▼
FastAPI REST    WebSocket Real-Time Push (30 FPS)
SQLite DB       React 18 + Vite + Tailwind Dashboard
```

---

## Technology Stack

- **Frontend**: React 18 + Vite 6 + TypeScript + Tailwind CSS v4 + Recharts + Lucide Icons
- **Backend**: Python 3.13 + FastAPI + SQLModel + SQLAlchemy 2.0 + WebSockets
- **AI/CV**: Ultralytics YOLOv8n + ByteTrack + PyTorch (Bi-LSTM / GRU) + OpenCV
- **Database**: SQLite (local development) / PostgreSQL (production)

---

## Quick Start

### 1. Backend Server
```powershell
cd backend
python run.py
```
- **API Server**: http://localhost:8000
- **Swagger Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 2. Frontend Development Server
```powershell
cd frontend
npm run dev
```
- **Web Dashboard**: http://localhost:5173
- **Demo Credentials**:
  - Administrator: `admin@aquaguard.ai` / `admin123`
  - Lifeguard / Operator: `operator@aquaguard.ai` / `operator123`
  - Research Scientist: `researcher@aquaguard.ai` / `research123`

---

## Research Experiments

| ID | Title | Detector | Tracker | Temporal Model | Status |
|---|---|---|---|---|---|
| **EXP-A** | Spatial Baseline | YOLOv8n | None | None | Ready for evaluation |
| **EXP-B** | Tracking + Heuristics | YOLOv8n | ByteTrack | Rule-Based | Ready for evaluation |
| **EXP-C** | Proposed Architecture | YOLOv8n | ByteTrack | 16-D Features + Bi-LSTM | Architecture implemented |
| **EXP-D** | Model Ablation (GRU) | YOLOv8n | ByteTrack | 16-D Features + GRU | Architecture implemented |
| **EXP-E** | Window Size Ablation | YOLOv8n | ByteTrack | Bi-LSTM (T=15, 30, 60) | Architecture implemented |

---

## Project Structure

```
AquaGuard_AI/
├── MASTER_REFERENCE.md      # COMPLETE master prompt, roadmap & verification reference
├── DEVELOPMENT_STATUS.md    # Phase-by-phase status tracking
├── PROJECT_PLAN.md          # High-level architecture and concepts
├── config/config.yaml       # Master AI, CV & system configuration
├── backend/                 # FastAPI REST & WebSocket application
├── frontend/                # React 18 + Vite + Tailwind CSS dashboard
├── ai/                      # YOLO, ByteTrack, 16-D Features, LSTM modules
├── experiments/             # Experiment configs (EXP-A, EXP-C) & benchmark scripts
├── docs/research/           # Academic research gap analysis
└── data/                    # Test video sequences and output metrics
```

---

## Important Research Guidelines

- **Zero Fabricated Results**: Under no circumstances will performance metrics be mocked or fabricated. All numbers in academic tables must originate from real benchmark runs.
- **CPU Edge Optimization**: Designed and verified to run on standard multicore CPUs (>= 15 FPS) without requiring CUDA/NVIDIA GPU hardware.
- **Safety Prototype**: Designed to supplement and support human lifeguards, not replace trained personnel.

---

*AquaGuard AI © 2026 — B.Tech Computer Science Engineering Final-Year Research Project*