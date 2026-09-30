# Chapter 5: Methodology and Mathematical Formulation

## 5.1 Swimmer Detection and Tracking Formulation
Let $I_t \in \mathbb{R}^{H \times W \times 3}$ denote the video frame captured at time step $t$. Swimmer localization is formulated as predicting a set of bounding boxes $B_t = \{b_i = (x_i, y_i, w_i, h_i, c_i, k_i)\}$, where $(x_i, y_i)$ are center coordinates, $(w_i, h_i)$ represent width and height, $c_i$ is detection confidence, and $k_i \in \mathbb{R}^{17 \times 3}$ represents anatomical pose keypoints (head, shoulders, elbows, wrists, hips, knees, ankles).

### 5.1.1 Aquatic-Adapted Bayesian Kalman Filter
Swimmer tracking across frames under surface wave turbulence is modeled using a linear discrete-time state-space system:
$$\mathbf{x}_t = \mathbf{F} \mathbf{x}_{t-1} + \mathbf{w}_t, \quad \mathbf{w}_t \sim \mathcal{N}(\mathbf{0}, \mathbf{Q})$$
$$\mathbf{z}_t = \mathbf{H} \mathbf{x}_t + \mathbf{v}_t, \quad \mathbf{v}_t \sim \mathcal{N}(\mathbf{0}, \mathbf{R})$$
where the state vector $\mathbf{x} = [x, y, a, h, \dot{x}, \dot{y}, \dot{a}, \dot{h}]^T$ encompasses 2D spatial position, aspect ratio $a = w/h$, height $h$, and their respective first-order temporal derivatives. To accommodate severe light refraction shifts, the process noise covariance matrix $\mathbf{Q}$ is scaled adaptively based on localized water surface variance:
$$\mathbf{Q}_t = \mathbf{Q}_0 \cdot (1 + \alpha \cdot \sigma^2_{caustic})$$

## 5.2 16-Dimensional Biomechanical Feature Vector
For each active swimmer track $k$ over a temporal window $T = 30$ frames (1.0 second at 30 FPS), AquaGuard AI computes a 16-dimensional feature vector $\mathbf{f}_t \in \mathbb{R}^{16}$:

1. **Vertical Aspect Ratio ($AR_v$)**:
   $$AR_v = \frac{h_t}{w_t}$$
   *Physiological Basis*: Swimmers in normal horizontal swimming have $AR_v < 1.0$ (horizontal orientation). Victims in the Instinctive Drowning Response have $AR_v > 1.8$ (upright vertical orientation in the water column).

2. **Head-to-Shoulder Submergence Ratio ($R_{hs}$)**:
   $$R_{hs} = \frac{y_{head} - y_{waterline}}{\max(1.0, |y_{shoulders} - y_{head}|)}$$
   *Physiological Basis*: Quantifies mouth submersion below water surface ($R_{hs} < 0$ denotes submersion).

3. **Torso Inclination Angle ($\theta_{torso}$)**:
   $$\theta_{torso} = \arctan\left(\frac{|y_{shoulders} - y_{hips}|}{|x_{shoulders} - x_{hips}| + \epsilon}\right) \cdot \frac{180}{\pi}$$
   *Physiological Basis*: Normal swimming exhibits horizontal torso ($\theta < 35^\circ$); IDR causes upright vertical posture ($\theta > 70^\circ$).

4. **Horizontal Translation Velocity ($v_x$)**:
   $$v_x = \frac{x_t - x_{t-\Delta t}}{\Delta t}$$
   *Physiological Basis*: Purposeful locomotion produces sustained non-zero $v_x$; drowning yields $v_x \approx 0$.

5. **Vertical Translation Velocity ($v_y$)**:
   $$v_y = \frac{y_t - y_{t-\Delta t}}{\Delta t}$$
   *Physiological Basis*: Vertical bobbing and sinking dynamics.

6. **Velocity Direction Ratio ($R_{vh}$)**:
   $$R_{vh} = \frac{|v_y|}{|v_x| + \epsilon}$$
   *Physiological Basis*: Swimming has low $R_{vh}$; drowning shows massive vertical-to-horizontal bias ($R_{vh} \gg 1.0$).

7. **Vertical Bobbing Acceleration ($a_y$)**:
   $$a_y = \frac{v_{y, t} - v_{y, t-\Delta t}}{\Delta t}$$

8. **Vertical Acceleration Variance ($\sigma^2_{ay}$)**:
   $$\sigma^2_{ay} = \frac{1}{N}\sum_{i=1}^N (a_{y, i} - \bar{a}_y)^2$$
   *Physiological Basis*: Uncontrolled panic cycles produce high vertical acceleration variance.

9. **Cyclic Arm Recovery Frequency ($f_{arm}$)**:
   $$f_{arm} = \arg\max_f \left| \mathcal{F}\{y_{wrist}(t) - y_{shoulder}(t)\} \right|$$
   *Physiological Basis*: Regular rhythmic cadence (0.5 - 1.2 Hz) in freestyle/breaststroke vs high irregular thrashing in frantic distress (>2.5 Hz).

10. **Arm Stroke Amplitude ($A_{arm}$)**:
    $$A_{arm} = \max_{t \in T}(y_{wrist}) - \min_{t \in T}(y_{wrist})$$
    *Physiological Basis*: Lateral arm pressing in IDR lacks vertical overhead recovery ($A_{arm} \to 0$).

11. **Localized Motion Energy ($E_m$)**:
    $$E_m = \frac{1}{|B_t|}\sum_{(x,y) \in B_t} |I_t(x,y) - I_{t-1}(x,y)|$$
    *Physiological Basis*: Distinguishes energetic surface distress from inert submerged motionless victims.

12. **Bounding Box Area Variance ($\sigma^2_{area}$)**:
    $$\sigma^2_{area} = \frac{1}{N}\sum_{i=1}^N \left(A_i - \bar{A}\right)^2$$
    *Physiological Basis*: Tracks expansion/collapse of water profile due to thrashing vs sinking.

13. **Submersion Immobility Duration ($T_{immob}$)**:
    $$T_{immob} = \sum_{t \in T} \mathbb{I}(\|\mathbf{v}_t\| < \epsilon_{still} \;\land\; R_{hs} < 0) \cdot \Delta t$$
    *Physiological Basis*: Critical indicator of shallow water blackout or unconscious sinking.

14. **Head Distance to Surface ($d_{surf}$)**:
    $$d_{surf} = y_{head} - y_{pool\_surface}$$

15. **Perimeter Splash Irregularity ($P_{splash}$)**:
    $$P_{splash} = \frac{\text{Perimeter}(M_t)}{2\sqrt{\pi \cdot \text{Area}(M_t)}}$$
    *Physiological Basis*: Isoperimetric quotient of swimmer water mask $M_t$ quantifying turbulent foam disturbance.

16. **Bayesian Kalman Track Confidence ($C_{track}$)**:
    $$C_{track} = \exp\left(-\frac{1}{2} (\mathbf{z}_t - \mathbf{H}\hat{\mathbf{x}}_t)^T \mathbf{S}_t^{-1} (\mathbf{z}_t - \mathbf{H}\hat{\mathbf{x}}_t)\right)$$

## 5.3 Spatial-Temporal Behavior BiLSTM
The sequence of 16-D feature vectors $\mathbf{X} = [\mathbf{f}_1, \mathbf{f}_2, \dots, \mathbf{f}_T] \in \mathbb{R}^{T \times 16}$ is processed by a 2-layer Bidirectional LSTM:
$$\vec{\mathbf{h}}_t = \text{LSTM}_{fwd}(\mathbf{f}_t, \vec{\mathbf{h}}_{t-1})$$
$$\overleftarrow{\mathbf{h}}_t = \text{LSTM}_{bwd}(\mathbf{f}_t, \overleftarrow{\mathbf{h}}_{t+1})$$
$$\mathbf{h}_t = [\vec{\mathbf{h}}_t \,;\, \overleftarrow{\mathbf{h}}_t]$$
The final temporal representation $\mathbf{h}_T$ passes through a fully connected projection layer with Softmax activation:
$$\mathbf{p} = \text{Softmax}(\mathbf{W}_c \mathbf{h}_T + \mathbf{b}_c) \in \mathbb{R}^3$$
representing probabilities for $[P_{normal}, P_{distress}, P_{drowning}]$.

### 5.3.1 Training Loss with Class Imbalance Weighting
To prioritize safety-critical zero-false-negative performance, training optimizes Focal Loss:
$$\mathcal{L}_{focal} = -\sum_{c=1}^3 \alpha_c (1 - p_c)^\gamma \log(p_c)$$
with focusing parameter $\gamma = 2.0$ and drowning class weight $\alpha_{drowning} = 3.5$.

## 5.4 Dual-Threshold Hysteresis State Machine
To eliminate high-frequency alert fluttering, state transitions are governed by asymmetric hysteresis thresholds:
$$\text{State}_{t} = \begin{cases} \text{ALERT}, & \text{if } P_{drowning} \ge \tau_{enter} \; (0.75) \\ \text{WARNING}, & \text{if } P_{distress} \ge \tau_{warn} \; (0.60) \;\land\; \text{State}_{t-1} = \text{NORMAL} \\ \text{NORMAL}, & \text{if } P_{drowning} < \tau_{exit} \; (0.35) \;\land\; \text{State}_{t-1} = \text{ALERT} \\ \text{State}_{t-1}, & \text{otherwise} \end{cases}$$
