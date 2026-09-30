"""
AquaGuard AI - Synthetic Scenarios & Physics Simulation Unit Tests (Phase 14)
"""
import os
import pytest
from httpx import AsyncClient
from ai.scenarios.scenario_engine import ScenarioEngine, ScenarioType
from ai.scenarios.synthetic_video_renderer import SyntheticVideoRenderer
from ai.scenarios.scenario_evaluator import ScenarioEvaluator

def test_scenario_engine_all_types():
    """Test scenario generator correctly produces trajectories for all 6 scenarios."""
    engine = ScenarioEngine(frame_width=640, frame_height=360, fps=25.0)
    for stype in ScenarioType:
        trajs = engine.generate_scenario(scenario_type=stype, duration_seconds=3.0, num_swimmers=2)
        assert len(trajs) >= 1
        assert len(trajs[0].states) == 75  # 3s * 25fps
        assert trajs[0].feature_matrix.shape == (75, 16)

def test_synthetic_video_renderer(tmp_path):
    """Test rendering synthetic pool surveillance MP4 video file with metadata."""
    engine = ScenarioEngine(frame_width=320, frame_height=240, fps=20.0)
    trajs = engine.generate_scenario(scenario_type=ScenarioType.FRANTIC_DISTRESS, duration_seconds=1.5)

    vid_path = str(tmp_path / "test_scenario.mp4")
    json_path = str(tmp_path / "test_scenario.json")

    renderer = SyntheticVideoRenderer(width=320, height=240, fps=20.0)
    res = renderer.render_scenario_to_video(trajs, vid_path, json_path)

    assert os.path.exists(vid_path)
    assert os.path.getsize(vid_path) > 1000
    assert os.path.exists(json_path)
    assert res["total_frames"] == 30

def test_scenario_evaluator_idr():
    """Test AI behavioral evaluation on Instinctive Drowning Response (IDR)."""
    engine = ScenarioEngine(fps=30.0)
    trajs = engine.generate_scenario(
        scenario_type=ScenarioType.INSTINCTIVE_DROWNING,
        duration_seconds=5.0,
        distress_onset_second=2.0
    )

    evaluator = ScenarioEvaluator(edge_backend="onnx")
    report = evaluator.evaluate_trajectory(trajs[0], onset_second=2.0)

    assert report["ground_truth_label"] == "drowning"
    assert report["false_alarms_before_onset"] == 0
    if report["time_to_detect_seconds"] is not None:
        assert report["time_to_detect_seconds"] <= 2.5, "Time to detect should be under 2.5s"

@pytest.mark.asyncio
async def test_scenarios_api_list(async_client: AsyncClient):
    """Test GET /api/scenarios returns list of predefined scenarios."""
    response = await async_client.get("/api/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] >= 5
    assert any(s["id"] == "instinctive_drowning" for s in data["scenarios"])

@pytest.mark.asyncio
async def test_scenarios_api_evaluate(async_client: AsyncClient):
    """Test POST /api/scenarios/evaluate runs automated AI assessment."""
    response = await async_client.post(
        "/api/scenarios/evaluate",
        json={
            "scenario_type": "instinctive_drowning",
            "duration_seconds": 5.0,
            "distress_onset_second": 2.0,
            "edge_backend": "onnx"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "evaluation" in data
    assert "summary" in data
    assert "time_to_detect_seconds" in data["summary"]
