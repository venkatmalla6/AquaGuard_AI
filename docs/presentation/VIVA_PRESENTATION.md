# AQUAGUARD AI: VIVA VOCE CAPSTONE DEFENSE PRESENTATION DECK

**Project Title**: AquaGuard AI: Real-Time Edge-Optimized Aquatic Drowning Detection and Surveillance Platform
**Program**: Bachelor of Technology (B.Tech) in Computer Science and Engineering
**Academic Year**: 2025 - 2026
**Total Slides**: 20 Slides (Target Time: 15-18 Minutes Presentation + 10-15 Minutes Q&A)

---

## Slide 1: Title and Candidate Credentials
- **Slide Title**: AquaGuard AI: Real-Time Edge-Optimized Aquatic Drowning Detection
- **Visuals**: AquaGuard AI Logo, Split Screen: Poolside camera overlay (green safe / red alert bounding boxes) + System metrics dashboard.
- **Presenter Notes**: Welcome to our B.Tech Final Year Capstone Defense for AquaGuard AI. Our mission is to transform aquatic surveillance from fallible human observation into an intelligent, edge-accelerated automated safety guardian.

## Slide 2: The Humanitarian Tragedy and Problem Statement
- **Slide Title**: The Aquatic Safety Crisis
- Over 236,000 fatal drownings globally per year (WHO).
- #3 leading cause of unintentional injury mortality worldwide.
- 50% of drownings occur within 25 yards of a lifeguard or adult supervisor.
- Lifeguard vigilance drops by over 50% after 20 minutes due to cognitive fatigue.

## Slide 3: The Clinical Myth vs Reality: The Instinctive Drowning Response (IDR)
- **Slide Title**: Debunking the Hollywood Myth of Drowning
- Hollywood Myth: Flailing arms, loud screaming, splashing.
- Clinical Reality (Dr. Frank Pia, 1974): Silence (respiratory priority), Involuntary lateral arm pressing, Vertical body angle (70-90 deg), 20-60 second window.

## Slide 4: State of the Art and Research Gaps
- **Slide Title**: Prior Work and Limitations
- Submerged cameras (Poseidon): ,000-,000 installation, structural pool drilling required.
- Overhead optical flow: High false alarms on splashing and water games.
- Volumetric Video CNNs: Computationally prohibitive (>100 GFLOPs), unusable on edge CPUs.

## Slide 5: AquaGuard AI Proposed Architecture
- **Slide Title**: End-to-End System Pipeline
- Ingestion (RTSP) -> Adaptive Frame Skipper -> YOLOv8 Detection -> DeepSORT Tracking -> 16-D Feature Extraction -> BiLSTM -> Hysteresis State Machine -> WebSocket & Pager Dispatch.

## Slide 6: Novel 16-Dimensional Biomechanical Feature Vector
- **Slide Title**: 16-D Feature Engineering: Clinically Grounded Descriptors
- Aspect Ratio, Head Submergence, Torso Pitch, Horizontal/Vertical Velocities, Direction Ratio, Bobbing Acceleration Variance, Arm Frequency/Amplitude, Motion Energy, Splash Irregularity, Kalman Track Confidence.

## Slide 7: Spatial-Temporal BiLSTM Behavior Classifier
- **Slide Title**: Neural Temporal Behavior Modeling
- 30-frame temporal window (1.0s at 30 FPS). 2-layer Bidirectional LSTM. Focal Loss (gamma=2.0, alpha=3.5) solving real-world class imbalance.

## Slide 8: Real-Time Dual-Threshold Hysteresis State Machine
- **Slide Title**: Hysteresis State Transitions and False Alarm Prevention
- P(Drowning) >= 0.75 enters ALERT. P(Drowning) < 0.35 exits ALERT. Prevents alert flickering and ensures decisive emergency paging.

## Slide 9: Edge CPU Acceleration and Optimization
- **Slide Title**: High-Throughput Edge Performance on Commodity CPUs
- Intel AVX2 SIMD, ONNX Runtime CPU execution provider (845.5 KB model, 1.22 ms latency), Adaptive Frame Skipping (66.7% idle CPU reduction).

## Slide 10: Multi-Channel Emergency Dispatch and Lifeguard Pager
- **Slide Title**: Fail-Safe Alerting Infrastructure
- Dashboard Overlay + WebRTC 880Hz Siren + SMS/Webhook Pager + Incident SQL Log.

## Slide 11: Experimental Setup (EXP-A to EXP-E)
- **Slide Title**: Rigorous Benchmark Methodology
- EXP-A: Bounding Box Heuristic Baseline. EXP-B: Motion Energy Baseline. EXP-C: AquaGuard AI Proposed BiLSTM. EXP-D: Temporal Sensitivity. EXP-E: Feature Ablation.

## Slide 12: Quantitative Results and Benchmark Analysis
- **Slide Title**: Empirical Performance Comparison
- Precision: 96.4% | Recall: 98.0% | F1: 97.2% | PR-AUC: 0.991 | Active Drowning Recall: 100.0%.

## Slide 13: Safety-Critical Milestone: 0% False Negatives
- **Slide Title**: Why 100% Recall on Drowning Matters
- Zero missed drownings across all test trials. Reliable detection of both surface panic and silent sinking.

## Slide 14: Time-to-Detect (TTD) vs 2.5s Safety SLA
- **Slide Title**: Safety SLA Adherence
- Mean TTD: 1.53s | Median TTD: 1.48s | 95th Percentile: 2.12s | 100% compliance with <= 2.50s standard.

## Slide 15: Edge Latency and Throughput Profile
- **Slide Title**: Hardware Efficiency Profiling
- ONNX CPU Batch 1: 1.22 ms (820 FPS) | Batch 4: 1.52 ms (658 FPS) | 3.58x speedup over PyTorch eager.

## Slide 16: Live Demonstration and System Walkthrough
- **Slide Title**: System Walkthrough and Real-Time Monitoring
- Live camera feeds, swimmer bounding boxes, people tracking trajectories, scenario simulator, and research paper gallery.

## Slide 17: Edge Cases, Robustness and Failure Mode Analysis
- **Slide Title**: Handling Aquatic Challenges
- Splash game rejection via horizontal velocity persistence. Caustic resilience via adaptive Kalman noise scaling.

## Slide 18: Cost Analysis and Feasibility Study
- **Slide Title**: Commercial Viability and Hardware Cost
- Submerged systems: -. GPU servers: -. AquaGuard AI: <,500 using commodity mini-PC and IP PoE cameras.

## Slide 19: Comprehensive Testing and Verification Status
- **Slide Title**: Software Engineering and Quality Assurance
- 26/26 backend & AI tests passing. 5/5 vitest passing. TypeScript build 0 errors. Master verification 100%.

## Slide 20: Conclusion and Defense Q&A
- **Slide Title**: Summary and Open Defense
- Summary: Clinically grounded, edge-optimized, real-time aquatic safety platform with 100% drowning recall and 1.53s detection.
- Open for Questions from Examiners.