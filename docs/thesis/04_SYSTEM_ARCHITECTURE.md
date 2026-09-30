# Chapter 4: System Architecture and Pipeline Design

## 4.1 High-Level Architecture Overview
AquaGuard AI is structured as a decoupled, multi-tiered enterprise architecture consisting of five integrated subsystems:
1. **Video Ingestion and Hardware Abstraction Layer**: Interfaces with IP RTSP streams, USB cameras, and pre-recorded MP4 test videos.
2. **Computer Vision and Tracking Engine**: Executes frame decoding, swimmer localization (YOLOv8), multi-object tracking (DeepSORT/ByteTrack), and Bayesian Kalman state estimation.
3. **Biomechanical Analytics and LSTM Behavior Classifier**: Computes 16-D kinematic descriptors per track, buffers temporal sequences, and performs neural classification.
4. **Backend REST and WebSocket Streaming Server**: FastAPI asynchronous server managing camera registries, alert persistence, live telemetry broadcasts, and experiment benchmarks.
5. **Interactive Single-Page Frontend**: React 18, TypeScript, Tailwind CSS, and Recharts delivering real-time video overlays, heatmaps, alert notifications, and edge performance monitoring.

## 4.2 Pipeline Processing Flow
The end-to-end dataflow proceeds as follows:
1. Incoming frames from poolside cameras are decoded via SIMD-accelerated OpenCV.
2. The Adaptive Frame Skipper evaluates pool threat level: if no swimmers are in distress, it samples every 3rd frame (stride=3), dropping CPU load by 66.7%.
3. YOLOv8 detects swimmer bounding boxes and keypoint poses.
4. DeepSORT tracks swimmers across frames using appearance embeddings and a Bayesian Kalman filter tuned with high acceleration noise covariance to absorb water refraction jumps.
5. For each active track, the 16-D Biomechanical Feature Extractor updates a sliding temporal buffer of 30 frames (1 second).
6. The ONNX Runtime CPU inference engine executes the BiLSTM model, generating state probabilities (Normal, Distress, Drowning).
7. If the drowning probability exceeds the dual threshold (tau_enter=0.75), the state machine transitions to ALERT, snaps the frame skipper to stride=1, and triggers the WebSocket dispatcher.
8. The frontend displays pulsing red bounding boxes, sounds an emergency audio siren, and dispatches SMS/Webhook notifications to lifeguard pagers.

## 4.3 Database Schema and Telemetry Design
The persistent storage layer is built on SQLite (edge/embedded) and PostgreSQL (production) with SQLAlchemy ORM:
- **Users**: Authentication, JWT tokens, RBAC roles (Admin, Head Lifeguard, Safety Auditor).
- **Cameras**: Stream URI, resolution, FPS, pool zone coordinates, and edge processing settings.
- **Alerts**: Swimmer ID, severity level (INFO, WARNING, CRITICAL), trigger confidence, timestamp, latency, and snapshot URL.
- **Incident Logs**: Detailed forensic records tracking the lifecycle of an emergency from initial trigger to lifeguard acknowledgment.
