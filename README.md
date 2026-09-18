# AquaGuard AI

## Real-Time Drowning Detection Using Person Tracking and Temporal Behavior Analysis with Edge AI

**B.Tech CSE Final-Year Research Project**

---

## Research Objective

> "Can temporal behavior analysis combined with person tracking improve the
> reliability of real-time drowning detection compared with frame-level YOLO detection?"

---

## System Architecture

`
Camera/Video → YOLOv8 → ByteTrack → Feature Extraction → LSTM → Alert
`

---

## Technology Stack

- **Frontend**: React + Vite + TypeScript + Tailwind CSS + Recharts
- **Backend**: Python + FastAPI + SQLModel + WebSocket
- **AI**: YOLOv8 + ByteTrack + PyTorch LSTM/GRU
- **Database**: SQLite (dev) → PostgreSQL (production)

---

## Quick Start

### Backend

`ash
cd backend
pip install -r requirements.txt
python run.py
`

API docs: http://localhost:8000/docs

### Frontend

`ash
cd frontend
npm install
npm run dev
`

App: http://localhost:5173

---

## Research Experiments

| ID | Name | Detector | Tracker | Temporal |
|---|---|---|---|---|
| EXP-A | Baseline | YOLOv8 | None | None |
| EXP-B | +Tracking | YOLOv8 | ByteTrack | None |
| EXP-C | Proposed | YOLOv8 | ByteTrack | LSTM |

---

## Project Structure

`
AquaGuard_AI/
├── frontend/          React dashboard
├── backend/           FastAPI server
├── ai/                CV & AI modules
├── experiments/       Experiment configs & results
├── data/              Datasets
├── config/            Configuration files
├── docs/              Documentation
└── research/          Research outputs
`

---

## Important Research Notes

- **No fabricated results**: All metrics come from actual experiments.
- **Simulated scenarios**: No real drowning experiments performed.
- **Ethical use**: This prototype supplements, not replaces, lifeguards.

---

*AquaGuard AI © 2026 — B.Tech CSE Research Project*
