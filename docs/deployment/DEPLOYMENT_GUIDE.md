# AQUAGUARD AI: EDGE DEPLOYMENT & HARDWARE SPECIFICATION GUIDE

## 1. Hardware Requirements & Bill of Materials (BOM)

### 1.1 Poolside Edge Compute Node
AquaGuard AI is designed for commodity, low-power x86 or ARM edge computing hardware without requiring discrete server GPUs.

| Component | Minimum Specification | Recommended Production Specification |
|---|---|---|
| Processor (CPU) | Intel Core i3 (8th Gen+) / Celeron J6412 (4 Cores, 2.0 GHz) | Intel Core i5 / i7 (11th-13th Gen, 6-8 Cores, AVX2 support) |
| Alternative Edge SBC | Raspberry Pi 5 (8GB RAM) | Intel N100 / NUC 12 Mini-PC |
| System Memory (RAM) | 8 GB DDR4 | 16 GB DDR4 / DDR5 Dual-Channel |
| Storage | 128 GB NVMe SSD | 512 GB NVMe SSD (High Endurance for video logging) |
| Network Interfaces | 1x Gigabit Ethernet RJ45 | 2x Gigabit Ethernet (Isolated Camera VLAN + LAN) |
| Enclosure | IP54 Dust/Splash Protective Case | IP66 Weatherproof NEMA Enclosure with Heat-Pipe Dissipation |
| Power Consumption | ~15W Idle / 35W Peak | ~25W Idle / 65W Peak |
| Estimated Cost | ~ -  USD | ~ -  USD |

### 1.2 Camera Hardware Specifications
- Type: IP Surveillance Camera with Power over Ethernet (PoE 802.3af).
- Resolution: 1080p Full HD (1920x1080) at 30 FPS.
- Sensor: Sony STARVIS CMOS (High low-light sensitivity, minimum 0.005 Lux).
- Lens: 2.8mm - 4.0mm wide-angle fixed or varifocal motorized lens.
- Dynamic Range: True WDR (Wide Dynamic Range >= 120 dB) essential to suppress water specular glare.
- Enclosure: IP67 waterproof and vandal-proof dome (IK10 rated).
- Protocol: RTSP stream (H.264 / H.265 baseline).

## 2. Camera Mounting & Optical Layout
1. Mounting Height: Minimum 4.0 meters to 6.0 meters above pool deck.
2. Pitch Angle: Downward tilt between 45 degrees and 60 degrees relative to horizon to prevent shallow glare.
3. Field of View: Position cameras opposite large pool windows to avoid direct morning/evening sun glare.
4. Lane Orientation: Mount on lateral perimeter looking perpendicular to swimming lanes.

## 3. Network Topology & Security
- Isolated Camera VLAN preventing public network congestion.
- Hardwired Gigabit PoE Switch delivering reliable low-latency RTSP packets.
- Edge Compute Node executing local inference with zero cloud dependency for lifesaving alerts.

## 4. Software Installation & Deployment
### 4.1 Running via Docker Compose
AquaGuard AI provides containerized deployment for edge nodes:
`yaml
version: '3.8'
services:
  aquaguard-backend:
    image: aquaguard-ai/backend:latest
    restart: unless-stopped
    network_mode: host
    environment:
      - PORT=8000
      - ONNX_NUM_THREADS=6
      - DEFAULT_EDGE_ENGINE=onnx
      - ADAPTIVE_FRAME_SKIP=true
`

### 4.2 Edge Systemd Service Configuration (Linux)
`ini
[Unit]
Description=AquaGuard AI Real-Time Lifeguard Surveillance Service
After=network.target network-online.target

[Service]
Type=simple
User=aquaguard
WorkingDirectory=/opt/aquaguard_ai
ExecStart=/usr/bin/python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
`

## 5. CPU Tuning & Performance Checklist
1. Set CPU governor to performance mode:
   echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
2. Verify Intel AVX2 SIMD extensions are active.
3. Verify ONNX Runtime CPU execution provider is active.
4. Run POST /api/system/edge/benchmark to verify latency < 2.0 ms.
