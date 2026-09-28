"""Reproducibility and runtime-parity check for the shipped Edge-AI model.

1. Refit the CHOSEN configuration (kind, horizon, hyper-parameters, seed) on
   the train split exactly as tools/edge_ai_train.py does, export it, and
   check that its content hash equals the shipped artifact's. That proves the
   artifact is the output of the recorded procedure, not a hand-edited file.
2. Compare scikit-learn predict_proba with the pure-Python runtime predictor
   on every test row: max absolute probability difference and the number of
   thresholded decisions that differ.
Writes reports/advanced_v1/model_parity.json. Chooses nothing.
"""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import numpy as np  # noqa: E402

import edge_ai_train as T  # noqa: E402
from app.coordination.edge_features import FEATURE_NAMES  # noqa: E402
from app.ml.edge_predictor import DEFAULT_ARTIFACT, canonical_sha256, load  # noqa: E402

OUT = os.path.join(ROOT, "reports", "advanced_v1", "model_parity.json")


def main() -> int:
    pred, status = load(DEFAULT_ARTIFACT, expected_features=FEATURE_NAMES)
    assert pred is not None, status
    kind, h = pred.kind, pred.horizon_ticks
    Xtr, ytr, _ = T.read("train")
    model, aux = T.fit(kind, T.candidates()[kind], Xtr, ytr[h])
    refit_sha = canonical_sha256(T.export_model(kind, model, aux))
    Xte, yte, _ = T.read("test")
    sk = T.proba(kind, model, aux, Xte)
    rt = np.asarray([pred.probability(list(map(float, row))) for row in Xte])
    diff = np.abs(sk - rt)
    thr = pred.threshold
    out = {"kind": kind, "horizon_ticks": h, "shipped_sha256": pred.sha256,
           "refit_sha256": refit_sha, "refit_reproduces_artifact": refit_sha == pred.sha256,
           "test_rows": int(len(Xte)), "max_abs_prob_diff": float(diff.max()),
           "mean_abs_prob_diff": float(diff.mean()),
           "decision_disagreements": int(((sk >= thr) != (rt >= thr)).sum())}
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
