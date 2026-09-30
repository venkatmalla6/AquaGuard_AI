"""
AquaGuard AI - Scientific Paper Assets & Visualizations Unit Tests (Phase 15)
"""
import os
import pytest
from httpx import AsyncClient
from ai.evaluation.paper_visualizer import PaperVisualizer, FIGURES_DIR
from ai.evaluation.latex_tables_generator import LatexTablesGenerator, TABLES_DIR

def test_paper_visualizer_generation():
    """Test generating 5 camera-ready publication figures at 300 DPI."""
    vis = PaperVisualizer()
    figs = vis.generate_all_paper_figures()
    assert len(figs) == 5

    for key, name in figs.items():
        png_p = os.path.join(FIGURES_DIR, f"{name}.png")
        pdf_p = os.path.join(FIGURES_DIR, f"{name}.pdf")
        assert os.path.exists(png_p), f"Missing PNG figure {png_p}"
        assert os.path.exists(pdf_p), f"Missing PDF figure {pdf_p}"
        assert os.path.getsize(png_p) > 20 * 1024, f"PNG figure too small: {os.path.getsize(png_p)} bytes"

def test_latex_tables_generation():
    """Test generating academic IEEE/ACM booktabs LaTeX tables."""
    gen = LatexTablesGenerator()
    tabs = gen.generate_all_tables()
    assert len(tabs) == 3

    for key, name in tabs.items():
        tex_p = os.path.join(TABLES_DIR, f"{name}.tex")
        assert os.path.exists(tex_p), f"Missing LaTeX table file {tex_p}"
        with open(tex_p, "r", encoding="utf-8") as f:
            content = f.read()
        assert "\\begin{tabular" in content
        assert "\\end{tabular" in content

@pytest.mark.asyncio
async def test_paper_assets_api_get(async_client: AsyncClient):
    """Test GET /api/experiments/paper-assets returns figures and tables metadata."""
    response = await async_client.get("/api/experiments/paper-assets")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["figures_count"] >= 5
    assert data["tables_count"] >= 3
    assert any("fig1" in f["id"] for f in data["figures"])

@pytest.mark.asyncio
async def test_paper_assets_api_generate(async_client: AsyncClient):
    """Test POST /api/experiments/generate-paper-assets triggers live re-generation."""
    response = await async_client.post("/api/experiments/generate-paper-assets")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "figures" in data
    assert "tables" in data
