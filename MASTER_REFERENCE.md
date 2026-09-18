# ==============================================================================
# AQUAGUARD AI — MASTER SPECIFICATION, ROADMAP & STATUS REFERENCE
# ==============================================================================
# Project: Real-Time Drowning Detection Using Person Tracking and Temporal
#          Behavior Analysis with Edge AI
# Scope:   B.Tech Computer Science Engineering Final-Year Research Project & Prototype
# Target:  Dual Goal — (1) Working Software Application + (2) Validated Research Paper
# Path:    D:\Btech\PROJECTS\AquaGuard_AI
# ==============================================================================

> **PURPOSE OF THIS DOCUMENT:**
> This file is the single authoritative reference for **AquaGuard AI**. Whenever a developer,
> evaluator, or AI coding assistant opens this repository to build, run, or extend the project,
> this file provides:
> 1. The full **Master Prompt & Academic Requirements** that define the project scope.
> 2. An exact account of **What Has Been Completed** (architecture, files, schemas, modules).
> 3. An exhaustive roadmap of **What Needs to Be Developed** across all 16 phases.
> 4. A **Build & Verification Guide** to test the system step-by-step.
> 5. The **Research Experiment Matrix** and strict scientific integrity guidelines.

---

## TABLE OF CONTENTS
1. [Executive Summary & Dual Goals](#1-executive-summary--dual-goals)
2. [Master Prompt & Core Research Specifications](#2-master-prompt--core-research-specifications)
3. [System Architecture & Data Flow](#3-system-architecture--data-flow)
4. [What Has Been Completed (Current Progress)](#4-what-has-been-completed-current-progress)
5. [What Needs to Be Developed (16-Phase Roadmap)](#5-what-needs-to-be-developed-16-phase-roadmap)
6. [Complete Codebase & File Inventory](#6-complete-codebase--file-inventory)
7. [Research Experiments & Academic Methodology](#7-research-experiments--academic-methodology)
8. [How to Build, Run & Verify the Project](#8-how-to-build-run--verify-the-project)
9. [Immediate Next Steps (Sprint Plan)](#9-immediate-next-steps-sprint-plan)

---

## 1. EXECUTIVE SUMMARY & DUAL GOALS

**AquaGuard AI** is a real-time computer vision and temporal deep learning system designed
to detect swimmer distress and potential drowning in aquatic facilities (public pools, resorts,
water parks).

Unlike typical software demos, this project serves **TWO SIMULTANEOUS OBJECTIVES**:

1. **A Production-Grade Prototype Application:**
   - Real-time video processing pipeline capable of handling IP camera RTSP streams and uploaded test videos.
   - Low-latency edge inference on CPU hardware (>= 15 FPS).
   - Interactive full-stack web dashboard (React 18 + Vite + Tailwind CSS + FastAPI + WebSockets).
   - Audio/visual alert engine with automated triage, logging, and historical playback.

2. **A Peer-Reviewable B.Tech Final-Year Research Paper:**
   - Scientifically grounded hypothesis comparing spatial vs. temporal architectures.
   - Formal ablation studies (LSTM vs. GRU vs. rule-based heuristics).
   - Strict adherence to academic integrity: **ZERO fabricated or hallucinated benchmark numbers**.
   - Clear documentation of the research gap, methodology, failure cases, and real measured results.

---

## 2. MASTER PROMPT & CORE RESEARCH SPECIFICATIONS

### 2.1 The Research Problem & Gap Analysis
According to the World Health Organization (WHO), drowning claims more than 236,000 lives each year.
In aquatic environments, human lifeguards face cognitive fatigue, optical reflections, occlusions,
and delayed reaction times.

Existing automated surveillance systems overwhelmingly rely on **frame-level object detection**
(e.g., standard YOLO bounding boxes). This paradigm fails in practice due to three fundamental flaws:
1. **High False Positive Rate (FPR):** Normal active swimming, vigorous kicking, splashing, and
   diving exhibit high motion energy that frame-level detectors frequently mistake for distress.
2. **Fatal False Negative Rate (FNR):** A submerged or motionless person floating near the surface
   is either detected simply as a generic "person" or missed entirely once partially occluded by water.
3. **Absence of Temporal Memory:** A single 33 ms video frame contains no historical context. A frame
   detector cannot distinguish between a swimmer pausing for 2 seconds to breathe versus an unconscious
   individual motionless for 15 seconds.

### 2.2 Core Research Hypothesis
> **Scientific Hypothesis ($H_1$):**
> *"Combining real-time multi-person tracking (ByteTrack) with a 16-dimensional temporal feature
> extraction pipeline and sequence modeling (Bi-LSTM / GRU) across a sliding temporal window
> significantly reduces false alarm rates (FAR) while maintaining high detection recall (>90%)
> for aquatic distress and drowning states compared to spatial-only YOLO baselines."*

### 2.3 Behavior Classes & State Machine
The system tracks each person continuously and classifies their behavioral state into three categories:

| Class ID | Label | Behavioral Indicators & Criteria | Severity | System Action |
|:---:|:---|:---|:---:|:---|
| **0** | **Normal** | Horizontal body posture ($w/h > 1.0$), steady swimming velocity ($>0.3$ m/s proxy), consistent stroke frequency, periodic surfacing | Normal | Green bounding box; log telemetry |
| **1** | **Distress** | Rapid irregular limb movement, sudden deceleration, vertical torso tilt ($>60^\circ$), excessive surface splashing, erratic trajectory | Warning | Amber bounding box; start persistence counter |
| **2** | **Potential Drowning** | Vertical or submerged posture, prolonged immobility ($>3.5$ s), head below waterline, zero forward velocity, collapsing bounding box | Critical Alert | Red flashing strobe; audible siren; dispatch alert event |

### 2.4 The 16-Dimensional Temporal Feature Vector
For each tracked person ID $i$ across sliding sequence window $T = 30$ frames (1.0 second at 30 FPS),
the system extracts a 16-dimensional feature vector at each time step $t$:

```
Feature Vector = [
    f1:  norm_center_x,        # Bounding box center X normalized (0.0 to 1.0)
    f2:  norm_center_y,        # Bounding box center Y normalized (0.0 to 1.0)
    f3:  norm_width,           # Bounding box width normalized by frame width
    f4:  norm_height,          # Bounding box height normalized by frame height
    f5:  aspect_ratio,         # Box width / height (w/h > 1 = swimming, w/h < 0.6 = vertical)
    f6:  velocity_x,           # Horizontal displacement dx / dt
    f7:  velocity_y,           # Vertical displacement dy / dt (sinking indicator)
    f8:  speed,                # Planar velocity magnitude: sqrt(vx^2 + vy^2)
    f9:  acceleration,         # Rate of change of speed (frantic thrashing cue)
    f10: area_change_rate,     # Relative change in bounding box area: dArea / Area
    f11: verticality_score,    # Vertical posture indicator: h / (w + h)
    f12: motion_energy,        # Frame-to-frame pixel difference / bounding box optical flow proxy
    f13: inactivity_duration,  # Elapsed seconds where speed remains below threshold (tau < 0.05)
    f14: submersion_proxy,     # Joint indicator of aspect ratio drop + downward centroid shift
    f15: trajectory_smoothness,# Curvature / path directional variance (linear swim vs erratic)
    f16: detection_confidence  # YOLOv8 detector confidence score c in [0, 1]
]
```

### 2.5 Academic Integrity & Anti-Fabrication Rule
- **Mandatory Policy:** Under NO circumstances will the system or documentation present fabricated,
  hardcoded, or synthetic benchmark tables as "real experimental results."
- All precision, recall, F1, mAP, and latency metrics presented in research tables MUST originate from
  actual test runs executed on real or publicly available benchmark datasets.
- Placeholder metrics before experimentation are explicitly marked as `Pending Experiment Run`.

---

## 3. SYSTEM ARCHITECTURE & DATA FLOW

```
                          +-------------------------------+
                          |  VIDEO SOURCE (RTSP / FILE)  |
                          +---------------+---------------+
                                          |
                                          v
                      [ PHASE 4 & 5: INGESTION PIPELINE ]
                      - OpenCV VideoCapture (30 FPS)
                      - Frame Resizing & Normalization (640x360)
                                          |
                                          v
                         [ PHASE 3: SPATIAL DETECTION ]
                         - YOLOv8n (Ultralytics nano model)
                         - Person Filter (class=0, conf >= 0.35)
                         - Bounding Boxes: [x1, y1, x2, y2, conf]
                                          |
                                          v
                        [ PHASE 5: MULTI-OBJECT TRACKING ]
                        - ByteTrack Data Association
                        - Kalman Filter State Prediction
                        - Stable Track IDs across Occlusions
                                          |
                                          v
                     [ PHASE 6: TEMPORAL FEATURE EXTRACTION ]
                     - 16-Dimensional Feature Vector per Track ID
                     - Rolling Sequence Buffer (T = 30 frames)
                                          |
                                          v
                     [ PHASE 7: BEHAVIOR SEQUENCE CLASSIFIER ]
                     - PyTorch Bi-LSTM / GRU Neural Network
                     - Softmax Class Probabilities:
                       [P(Normal), P(Distress), P(Drowning)]
                                          |
                                          v
                         [ PHASE 8: ALERT LOGIC ENGINE ]
                         - Consecutive Frame Persistence (N >= 8 frames)
                         - Hysteresis De-bouncing & Cooldown
                         - Alert State Machine (IDLE -> WARNING -> CRITICAL)
                                          |
                  +-----------------------+-----------------------+
                  |                                               |
                  v                                               v
     [ PERSISTENCE & AUDIT ]                         [ REAL-TIME BROADCAST ]
     - FastAPI REST API                              - WebSocket Server (30 FPS)
     - SQLite Database (13 Tables)                   - Live Bounding Box Metadata
     - Incident Logs & Snapshots                     - Instantaneous Alert Push
                  |                                               |
                  +-----------------------+-----------------------+
                                          |
                                          v
                       [ PHASE 9: FULL-STACK REACT DASHBOARD ]
                       - Dark Slate & Vivid Cyan UI Design System
                       - Live Camera Surveillance & Overlays
                       - Active Incident Desk with Acknowledgment
                       - Research Experiment Benchmarking UI
```

---

## 4. WHAT HAS BEEN COMPLETED (CURRENT PROGRESS)

### 4.1 Completed Phases Summary
- **Phase 1: Architecture, Planning & Environment Setup** — **100% COMPLETE**
- **Phase 2: Backend Architecture & AI Modules** — **100% COMPLETE**
- **Phase 3: Frontend Architecture & Design System** — **100% COMPLETE**
- **Active Running Daemons:**
  - **Backend Server:** FastAPI Uvicorn running on `http://localhost:8000` (docs at `http://localhost:8000/docs`)
  - **Frontend Dev Server:** Vite 6 + React 18 running on `http://localhost:5173`

### 4.2 Detailed Inventory of Completed Deliverables

#### Configuration & Environment
- [x] `config/config.yaml`: Centralized configuration defining video resolution, YOLO parameters, ByteTrack tracker buffers, 16 temporal feature toggles, LSTM hyperparameters, alert thresholds, and experiment matrices.
- [x] `.env.example` & `.gitignore`: Standard environment templates and comprehensive ignore rules.
- [x] `backend/app/core/config.py`: Pydantic BaseSettings class loading environment variables, JWT secrets, CORS allowances, and database paths.
- [x] `backend/app/database/db.py`: Async SQLite engine using SQLAlchemy 2.0 and SQLModel with automatic schema initialization.
- [x] `backend/run.py`: Uvicorn launch runner configured for async reload.

#### Database Schemas (13 SQLModel Tables in `backend/app/models/models.py`)
- [x] `User`: Role-based access control (Admin, Operator, Researcher) with hashed passwords.
- [x] `Camera`: RTSP/Webcam stream configurations with resolution, target FPS, and operational status.
- [x] `DetectionZone`: Multi-point polygon zones defining shallow vs. deep pool regions.
- [x] `VideoUpload`: Metadata for uploaded benchmark video files with frame counts and processing flags.
- [x] `TrackedPerson`: Persistent swimmer entities with first/last seen timestamps and peak risk score.
- [x] `PersonTrackFrame`: Per-frame coordinate records with velocity and bounding box dimensions.
- [x] `TemporalFeatureRecord`: All 16 normalized feature values stored per frame for academic export.
- [x] `Alert`: Incidents categorized by severity (`WARNING`, `CRITICAL`) with snapshot paths and triage state.
- [x] `AlertEvent`: Granular timeline log of all state transitions per alert.
- [x] `Experiment`: Research experiment definitions (EXP-A through EXP-E).
- [x] `ExperimentRun`: Individual test runs mapped to specific video datasets and model checkpoints.
- [x] `ExperimentMetric`: Verified quantitative evaluation records (Precision, Recall, F1, Latency, FPS).
- [x] `SystemMetric`: Hardware telemetry records (CPU %, RAM %, inference time per frame).

#### AI & Computer Vision Core Pipeline
- [x] `ai/detection/detector.py`: `YOLODetector` class wrapping YOLOv8n with normalized outputs, confidence filtering, and non-blocking inference.
- [x] `ai/tracking/tracker.py`: `PersonTracker` class wrapping ByteTrack multi-object tracking with track confirmation and loss buffers.
- [x] `ai/features/feature_extractor.py`: `TrackFeatureExtractor` computing the full 16-D temporal feature vector across rolling frame windows.
- [x] `ai/temporal/lstm_model.py`: PyTorch `BehaviorClassifier` neural network implementing 2-layer Bidirectional LSTM and GRU sequence architectures with Dropout and Softmax classification.
- [x] `ai/evaluation/alert_engine.py`: `AlertEngine` implementing hysteresis de-bouncing, multi-frame persistence checking ($N \ge 8$), cooldown timers, and severity escalation.

#### Frontend Application (`frontend/`)
- [x] Vite + React 18 + TypeScript setup with path aliases (`@/*`).
- [x] Tailwind CSS v4 design system configured with custom CSS tokens in `src/index.css`:
  - Oceanic dark palette: Background `#020617` (slate-950), Sidebar `#0f172a` (slate-900), Surface `#1e293b`.
  - Neon cyan accent: `#00b5d4` / `#06b6d4`.
  - Glassmorphic card styling (`glass-card`) and pulsating critical alert animations (`alert-pulse`).
- [x] Global TypeScript interfaces (`src/types/index.ts`) matching backend SQLModel schemas.
- [x] Axios API client (`src/services/api.ts`) with request interceptors for JWT authorization.
- [x] Auto-reconnecting WebSocket hook (`src/hooks/useWebSocket.ts`) with exponential backoff.
- [x] App shell layout (`src/layouts/MainLayout.tsx`) featuring collapsible sidebar, system status beacon, and alert counters.
- [x] Reusable UI components: `StatCard.tsx`, `StatusBadge.tsx`, `LoadingSpinner.tsx`.
- [x] **Pages Implemented:**
  - `src/pages/LoginPage.tsx`: Glassmorphic login with 1-click role demo credentials.
  - `src/pages/DashboardPage.tsx`: Full operational overview with live metrics, active swimmers grid, system health panel, and critical alert banner.
  - Placeholder scaffolding for `LiveMonitoringPage`, `VideoTestingPage`, `AlertsPage`, `PeopleTrackingPage`, `ResearchPage`, and `SystemPage`.

---

## 5. WHAT NEEDS TO BE DEVELOPED (16-PHASE ROADMAP)

The following table provides the complete status and roadmap for all 16 phases of AquaGuard AI:

| Phase | Phase Title | Primary Focus & Deliverables | Status |
|:---:|:---|:---|:---:|
| **1** | **Architecture & Planning** | Research gap analysis, system requirements, project structure, environment check | **COMPLETE** |
| **2** | **Backend Foundation** | Async database, 13 SQLModel tables, FastAPI lifespan, AI modules | **COMPLETE** |
| **3** | **Frontend Foundation** | React+TS scaffold, Tailwind tokens, Router, Type system, Dashboard & Login | **COMPLETE** |
| **4** | **REST & Auth API Routes** | JWT authentication, Camera CRUD, Alert triage, Experiment endpoints | **IN PROGRESS** |
| **5** | **Video Ingestion Pipeline** | Upload handler, frame generator, background queue, video storage | **PENDING** |
| **6** | **Live Tracking & Feature Integration**| End-to-end integration of Detector + Tracker + Feature Extractor | **PENDING** |
| **7** | **Temporal Model Training Pipeline** | Synthetic/public dataset sequence generator, train loop, PyTorch weights | **PENDING** |
| **8** | **Real-Time WebSocket Streamer** | Low-latency binary/base64 frame broadcast with track annotations | **PENDING** |
| **9** | **Full Frontend Page Implementations**| Connect 7 placeholder pages to live REST and WebSocket APIs | **PENDING** |
| **10**| **Automated Research Benchmark Suite**| Automated runner for EXP-A through EXP-E with metric export | **PENDING** |
| **11**| **Alert Notification & Dispatch** | Web Audio siren, browser push notification, email/webhook mock | **PENDING** |
| **12**| **Edge Optimization (CPU Focus)** | TorchScript / ONNX export, frame skipping, OpenCV optimizations | **PENDING** |
| **13**| **Comprehensive Testing Suite** | Pytest unit tests, CV pipeline tests, API route tests, Vitest UI | **PENDING** |
| **14**| **Synthetic Data & Scenarios Engine** | Generator for normal swimming vs distress vs motionless sequences | **PENDING** |
| **15**| **Paper Assets & Visualizations** | Precision-Recall curves, confusion matrices, latency vs FPS plots | **PENDING** |
| **16**| **Documentation & B.Tech Defense Pack**| Thesis chapters, viva presentation slides, user guide, API docs | **PENDING** |

---

### Detailed Task Specifications for Upcoming Phases:

#### Phase 4: REST & WebSocket API Routes (Current Sprint)
- [ ] `backend/app/api/deps/auth.py`: JWT token decoder, password hashing utilities, current user dependency.
- [ ] `backend/app/api/routes/auth.py`:
  - `POST /api/auth/login`: Authenticate and issue access token.
  - `GET /api/auth/me`: Retrieve current user profile and assigned role.
- [ ] `backend/app/api/routes/cameras.py`:
  - `GET /api/cameras`: List all registered cameras.
  - `POST /api/cameras`: Register a new IP camera or webcam stream.
  - `GET /api/cameras/{id}`: Detailed camera configuration and status.
  - `DELETE /api/cameras/{id}`: Remove camera.
- [ ] `backend/app/api/routes/alerts.py`:
  - `GET /api/alerts`: Query alert history with status and severity filters.
  - `POST /api/alerts/{id}/acknowledge`: Mark alert as seen by operator.
  - `POST /api/alerts/{id}/resolve`: Mark alert resolved with incident notes.
- [ ] `backend/app/api/routes/experiments.py`:
  - `GET /api/experiments`: List all registered research experiments.
  - `POST /api/experiments/run`: Launch automated test run against benchmark dataset.
  - `GET /api/experiments/{id}/metrics`: Fetch quantitative comparison metrics.
- [ ] `backend/app/api/routes/system.py`:
  - `GET /api/system/status`: Real-time CPU utilization, RAM usage, and inference latency.

#### Phase 5: Video Processing & Frame Ingestion
- [ ] `backend/app/api/routes/videos.py`: Video file upload endpoint supporting `.mp4`, `.avi`, `.mov`.
- [ ] `ai/pipeline/video_processor.py`: Asynchronous OpenCV video reader, frame-by-frame generator.
- [ ] Processing progress reporter via database status and WebSocket updates.

#### Phase 6: End-to-End Tracking & Feature Pipeline Integration
- [ ] Pipeline orchestrator combining:
  `Raw Frame -> YOLODetector -> PersonTracker -> TrackFeatureExtractor -> Feature Tensor`
- [ ] Maintain active in-memory track states with automated memory eviction for stale tracks.

#### Phase 7: Behavior Model Weights & Training Harness
- [ ] Generate synthetic sequence training data representing normal swimming, frantic distress, and sinking immobility.
- [ ] Implement training script `ai/temporal/train_lstm.py` with loss curves and validation metrics.
- [ ] Export trained weights checkpoint to `ai/models/behavior_lstm.pt`.

#### Phase 8: Real-Time WebSocket Streaming Server
- [ ] Implement `/ws/stream/{camera_id}` for video frame streaming + bounding box metadata.
- [ ] Implement `/ws/alerts` for instantaneous push notifications to all connected clients.

#### Phase 9: Full Frontend Page Implementations
- [ ] `LiveMonitoringPage`: Render canvas-based bounding box overlays with color-coded risk levels.
- [ ] `VideoTestingPage`: Drag-and-drop video upload with real-time processing timeline.
- [ ] `AlertsPage`: Filterable incident triage table with snapshot modal view.
- [ ] `ResearchPage`: Interactive Recharts comparison plots showing Precision, Recall, and Latency across EXP-A, EXP-B, and EXP-C.
- [ ] Web Audio API siren alert implementation.

---

## 6. COMPLETE CODEBASE & FILE INVENTORY

```
D:\Btech\PROJECTS\AquaGuard_AI\
|-- .env.example                         <- Template for environment configuration
|-- .gitignore                           <- Git exclusion rules
|-- DEVELOPMENT_STATUS.md                <- Phase completion checklist
|-- MASTER_REFERENCE.md                  <- THIS COMPLETE MASTER REFERENCE FILE
|-- PROJECT_PLAN.md                      <- High-level concept summary
|-- README.md                            <- Quickstart guide for developers
|
|-- config/
|   `-- config.yaml                      <- Master AI/CV and system configuration
|
|-- backend/
|   |-- requirements.txt                 <- Python dependencies
|   |-- run.py                           <- Uvicorn server launcher
|   `-- app/
|       |-- main.py                      <- FastAPI application entry point
|       |-- core/
|       |   `-- config.py                <- Pydantic settings & env variables
|       |-- database/
|       |   `-- db.py                    <- Async SQLite session engine
|       |-- models/
|       |   `-- models.py                <- 13 SQLModel database tables
|       `-- api/
|           |-- deps/                    <- Route dependencies (auth, db session)
|           `-- routes/                  <- REST API endpoints (Phase 4)
|
|-- ai/
|   |-- detection/
|   |   `-- detector.py                  <- YOLOv8 person detector wrapper
|   |-- tracking/
|   |   `-- tracker.py                   <- ByteTrack multi-person tracker
|   |-- features/
|   |   `-- feature_extractor.py         <- 16-D temporal feature extractor
|   |-- temporal/
|   |   `-- lstm_model.py                <- Bi-LSTM / GRU PyTorch behavior model
|   `-- evaluation/
|       `-- alert_engine.py              <- Multi-frame alert logic & hysteresis
|
|-- experiments/
|   `-- configs/
|       |-- exp_a_baseline.yaml          <- Spatial YOLO baseline configuration
|       `-- exp_c_proposed.yaml          <- Proposed YOLO+ByteTrack+LSTM config
|
|-- docs/
|   `-- research/
|       `-- RESEARCH_GAP.md              <- Literature review & research gap analysis
|
`-- frontend/
    |-- package.json                     <- Node.js dependencies
    |-- vite.config.ts                   <- Vite build configuration & proxy
    |-- src/
        |-- main.tsx                     <- React DOM root
        |-- App.tsx                      <- React Router configuration
        |-- index.css                    <- Tailwind v4 & custom design tokens
        |-- types/
        |   `-- index.ts                 <- TypeScript interfaces
        |-- services/
        |   `-- api.ts                   <- Axios HTTP client
        |-- hooks/
        |   `-- useWebSocket.ts          <- Reconnecting WebSocket hook
        |-- layouts/
        |   `-- MainLayout.tsx           <- Sidebar + Navigation wrapper
        |-- components/common/
        |   |-- StatCard.tsx             <- Metric display card
        |   |-- StatusBadge.tsx          <- Severity indicator badge
        |   `-- LoadingSpinner.tsx       <- Loading animation
        `-- pages/
            |-- LoginPage.tsx            <- Glassmorphic login
            |-- DashboardPage.tsx        <- Operational command dashboard
            |-- LiveMonitoringPage.tsx   <- Real-time CCTV viewer
            |-- VideoTestingPage.tsx     <- Video file testing
            |-- AlertsPage.tsx           <- Incident triage desk
            |-- PeopleTrackingPage.tsx   <- Swimmer trajectory inspector
            |-- ResearchPage.tsx         <- Academic experiment comparison
            `-- SystemPage.tsx           <- CPU/RAM edge hardware monitor
```

---

## 7. RESEARCH EXPERIMENTS & ACADEMIC METHODOLOGY

To satisfy B.Tech CSE thesis criteria, the system is designed to execute five structured experiments:

| Experiment ID | Title | Detector | Tracker | Temporal Model | Scientific Purpose |
|:---|:---|:---:|:---:|:---:|:---|
| **EXP-A** | **Spatial Baseline** | YOLOv8n | None | None | Benchmark standard frame-level YOLO failure modes |
| **EXP-B** | **Tracking + Heuristics**| YOLOv8n | ByteTrack | Rule-Based | Evaluate trajectory continuity without deep learning |
| **EXP-C** | **Proposed Architecture**| YOLOv8n | ByteTrack | Bi-LSTM (2-layer) | Validate primary research hypothesis |
| **EXP-D** | **Model Ablation: GRU** | YOLOv8n | ByteTrack | GRU (2-layer) | Compare LSTM vs GRU latency and parameter efficiency |
| **EXP-E** | **Window Ablation** | YOLOv8n | ByteTrack | Bi-LSTM ($T \in \{15, 30, 60\}$) | Identify optimal temporal receptive field |

### Evaluation Metrics Tracked:
1. **Precision ($P$):** Proportion of detected drowning events that were true emergencies.
2. **Recall ($R$ / Sensitivity):** Proportion of actual drowning events successfully flagged.
3. **$F_1$-Score:** Harmonic mean of Precision and Recall ($2 \cdot \frac{P \cdot R}{P + R}$).
4. **False Alarm Rate (FAR):** Number of false positive alerts per monitored operating hour.
5. **Mean Time to Alert (MTTA):** Average time in seconds from onset of distress to critical alarm.
6. **Inference Latency:** Average processing time per frame in milliseconds on edge CPU.
7. **Throughput:** Processed frames per second (FPS).

> **Academic Rule:** When writing the B.Tech project thesis or paper draft, populate metric tables
> solely from recorded `ExperimentMetric` records generated by running the automated benchmark suite.

---

## 8. HOW TO BUILD, RUN & VERIFY THE PROJECT

### 8.1 Environment Requirements
- **Operating System:** Windows 10/11
- **Python:** Version 3.11, 3.12, or 3.13 (Python 3.13.7 verified working)
- **Node.js:** Version 18+ (Node.js v25.5.0 and npm 11.8.0 verified working)
- **Hardware Mode:** CPU Execution (no NVIDIA GPU or CUDA required)

### 8.2 Starting the Backend Server
1. Open PowerShell and navigate to the backend directory:
   ```powershell
   cd D:\Btech\PROJECTS\AquaGuard_AI\backend
   ```
2. Launch the backend server:
   ```powershell
   python run.py
   ```
3. Verify backend output:
   - Server runs on: `http://localhost:8000`
   - Interactive Swagger API Documentation: `http://localhost:8000/docs`
   - Health check endpoint: `http://localhost:8000/health`

### 8.3 Starting the Frontend Development Server
1. Open a second PowerShell terminal and navigate to the frontend directory:
   ```powershell
   cd D:\Btech\PROJECTS\AquaGuard_AI\frontend
   ```
2. Launch Vite development server:
   ```powershell
   npm run dev
   ```
3. Open a web browser to: `http://localhost:5173`

### 8.4 Preconfigured Demo Credentials
On the login screen (`http://localhost:5173/login`), use the 1-click preset buttons or manual login:
- **Administrator:** `admin@aquaguard.ai` / `admin123`
- **Lifeguard / Operator:** `operator@aquaguard.ai` / `operator123`
- **Research Scientist:** `researcher@aquaguard.ai` / `research123`

### 8.5 Verification Checklist
Whenever you want to verify the system's operational integrity, check off the following:
- [ ] **Backend Health:** `curl http://localhost:8000/health` returns `{"status":"healthy","app":"AquaGuard AI"}`.
- [ ] **Database File:** Ensure `backend/aquaguard.db` exists and has table schemas initialized.
- [ ] **Frontend Compilation:** Ensure `http://localhost:5173` loads without Vite compilation errors.
- [ ] **Authentication Flow:** Click the "Operator" demo button and log in. Verify redirection to `/dashboard`.
- [ ] **Dashboard Elements:** Confirm that Stat Cards, System Status (Online), Swimmer Tracking grid, and Alert Banner render properly.
- [ ] **Navigation Shell:** Confirm sidebar links navigate smoothly across the 7 application views.

---

## 9. IMMEDIATE NEXT STEPS (SPRINT PLAN)

To continue development toward a fully functional end-to-end prototype:

1. **Implement Phase 4 REST Routes:**
   - Create `backend/app/api/deps/auth.py` for JWT validation.
   - Create `backend/app/api/routes/auth.py` for `/api/auth/login` and `/api/auth/me`.
   - Create `backend/app/api/routes/cameras.py` for camera feed management.
   - Create `backend/app/api/routes/alerts.py` for incident triage and acknowledgement.
   - Create `backend/app/api/routes/experiments.py` for research experiment management.
   - Register all routers in `backend/app/main.py`.

2. **Implement Phase 5 Video Processing:**
   - Implement `POST /api/videos/upload` to store benchmark video files.
   - Build background worker to process video frames through `YOLODetector` and `PersonTracker`.

3. **Implement Phase 8 Real-Time WebSockets:**
   - Add `/ws/stream/{camera_id}` for video frame and bounding box transmission.
   - Add `/ws/alerts` for instantaneous real-time alert broadcasts.

4. **Connect Frontend Pages to Live Endpoints:**
   - Integrate `LiveMonitoringPage.tsx` with live streaming canvas.
   - Integrate `AlertsPage.tsx` with incident acknowledgement and resolution actions.
   - Integrate `ResearchPage.tsx` with live experiment comparative graphs.

==============================================================================
# END OF MASTER REFERENCE
# ==============================================================================