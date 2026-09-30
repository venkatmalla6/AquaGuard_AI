import sys
from pathlib import Path
root = Path(__file__).parent.parent
def check(rel, sz, desc):
    p = root / rel
    if not p.exists() or p.stat().st_size < sz:
        print(f'FAIL: {rel} ({desc})')
        return False
    print(f'PASS: {rel} ({p.stat().st_size:,} bytes) - {desc}')
    return True
items = [
    ('docs/thesis/01_ABSTRACT.md', 1000, 'Abstract'),
    ('docs/thesis/02_INTRODUCTION.md', 1000, 'Introduction'),
    ('docs/thesis/03_LITERATURE_REVIEW.md', 1000, 'Literature Review'),
    ('docs/thesis/04_SYSTEM_ARCHITECTURE.md', 1000, 'System Architecture'),
    ('docs/thesis/05_METHODOLOGY_MATHEMATICAL_FORMULATION.md', 2000, 'Methodology'),
    ('docs/thesis/06_EDGE_OPTIMIZATION.md', 1500, 'Edge Optimization'),
    ('docs/thesis/07_EMPIRICAL_EVALUATION.md', 2000, 'Evaluation'),
    ('docs/thesis/08_CONCLUSION_FUTURE_WORK.md', 1000, 'Conclusion'),
    ('docs/thesis/THESIS_COMPLETE.md', 20000, 'Master Thesis'),
    ('docs/presentation/VIVA_PRESENTATION.md', 2500, 'Presentation Deck'),
    ('docs/presentation/EXAMINER_QA_DEFENSE_GUIDE.md', 5000, 'Examiner QA'),
    ('docs/deployment/DEPLOYMENT_GUIDE.md', 1000, 'Deployment Guide'),
    ('docs/api/API_REFERENCE.md', 1000, 'API Reference'),
    ('ai/models/registry/behavior_lstm.onnx', 500000, 'ONNX Model'),
    ('ai/models/registry/behavior_lstm.torchscript.pt', 500000, 'TorchScript Model')
]
for fn in ['fig1_precision_recall_curves', 'fig2_confusion_matrices_comparison', 'fig3_latency_vs_edge_throughput', 'fig4_feature_importance_ranking', 'fig5_time_to_detect_sla_adherence']:
    items.append((f'docs/paper/figures/{fn}.png', 10000, f'Figure PNG {fn}'))
    items.append((f'docs/paper/figures/{fn}.pdf', 5000, f'Figure PDF {fn}'))
for tn in ['table1_model_comparison.tex', 'table2_edge_acceleration.tex', 'table3_biomechanical_features.tex']:
    items.append((f'docs/paper/tables/{tn}', 300, f'Table {tn}'))
ok = sum(1 for r, s, d in items if check(r, s, d))
print(f'Total: {ok}/{len(items)} passed')
sys.exit(0 if ok == len(items) else 1)