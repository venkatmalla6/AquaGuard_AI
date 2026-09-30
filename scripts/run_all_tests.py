"""
AquaGuard AI - Master Comprehensive Testing Suite Runner (Phase 13)
Executes full backend pytest, computer vision pipeline validation,
frontend vitest unit tests, and production TypeScript builds.
"""
from __future__ import annotations
import os
import sys
import time
import subprocess
from pathlib import Path

root_dir = str(Path(__file__).parent.parent)

def run_command(cmd, cwd=root_dir, name=""):
    print(f"\n>> Running {name}...")
    t0 = time.perf_counter()
    p = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    dur = time.perf_counter() - t0
    if p.returncode == 0:
        print(f" [OK] {name} passed in {dur:.2f}s")
        return True, dur, p.stdout
    else:
        print(f" [FAIL] {name} failed in {dur:.2f}s")
        print(p.stdout)
        print(p.stderr)
        return False, dur, p.stderr

def main():
    print("=" * 75)
    print(" AQUAGUARD AI - PHASE 13: MASTER COMPREHENSIVE TEST SUITE")
    print("=" * 75)
    
    total_start = time.perf_counter()
    results = {}

    # 1. Backend & AI Pytest Suite
    ok1, dur1, out1 = run_command("python -m pytest tests -q", name="Backend & AI Pytest Suite (21 Tests)")
    results["Pytest Backend & AI"] = {"status": "PASSED" if ok1 else "FAILED", "duration": f"{dur1:.2f}s"}

    # 2. Edge Optimization Suite
    ok2, dur2, out2 = run_command("python scripts/test_phase12.py", name="Edge Optimization & Benchmark Suite")
    results["Edge Optimization"] = {"status": "PASSED" if ok2 else "FAILED", "duration": f"{dur2:.2f}s"}

    # 3. Frontend Vitest Unit Tests
    frontend_dir = os.path.join(root_dir, "frontend")
    ok3, dur3, out3 = run_command("npm test", cwd=frontend_dir, name="Frontend Vitest Suite (5 Tests)")
    results["Frontend Vitest"] = {"status": "PASSED" if ok3 else "FAILED", "duration": f"{dur3:.2f}s"}

    # 4. Frontend Production Build & TypeScript Typecheck
    ok4, dur4, out4 = run_command("npm run build", cwd=frontend_dir, name="Frontend TypeScript & Vite Build")
    results["Frontend Vite Build"] = {"status": "PASSED" if ok4 else "FAILED", "duration": f"{dur4:.2f}s"}

    total_dur = time.perf_counter() - total_start
    all_passed = all(r["status"] == "PASSED" for r in results.values())

    print("\n" + "=" * 75)
    print(" SUMMARY MATRIX:")
    print("=" * 75)
    for suite, data in results.items():
        print(f"  * {suite.ljust(35)}: [{data['status']}] (Duration: {data['duration']})")
    print("-" * 75)
    print(f" Total Verification Duration: {total_dur:.2f}s")
    if all_passed:
        print(" [SUCCESS] ALL 4 TEST SUITES PASSED! Phase 13 Complete.")
        print("=" * 75)
        sys.exit(0)
    else:
        print(" [ERROR] One or more test suites failed.")
        print("=" * 75)
        sys.exit(1)

if __name__ == "__main__":
    main()
