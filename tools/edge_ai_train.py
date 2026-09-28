"""Train, select and export the Edge-AI conflict predictor (OFFLINE tooling).

  PYTHONPATH=. python3 tools/edge_ai_train.py

Training dependencies (scikit-learn, numpy) are used HERE ONLY. The exported
artifact is evaluated at runtime by app/ml/edge_predictor.py in pure Python.

Selection discipline, fixed before any result was seen:
  1. Every candidate is FIT on the train split only (seeds 1100001-1100030).
  2. Horizon, model family and decision threshold are chosen on the
     VALIDATION split only (seeds 1200001-1200010):
       - model: best validation PR-AUC; within 0.005 of the best, the
         cheaper model wins (logreg < tree < gbdt < forest);
       - threshold: maximises validation F0.5 (precision-weighted, because a
         false alarm costs a needless proactive hold);
       - horizon: the LONGEST candidate whose best validation F0.5 is within
         0.05 of the best horizon's (more lead time when quality is
         comparable).
  3. The TEST split (seeds 1300001-1300010) is evaluated exactly ONCE, after
     every choice above is frozen, and is never used to choose anything.
The analytic lookahead (feature la_lead_ticks <= H) is scored on the same
splits as the non-ML baseline the model has to beat.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402  (tooling only)
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import average_precision_score, roc_auc_score  # noqa: E402
from sklearn.tree import DecisionTreeClassifier  # noqa: E402

from app.coordination.edge_features import FEATURE_LOOKAHEAD_H, FEATURE_NAMES  # noqa: E402
from app.ml.edge_predictor import DEFAULT_ARTIFACT, canonical_sha256, load  # noqa: E402

DATA = os.path.join(ROOT, "reports", "advanced_v1", "dataset")
REPORT = os.path.join(ROOT, "reports", "advanced_v1", "model_report.json")
HORIZONS = (10, 15, 25)
COST_ORDER = ("logreg", "tree", "gbdt", "forest")
MODEL_VERSION = "edge-conflict-v1"
SEED = 7


def read(split: str):
    X, y, meta = [], {h: [] for h in HORIZONS}, []
    with gzip.open(os.path.join(DATA, f"{split}.jsonl.gz"), "rt") as fh:
        for line in fh:
            r = json.loads(line)
            X.append(r["x"])
            for h in HORIZONS:
                y[h].append(r[f"y{h}"])
            meta.append((r["scenario"], r["seed"], r["ttc_ticks"]))
    return np.asarray(X, dtype=float), {h: np.asarray(v) for h, v in y.items()}, meta


def fbeta(p, r, beta=0.5):
    if p + r == 0:
        return 0.0
    b2 = beta * beta
    return (1 + b2) * p * r / (b2 * p + r)


def pr_at(y, pred):
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    tn = int(((pred == 0) & (y == 0)).sum())
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": round(p, 4),
            "recall": round(r, 4), "f1": round(fbeta(p, r, 1.0), 4),
            "f0.5": round(fbeta(p, r, 0.5), 4),
            "fpr": round(fp / (fp + tn), 4) if fp + tn else 0.0,
            "fnr": round(fn / (fn + tp), 4) if fn + tp else 0.0}


def best_threshold(y, prob):
    best = (0.0, 0.5)
    for t in np.linspace(0.05, 0.95, 91):
        m = pr_at(y, (prob >= t).astype(int))
        if m["f0.5"] > best[0]:
            best = (m["f0.5"], float(round(t, 3)))
    return best


def candidates():
    return {
        "logreg": LogisticRegression(max_iter=2000, C=1.0),
        "tree": DecisionTreeClassifier(max_depth=6, min_samples_leaf=50, random_state=SEED),
        "gbdt": GradientBoostingClassifier(n_estimators=80, max_depth=3, learning_rate=0.1,
                                           random_state=SEED),
        "forest": RandomForestClassifier(n_estimators=40, max_depth=8, min_samples_leaf=20,
                                         random_state=SEED, n_jobs=1),
    }


def fit(kind, model, X, y):
    if kind == "logreg":
        mean, scale = X.mean(axis=0), X.std(axis=0)
        scale[scale < 1e-9] = 1.0
        model.fit((X - mean) / scale, y)
        return model, (mean, scale)
    model.fit(X, y)
    return model, None


def proba(kind, model, aux, X):
    if kind == "logreg":
        mean, scale = aux
        return model.predict_proba((X - mean) / scale)[:, 1]
    return model.predict_proba(X)[:, 1]


def _export_tree(t, value_fn):
    return {"f": [int(v) for v in t.feature], "t": [float(v) for v in t.threshold],
            "l": [int(v) for v in t.children_left], "r": [int(v) for v in t.children_right],
            "v": [float(value_fn(t.value[i])) for i in range(t.node_count)]}


def export_model(kind, model, aux):
    if kind == "logreg":
        mean, scale = aux
        return {"kind": "logreg", "mean": [float(v) for v in mean],
                "scale": [float(v) for v in scale],
                "coef": [float(v) for v in model.coef_[0]],
                "intercept": float(model.intercept_[0])}
    if kind == "tree":
        return {"kind": "tree", "tree": _export_tree(model.tree_, lambda v: v[0][1] / v[0].sum())}
    if kind == "forest":
        return {"kind": "forest", "trees": [_export_tree(e.tree_, lambda v: v[0][1] / v[0].sum())
                                            for e in model.estimators_]}
    # gbdt: log-odds init + learning_rate * sum of regression-tree leaves
    prior = model.init_.class_prior_[1]
    return {"kind": "gbdt", "init": float(np.log(prior / (1 - prior))),
            "learning_rate": float(model.learning_rate),
            "trees": [_export_tree(e[0].tree_, lambda v: v[0][0]) for e in model.estimators_]}


def calibration(y, prob, threshold, bins=10):
    edges = [i / bins for i in range(bins + 1)]
    pos, neg = [], []
    gp = float(y[prob >= threshold].mean()) if (prob >= threshold).any() else 0.5
    gn = float(1 - y[prob < threshold].mean()) if (prob < threshold).any() else 0.5
    for i in range(bins):
        m = (prob >= edges[i]) & (prob < edges[i + 1] if i < bins - 1 else prob <= 1.0)
        n = int(m.sum())
        if n >= 30:
            rate = float(y[m].mean())
            pos.append(round(rate, 4))
            neg.append(round(1 - rate, 4))
        else:
            pos.append(round(gp, 4))
            neg.append(round(gn, 4))
    return {"edges": edges, "confidence_if_positive": pos, "confidence_if_negative": neg,
            "source": "validation split, per-bin empirical rate (bins with < 30 samples use the split-wide rate)"}


def ece(y, prob, bins=10):
    total, err = len(y), 0.0
    for i in range(bins):
        lo, hi = i / bins, (i + 1) / bins
        m = (prob >= lo) & (prob < hi if i < bins - 1 else prob <= 1.0)
        if m.any():
            err += m.sum() / total * abs(prob[m].mean() - y[m].mean())
    return round(float(err), 4)


def main() -> int:
    t0 = time.time()
    Xtr, ytr, _ = read("train")
    Xva, yva, _ = read("validation")
    lead_idx = FEATURE_NAMES.index("la_lead_ticks")
    report = {"model_version": MODEL_VERSION, "selection_rules": __doc__.split("Selection")[1],
              "rows": {"train": int(len(Xtr)), "validation": int(len(Xva))}, "horizons": {}}
    per_h = {}
    for h in HORIZONS:
        entry = {"positives_train": int(ytr[h].sum()), "positives_validation": int(yva[h].sum()),
                 "candidates": {}}
        # la_lead_ticks is FEATURE_LOOKAHEAD_H + 1 when the lookahead saw no
        # conflict, so the analytic rule can only claim min(h, that) ticks.
        analytic = (Xva[:, lead_idx] <= min(h, FEATURE_LOOKAHEAD_H)).astype(int)
        entry["analytic_lookahead_validation"] = pr_at(yva[h], analytic)
        fitted = {}
        for kind, model in candidates().items():
            t = time.time()
            m, aux = fit(kind, model, Xtr, ytr[h])
            pv = proba(kind, m, aux, Xva)
            f05, thr = best_threshold(yva[h], pv)
            entry["candidates"][kind] = {
                "pr_auc": round(float(average_precision_score(yva[h], pv)), 4),
                "roc_auc": round(float(roc_auc_score(yva[h], pv)), 4),
                "best_f0.5": round(f05, 4), "threshold": thr,
                "at_threshold": pr_at(yva[h], (pv >= thr).astype(int)),
                "fit_s": round(time.time() - t, 1)}
            fitted[kind] = (m, aux, pv, thr)
        best_auc = max(c["pr_auc"] for c in entry["candidates"].values())
        chosen = next(k for k in COST_ORDER if entry["candidates"][k]["pr_auc"] >= best_auc - 0.005)
        entry["chosen_model"] = chosen
        per_h[h] = (entry, fitted[chosen])
        report["horizons"][str(h)] = entry
        print("H", h, "chosen", chosen, json.dumps({k: (v["pr_auc"], v["best_f0.5"]) for k, v in entry["candidates"].items()}), flush=True)
    best_f = max(per_h[h][0]["candidates"][per_h[h][0]["chosen_model"]]["best_f0.5"] for h in HORIZONS)
    horizon = max(h for h in HORIZONS
                  if per_h[h][0]["candidates"][per_h[h][0]["chosen_model"]]["best_f0.5"] >= best_f - 0.05)
    entry, (model, aux, pv, thr) = per_h[horizon]
    kind = entry["chosen_model"]
    report["chosen"] = {"horizon_ticks": horizon, "model": kind, "threshold": thr}

    model_block = export_model(kind, model, aux)
    artifact = {
        "version": MODEL_VERSION, "features": list(FEATURE_NAMES), "horizon_ticks": horizon,
        "threshold": thr, "model": model_block,
        "calibration": calibration(yva[horizon], pv, thr),
        "training": {"dataset_manifest": "reports/advanced_v1/dataset/manifest.json",
                     "train_seeds": "1100001-1100030", "validation_seeds": "1200001-1200010",
                     "sklearn_random_state": SEED, "tool": "tools/edge_ai_train.py"},
        "content_sha256": canonical_sha256(model_block),
    }
    os.makedirs(os.path.dirname(DEFAULT_ARTIFACT), exist_ok=True)
    with open(DEFAULT_ARTIFACT, "w") as fh:
        json.dump(artifact, fh, sort_keys=True, separators=(",", ":"))
    with open(DEFAULT_ARTIFACT, "rb") as fh:
        file_sha = hashlib.sha256(fh.read()).hexdigest()

    # ---- held-out TEST: evaluated once, with everything above frozen --------
    Xte, yte, meta_te = read("test")
    pred, status = load(expected_features=FEATURE_NAMES)
    assert pred is not None, status
    t = time.perf_counter()
    pt = np.asarray([pred.probability(list(x)) for x in Xte])
    per_call_us = (time.perf_counter() - t) / len(Xte) * 1e6
    sk_pt = proba(kind, model, aux, Xte)
    y = yte[horizon]
    dec = (pt >= thr).astype(int)
    test = {"rows": int(len(Xte)), "positives": int(y.sum()),
            "pr_auc": round(float(average_precision_score(y, pt)), 4),
            "roc_auc": round(float(roc_auc_score(y, pt)), 4),
            "brier": round(float(((pt - y) ** 2).mean()), 4), "ece": ece(y, pt),
            "at_threshold": pr_at(y, dec),
            "analytic_lookahead": pr_at(y, (Xte[:, FEATURE_NAMES.index("la_lead_ticks")] <= min(horizon, FEATURE_LOOKAHEAD_H)).astype(int)),
            "max_abs_diff_runtime_vs_sklearn": float(np.abs(pt - sk_pt).max())}
    by_sc = {}
    for sc in sorted({m[0] for m in meta_te}):
        idx = np.asarray([m[0] == sc for m in meta_te])
        by_sc[sc] = {"model": pr_at(y[idx], dec[idx]),
                     "analytic": pr_at(y[idx], (Xte[idx, FEATURE_NAMES.index("la_lead_ticks")] <= min(horizon, FEATURE_LOOKAHEAD_H)).astype(int))}
    test["by_scenario"] = by_sc
    ttc = [m[2] for m, d, yy in zip(meta_te, dec, y) if d == 1 and yy == 1 and m[2] is not None]
    test["mean_lead_ticks_true_positives"] = round(sum(ttc) / len(ttc), 2) if ttc else None
    report["test"] = test
    report["runtime"] = {"inference_us_per_pair_pure_python": round(per_call_us, 2),
                         "artifact_bytes": os.path.getsize(DEFAULT_ARTIFACT),
                         "artifact_file_sha256": file_sha,
                         "model_content_sha256": artifact["content_sha256"]}
    report["wall_s"] = round(time.time() - t0, 1)
    with open(REPORT, "w") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
    print(json.dumps({"chosen": report["chosen"], "test": {k: test[k] for k in ("pr_auc", "roc_auc", "at_threshold", "analytic_lookahead")}, "runtime": report["runtime"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
