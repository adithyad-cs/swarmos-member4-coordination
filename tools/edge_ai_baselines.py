"""Score the Edge-AI model against NON-ML baselines on the frozen splits.

Why a separate tool: the first model report (tools/edge_ai_train.py) scored
the analytic lookahead with `la_lead_ticks <= H`. For H = 25 that is always
true, because the lookahead feature only looks FEATURE_LOOKAHEAD_H = 15 ticks
ahead and encodes "no conflict seen" as 16. That baseline row was therefore
meaningless. It never influenced model selection (selection compares ML
candidates on validation PR-AUC / F0.5 only), so the chosen model stands;
this tool re-scores the baselines correctly and records them next to it.

Nothing here chooses the model, its horizon or its threshold. The one tuned
baseline (a distance threshold) is tuned on VALIDATION and applied to TEST.

Baselines, all computed from the same runtime features:
  B1 analytic lookahead: la_lead_ticks <= min(H, 15)
  B2 constant-velocity CPA: dcpa_m < CONFLICT_M and tcpa_s <= H x 0.1 s
  B3 distance rule: dist_m < d*, d* maximising validation F0.5
The model row is recomputed with the RUNTIME (pure-Python) predictor.
"""

from __future__ import annotations

import gzip
import json
import os
import sys
import time
import tracemalloc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.coordination.edge_features import FEATURE_LOOKAHEAD_H, FEATURE_NAMES  # noqa: E402
from app.coordination.swarm_policy import CONFLICT_M  # noqa: E402
from app.ml.edge_predictor import DEFAULT_ARTIFACT, load  # noqa: E402

DATA = os.path.join(ROOT, "reports", "advanced_v1", "dataset")
OUT = os.path.join(ROOT, "reports", "advanced_v1", "model_baselines.json")


def rows(split):
    with gzip.open(os.path.join(DATA, f"{split}.jsonl.gz"), "rt") as fh:
        for line in fh:
            yield json.loads(line)


def score(pairs):
    tp = fp = fn = tn = 0
    for pred, y in pairs:
        if pred and y:
            tp += 1
        elif pred:
            fp += 1
        elif y:
            fn += 1
        else:
            tn += 1
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = lambda b: (1 + b * b) * p * r / (b * b * p + r) if p + r else 0.0  # noqa: E731
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": round(p, 4), "recall": round(r, 4),
            "f1": round(f(1.0), 4), "f0.5": round(f(0.5), 4),
            "fpr": round(fp / (fp + tn), 4) if fp + tn else 0.0}


def main() -> int:
    pred, status = load(DEFAULT_ARTIFACT, expected_features=FEATURE_NAMES)
    assert pred is not None, status
    H = pred.horizon_ticks
    ylab = f"y{H}"
    i = {n: FEATURE_NAMES.index(n) for n in ("la_lead_ticks", "dcpa_m", "tcpa_s", "dist_m")}

    # B3: tune the distance threshold on validation only
    val = [(r["x"][i["dist_m"]], r[ylab]) for r in rows("validation")]
    best = (0.0, None)
    for k in range(100, 601, 5):
        d = k / 100.0
        m = score((x < d, y) for x, y in val)
        if m["f0.5"] > best[0]:
            best = (m["f0.5"], d)
    d_star = best[1]

    b1, b2, b3, mdl, by_sc = [], [], [], [], {}
    t_total, n = 0.0, 0
    for r in rows("test"):
        x, y = r["x"], r[ylab]
        p1 = x[i["la_lead_ticks"]] <= min(H, FEATURE_LOOKAHEAD_H)
        p2 = x[i["dcpa_m"]] < CONFLICT_M and x[i["tcpa_s"]] <= H * 0.1
        p3 = x[i["dist_m"]] < d_star
        t0 = time.perf_counter()
        pm = pred.predict(x)["conflict"]
        t_total += time.perf_counter() - t0
        n += 1
        for lst, p in ((b1, p1), (b2, p2), (b3, p3), (mdl, pm)):
            lst.append((p, y))
        sc = by_sc.setdefault(r["scenario"], {"model": [], "B1": [], "B2": []})
        sc["model"].append((pm, y))
        sc["B1"].append((p1, y))
        sc["B2"].append((p2, y))

    tracemalloc.start()
    p2_, _ = load(DEFAULT_ARTIFACT, expected_features=FEATURE_NAMES)
    mem = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    del p2_

    report = json.load(open(os.path.join(ROOT, "reports", "advanced_v1", "model_report.json")))
    out = {
        "horizon_ticks": H, "model_sha256": pred.sha256, "test_rows": n,
        "note": ("Re-scores the non-ML baselines correctly; the model_report.json "
                 "analytic row for H > 15 was a definition bug (always positive). "
                 "Selection is unaffected: it compared ML candidates only."),
        "test": {
            "model_runtime": score(mdl),
            "B1_analytic_lookahead": score(b1),
            "B2_constant_velocity_cpa": score(b2),
            "B3_distance_rule": {**score(b3), "d_star_m_from_validation": d_star},
        },
        "test_by_scenario": {s: {k: score(v) for k, v in d.items()} for s, d in sorted(by_sc.items())},
        "runtime": {"mean_predict_us_incl_confidence": round(t_total / n * 1e6, 2),
                    "loaded_model_peak_bytes": mem,
                    "max_abs_diff_runtime_vs_sklearn": report["test"].get("max_abs_diff_runtime_vs_sklearn")},
    }
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    print(json.dumps(out["test"], indent=1))
    print(json.dumps(out["runtime"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
