"""
AquaGuard AI - Synthetic Scenarios & Physics Simulation Endpoints (Phase 14)
Enables research scientists and operators to generate physiological edge-case
scenarios, render synthetic surveillance videos, and measure detection latency.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field

# Setup path for AI module imports
root_dir = str(Path(__file__).parent.parent.parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.api.deps.auth import get_current_user
from app.models.models import User
from ai.scenarios.scenario_engine import ScenarioEngine, ScenarioType
from ai.scenarios.synthetic_video_renderer import SyntheticVideoRenderer
from ai.scenarios.scenario_evaluator import ScenarioEvaluator

router = APIRouter()

PREDEFINED_SCENARIOS = [
    {
        "id": "instinctive_drowning",
        "title": "Instinctive Drowning Response (IDR)",
        "description": "Simulates classic Pia (1974) physiological response: upright vertical body, lateral arm pressing, inability to kick, absence of forward locomotion.",
        "risk_level": "critical",
        "primary_label": "drowning",
        "typical_onset_sec": 3.0,
        "default_duration_sec": 10.0,
    },
    {
        "id": "frantic_distress",
        "title": "Frantic Active Distress",
        "description": "Simulates conscious struggling swimmer waving, thrashing, elevated acceleration variance, and shouting before exhaustion.",
        "risk_level": "warning",
        "primary_label": "distress",
        "typical_onset_sec": 2.5,
        "default_duration_sec": 10.0,
    },
    {
        "id": "submersion_immobility",
        "title": "Silent Submersion Immobility (Blackout)",
        "description": "Simulates shallow water blackout or sudden loss of consciousness: sinking downwards, shrinking bounding box, near 100% inactivity.",
        "risk_level": "critical",
        "primary_label": "drowning",
        "typical_onset_sec": 2.0,
        "default_duration_sec": 8.0,
    },
    {
        "id": "normal_lap_swimming",
        "title": "Normal Horizontal Lap Swimming",
        "description": "Continuous rhythmic breaststroke/freestyle: horizontal aspect ratio, steady speed, low vertical ratio. Ground truth negative baseline.",
        "risk_level": "none",
        "primary_label": "normal",
        "typical_onset_sec": 0.0,
        "default_duration_sec": 12.0,
    },
    {
        "id": "playful_splashing",
        "title": "Playful Water Games (False Alarm Control)",
        "description": "Children jumping and splashing vigorously: high movement variance but maintaining horizontal posture and self-propulsion.",
        "risk_level": "low",
        "primary_label": "normal",
        "typical_onset_sec": 0.0,
        "default_duration_sec": 10.0,
    },
    {
        "id": "multi_swimmer_crowd",
        "title": "Multi-Swimmer Crowd with 1 Drowning Incident",
        "description": "High-density pool crowd with 4 swimmers swimming normally and 1 peripheral swimmer entering instinctive drowning response.",
        "risk_level": "critical",
        "primary_label": "drowning",
        "typical_onset_sec": 3.5,
        "default_duration_sec": 12.0,
    },
]

class ScenarioGenerateRequest(BaseModel):
    scenario_type: str = Field("instinctive_drowning")
    duration_seconds: float = Field(8.0, ge=3.0, le=30.0)
    num_swimmers: int = Field(1, ge=1, le=8)
    distress_onset_second: float = Field(2.5, ge=1.0, le=25.0)
    render_video: bool = Field(False)

class ScenarioEvaluateRequest(BaseModel):
    scenario_type: str = Field("instinctive_drowning")
    duration_seconds: float = Field(8.0, ge=3.0, le=20.0)
    distress_onset_second: float = Field(2.5, ge=1.0, le=15.0)
    edge_backend: str = Field("onnx")

@router.get("", summary="List Predefined Aquatic Scenarios")
async def list_scenarios(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Retrieve catalog of available physiological aquatic scenarios and biomechanical parameters."""
    return {
        "status": "success",
        "count": len(PREDEFINED_SCENARIOS),
        "scenarios": PREDEFINED_SCENARIOS,
    }

@router.post("/generate", summary="Generate Synthetic Aquatic Scenario Trajectories or Video")
async def generate_scenario(
    req: ScenarioGenerateRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Generates parameterized trajectories and optionally renders an MP4 synthetic video."""
    try:
        stype = ScenarioType(req.scenario_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario_type '{req.scenario_type}'. Choose from: {[s['id'] for s in PREDEFINED_SCENARIOS]}"
        )

    engine = ScenarioEngine(frame_width=1280, frame_height=720, fps=30.0)
    trajectories = engine.generate_scenario(
        scenario_type=stype,
        duration_seconds=req.duration_seconds,
        num_swimmers=req.num_swimmers,
        distress_onset_second=req.distress_onset_second
    )

    rendered_video_info = None
    if req.render_video:
        renderer = SyntheticVideoRenderer(width=1280, height=720, fps=30.0)
        vid_filename = f"scenario_{stype.value}_{int(req.duration_seconds)}s.mp4"
        out_vid = os.path.join(root_dir, "data", "synthetic_videos", vid_filename)
        out_json = out_vid.replace(".mp4", ".json")
        rendered_video_info = renderer.render_scenario_to_video(
            trajectories=trajectories,
            output_video_path=out_vid,
            output_json_path=out_json
        )

    trajectories_summary = [
        {
            "track_id": t.track_id,
            "scenario": t.scenario_type.value,
            "primary_label": t.primary_label,
            "frames_count": len(t.states),
            "start_position": [t.states[0].x, t.states[0].y],
            "end_position": [t.states[-1].x, t.states[-1].y],
        }
        for t in trajectories
    ]

    return {
        "status": "success",
        "scenario_type": stype.value,
        "duration_seconds": req.duration_seconds,
        "num_swimmers": len(trajectories),
        "trajectories": trajectories_summary,
        "rendered_video": rendered_video_info,
    }

@router.post("/evaluate", summary="Evaluate Detection Accuracy and Latency on Scenario")
async def evaluate_scenario(
    req: ScenarioEvaluateRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Executes live AI behavioral classifier and alert engine on the simulated scenario
    to report time-to-detect latency (TTD) and frame classification accuracy.
    """
    try:
        stype = ScenarioType(req.scenario_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid scenario_type: {req.scenario_type}")

    engine = ScenarioEngine(frame_width=1280, frame_height=720, fps=30.0)
    trajs = engine.generate_scenario(
        scenario_type=stype,
        duration_seconds=req.duration_seconds,
        num_swimmers=1,
        distress_onset_second=req.distress_onset_second
    )

    evaluator = ScenarioEvaluator(edge_backend=req.edge_backend)
    eval_result = evaluator.evaluate_trajectory(trajs[0], onset_second=req.distress_onset_second)

    return {
        "status": "success",
        "scenario": stype.value,
        "evaluation": eval_result,
        "summary": {
            "time_to_detect_seconds": eval_result["time_to_detect_seconds"],
            "accuracy_percent": round(eval_result["frame_accuracy"] * 100.0, 1),
            "false_alarms": eval_result["false_alarms_before_onset"],
            "sla_met": bool(eval_result["time_to_detect_seconds"] is not None and eval_result["time_to_detect_seconds"] <= 2.5),
        }
    }
