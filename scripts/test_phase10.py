"""
AquaGuard AI - Phase 10 Verification Script
Validates:
1. BenchmarkSuite engine execution across EXP-A to EXP-E
2. GET /api/experiments/comparison endpoint
3. SQLite database persistence of verified metrics
4. Research export files (benchmark_summary.json, benchmark_comparison_table.csv, benchmark_latex_table.tex)
"""
import sys
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

def main():
    print("[1] Verifying Benchmark Suite Output Files...")
    res_dir = ROOT / "experiments" / "results"
    summary_json = res_dir / "benchmark_summary.json"
    table_csv    = res_dir / "benchmark_comparison_table.csv"
    latex_tex    = res_dir / "benchmark_latex_table.tex"

    assert summary_json.exists(), "Missing benchmark_summary.json"
    assert table_csv.exists(), "Missing benchmark_comparison_table.csv"
    assert latex_tex.exists(), "Missing benchmark_latex_table.tex"
    print("    [OK] Found benchmark_summary.json")
    print("    [OK] Found benchmark_comparison_table.csv")
    print("    [OK] Found benchmark_latex_table.tex")

    with open(summary_json, "r") as f:
        data = json.load(f)
    assert len(data) == 5, f"Expected 5 experiments, found {len(data)}"
    for key in ["exp_a", "exp_b", "exp_c", "exp_d", "exp_e"]:
        assert key in data, f"Missing {key} in summary"
        print(f"    [OK] Verified {key.upper()}: F1={data[key]['f1_score']}, Drowning Recall={data[key]['recall_drowning']}")

    print("\n[2] Verifying SQLite Database Records...")
    conn = sqlite3.connect(str(ROOT / "aquaguard.db"))
    c = conn.cursor()
    c.execute("""
        SELECT e.id, e.name, e.status, m.precision, m.recall, m.f1_score, m.recall_drowning, m.avg_fps
        FROM experiments e
        JOIN experiment_metrics m ON e.id = m.experiment_id
        ORDER BY e.id
    """)
    rows = c.fetchall()
    assert len(rows) == 5, f"Expected 5 database records, found {len(rows)}"
    for r in rows:
        print(f"    [OK] DB Exp #{r[0]}: {r[1]} -> Status: {r[2]}, F1: {r[5]}, Drowning Recall: {r[6]}, FPS: {r[7]}")
    conn.close()

    print("\n[3] Verifying FastAPI Endpoint via Starlette TestClient...")
    from app.main import app
    from starlette.testclient import TestClient

    client = TestClient(app)
    # Login as admin to get token
    login_res = client.post("/api/auth/login", json={"email": "operator@aquaguard.ai", "password": "operator123"})
    assert login_res.status_code == 200, f"Login failed: {login_res.status_code}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Test GET /api/experiments/comparison
    comp_res = client.get("/api/experiments/comparison", headers=headers)
    assert comp_res.status_code == 200, f"Comparison endpoint failed: {comp_res.status_code}"
    comp_data = comp_res.json()
    assert len(comp_data) == 5, f"Expected 5 comparison entries, got {len(comp_data)}"
    print(f"    [OK] GET /api/experiments/comparison returned {len(comp_data)} items")
    for item in comp_data:
        print(f"         - {item['name']}: F1={item['f1_score']}, Imp: +{item['improvement_f1_pct']}%")

    print("\n[4] All Phase 10 Research Benchmark Suite checks PASSED successfully!")

if __name__ == "__main__":
    main()

