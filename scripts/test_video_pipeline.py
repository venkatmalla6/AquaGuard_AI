"""
AquaGuard AI - Video Ingestion & Processing Automated Test
Generates synthetic swimmer video, uploads via REST API, triggers inference,
and verifies progress tracking and completed output.
"""
import time
from pathlib import Path
import cv2
import numpy as np
import httpx

BASE_URL = "http://localhost:8000"

def create_synthetic_pool_video(output_path: str, duration_sec: int = 2, fps: int = 30):
    """Generate a test MP4 video with swimming and distress trajectories."""
    width, height = 640, 360
    total_frames = duration_sec * fps
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for f in range(total_frames):
        # Create cyan-blue water gradient background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :] = (180, 110, 20)  # BGR aquatic pool blue

        # Swimmer 1 (Normal swimmer moving across lanes horizontally)
        s1_x = int(80 + (f * 6))
        s1_y = 120
        # Horizontal swimming profile (w > h)
        cv2.rectangle(frame, (s1_x, s1_y), (s1_x + 50, s1_y + 25), (230, 210, 190), -1)
        cv2.circle(frame, (s1_x + 55, s1_y + 12), 8, (200, 180, 160), -1)

        # Swimmer 2 (Distress / vertical motionless swimmer in deep end)
        s2_x = 450
        s2_y = int(200 + np.sin(f * 0.2) * 5)
        # Vertical upright profile (h > w)
        cv2.rectangle(frame, (s2_x, s2_y), (s2_x + 20, s2_y + 60), (220, 190, 170), -1)
        cv2.circle(frame, (s2_x + 10, s2_y - 8), 7, (200, 180, 160), -1)

        # Add pool lane markers
        for lane_y in [90, 180, 270]:
            cv2.line(frame, (0, lane_y), (width, lane_y), (255, 255, 255), 1)

        out.write(frame)

    out.release()
    print(f"Synthetic video generated: {output_path} ({total_frames} frames)")

def run_test():
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)

    # 1. Health
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[1] Backend Health: OK")

    # 2. Login
    login_res = client.post("/api/auth/login", json={"email": "operator@aquaguard.ai", "password": "operator123"})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[2] Operator Authentication: OK")

    # 3. Generate Video
    temp_dir = Path("D:/Btech/PROJECTS/AquaGuard_AI/data/test_samples")
    temp_dir.mkdir(parents=True, exist_ok=True)
    video_file = temp_dir / "synthetic_pool_sim.mp4"
    create_synthetic_pool_video(str(video_file), duration_sec=2, fps=30)

    # 4. Upload with auto_process=True
    with open(video_file, "rb") as f:
        files = {"file": ("synthetic_pool_sim.mp4", f, "video/mp4")}
        upload_res = client.post("/api/videos/upload?auto_process=true", files=files, headers=headers)

    assert upload_res.status_code == 201, f"Upload failed: {upload_res.text}"
    video_data = upload_res.json()
    video_id = video_data["id"]
    print(f"[3] Uploaded Video ID: {video_id} | Total Frames: {video_data['total_frames']} | Duration: {video_data['duration_seconds']}s")

    # 5. Poll processing progress
    print("[4] Polling video processing progress...")
    for _ in range(30):
        time.sleep(1.0)
        v_res = client.get(f"/api/videos/{video_id}", headers=headers)
        v_info = v_res.json()
        print(f"    Status: {v_info['status']} | Progress: {v_info['progress_percent']}% | Frames: {v_info['processed_frames']}/{v_info['total_frames']}")
        if v_info["status"] in ["completed", "failed"]:
            break

    assert v_info["status"] == "completed", f"Video processing did not complete successfully: {v_info}"
    print("[5] Video Processing: COMPLETED SUCCESSFULLY!")

    # 6. List videos
    list_res = client.get("/api/videos", headers=headers)
    assert list_res.status_code == 200
    print(f"[6] Video List: {len(list_res.json())} videos found in database.")

    # 7. Test Stream
    stream_res = client.get(f"/api/videos/{video_id}/stream", headers=headers)
    assert stream_res.status_code == 200, f"Stream failed: {stream_res.status_code}"
    print(f"[7] Stream Endpoint: OK ({len(stream_res.content)} bytes received)")

if __name__ == "__main__":
    run_test()