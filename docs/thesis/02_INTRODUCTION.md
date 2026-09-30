# Chapter 2: Introduction and Problem Formulation

## 2.1 Background and Motivation
Drowning is a major global public health concern. Unintentional drowning claims hundreds of thousands of lives every year. In public pools, water parks, schools, hotels, and athletic facilities, lifeguards are the primary defense against catastrophic immersion events. However, human vigilance is inherently fallible. Studies in occupational cognitive psychology show that human visual monitoring accuracy drops by over 50% after just 20 minutes of continuous scanning, especially under high glare, high swimmer density, and hot ambient temperatures.

Furthermore, popular media has popularized the dangerous myth that drowning individuals splash violently, wave their arms over their head, and shout for help. In reality, Dr. Frank Pia's research demonstrates that a drowning human is physically incapable of shouting because their respiratory system is prioritizing gas exchange over speech. Their arms reflexively press down against the water surface in an involuntary attempt to leverage the mouth above water level. Consequently, drowning happens in plain sight, often without anyone nearby noticing.

## 2.2 Operational Challenges in Aquatic Environments
Automating drowning detection through computer vision introduces severe domain-specific challenges that cause generic object detection and action recognition algorithms to fail:
1. **Water Surface Optical Perturbations**: Constant surface ripples, caustic lens focusing, and turbulent wave crests create intense specular highlights and rapid illumination shifts that rupture background subtraction models.
2. **Refractive Pose Distortion**: As a swimmer submerges, water refraction bends light rays, distorting apparent limb lengths, joint angles, and spatial coordinates.
3. **Severe False Alarm Triggers**: Playful splashing, diving, breath-holding games, and water polo involve high splashing and rapid movements that naive motion energy detectors falsely classify as life-threatening emergencies.
4. **Computational and Hardware Constraints**: Most swimming pools are operated with limited IT infrastructure. Requiring expensive multi-thousand-dollar server-grade GPUs with dedicated liquid cooling is economically non-viable for widespread adoption. A successful system must execute on low-power commodity edge x86/ARM CPUs.

## 2.3 Research Objectives and Scope
The primary objectives of this project are:
1. To develop a computer vision pipeline that detects and tracks multiple swimmers in real-time under refractive and caustic conditions.
2. To formulate a mathematically grounded 16-dimensional biomechanical feature vector based on human swimming kinematics and the Instinctive Drowning Response (IDR).
3. To design and train a temporal sequence classifier (Bidirectional LSTM) capable of discriminating among normal swimming, playful splashing, active distress, and submersion drowning.
4. To optimize the full pipeline for real-time edge execution on commodity CPUs without specialized GPU acceleration.
5. To build an intuitive, full-stack operator dashboard and multi-channel emergency alert system guaranteeing a Time-to-Detect (TTD) under 2.50 seconds.
