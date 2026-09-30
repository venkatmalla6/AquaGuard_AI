# Chapter 3: Literature Review and Theoretical Foundations

## 3.1 Physiological Foundations of Drowning
### 3.1.1 The Instinctive Drowning Response (Pia, 1974)
Dr. Frank Pia's groundbreaking study established the clinical baseline for non-swimmer drowning behavior:
- **Speech Inability**: The respiratory system is fundamentally designed for breathing. Speech is a secondary function. When water enters the airway or mouth, laryngospasm or involuntary breathing cycles prevent the person from calling for help.
- **Arm Movements**: Drowning individuals cannot wave for help. Nature involuntarily forces them to extend their arms laterally and press down on the water's surface to elevate their mouth.
- **Upright Torso Positioning**: Unlike normal swimming where the swimmer's body is oriented horizontally (pitch angle near 0 degrees), drowning victims are positioned vertically in the water column (pitch angle near 90 degrees), with little or no supporting kick.
- **Critical Time Window**: From the onset of the Instinctive Drowning Response, an individual can only maintain their mouth above water for 20 to 60 seconds before submersion occurs.

### 3.1.2 Stallman's 4-Phase Aquatic Incident Model (2017)
Stallman et al. categorized the physiological progression of aquatic accidents into four sequential stages:
1. *Pre-Distress / Normal Swimming*: Steady forward translation, controlled periodic arm recovery, horizontal torso.
2. *Frantic Distress*: Awareness of fatigue or panic; swimmer attempts purposeful movement, high cadence thrashing, shouting if possible.
3. *Instinctive Drowning Response (IDR)*: Involuntary survival reflexes; vertical bobbing, zero forward propulsion, lateral arm pressing, silence.
4. *Submersion and Immobility*: Involuntary inhalation of water, loss of consciousness, sinking or drifting suspended below the surface.

AquaGuard AI directly maps these physiological states into its state machine to ensure early intervention before the irreversible Phase 4 is reached.

## 3.2 Review of Computer Vision and AI Approaches
### 3.2.1 Classical Optical Flow and Motion Energy
Early research (e.g., Poseidon system, Kamiel et al.) relied on underwater camera arrays and overhead background subtraction. While effective in clear, undisturbed Olympic diving pools, these systems suffer in outdoor or crowded community pools due to wave caustics and surface reflection. Furthermore, motion energy alone fails to distinguish between playful splashing and true distress.

### 3.2.2 3D Volumetric CNNs (I3D, SlowFast, VideoMAE)
Recent computer vision research has applied 3D convolutional networks (e.g., Carreira & Zisserman I3D, Feichtenhofer SlowFast) to action recognition. While these models capture spatial and temporal features jointly, they suffer from:
- Prohibitive computational complexity (often >100 GFLOPs per forward pass).
- Inability to run on commodity edge CPUs in real time.
- Heavy reliance on appearance textures that are disrupted by water refraction.

### 3.2.3 Pose-Driven Biomechanical Sequence Modeling
AquaGuard AI adopts a hybrid approach: decoupling object spatial detection (YOLOv8) from biomechanical kinematics (16-D feature extractor) and temporal modeling (BiLSTM). This approach yields two major advantages:
1. **Explainability**: Each feature in the 16-D vector has a clear physical and physiological meaning (aspect ratio, velocity ratio, submergence depth).
2. **Extreme Edge Efficiency**: The BiLSTM operates on compact 16-D feature vectors rather than dense pixel tensors, requiring less than 0.05 GFLOPs and achieving 1.22 ms inference latency on an edge CPU thread.
