"""EDGE_AI_PREDICTOR: artifact loading, pure-Python inference, fallback, and
the fence that keeps the model out of the binding safety kernel."""

from __future__ import annotations

import ast
import inspect
import json
import math
import pathlib

import pytest

from app.coordination.edge_features import FEATURE_NAMES
from app.coordination.swarm_policy import SwarmPolicy
from app.ml.edge_predictor import DEFAULT_ARTIFACT, EdgePredictor, canonical_sha256, load
from app.product import attach_edge_ai, describe_policy, make_swarmos_policy
from app.sim.engine import SimEngine
from app.sim.scenarios import get_scenario

ROOT = pathlib.Path(__file__).resolve().parents[1]
N = len(FEATURE_NAMES)
CAL = {"edges": [0.0, 0.5, 1.0000001], "confidence_if_positive": [0.3, 0.9],
       "confidence_if_negative": [0.95, 0.4]}


def _tree(feature, thr, lo, hi):
    return {"f": [feature, -2, -2], "t": [thr, -2.0, -2.0], "l": [1, -1, -1],
            "r": [2, -1, -1], "v": [0.0, lo, hi]}


def _artifact(model: dict, *, features=FEATURE_NAMES, threshold=0.5) -> dict:
    return {"version": "edge_conflict_test", "features": list(features), "horizon_ticks": 15,
            "threshold": threshold, "calibration": CAL, "model": model,
            "content_sha256": canonical_sha256(model)}


def _write(tmp_path, art, name="m.json"):
    p = tmp_path / name
    p.write_text(json.dumps(art))
    return str(p)


LOGREG = {"kind": "logreg", "intercept": -1.0, "mean": [0.0] * N, "scale": [1.0] * N,
          "coef": [-2.0] + [0.0] * (N - 1)}


def test_logreg_inference_matches_the_closed_form():
    pred, status = load(_write_tmp(LOGREG), expected_features=FEATURE_NAMES)
    assert status == "ok"
    x = [0.25] + [0.0] * (N - 1)
    assert pred.probability(x) == pytest.approx(1 / (1 + math.exp(1.5)))
    out = pred.predict(x)
    assert set(out) == {"probability", "conflict", "confidence", "horizon_ticks", "model",
                        "model_sha256"}
    assert out["conflict"] is False and out["confidence"] == 0.95
    assert out["horizon_ticks"] == 15 and out["model"] == "edge_conflict_test"


def _write_tmp(model, **kw):
    import tempfile
    d = pathlib.Path(tempfile.mkdtemp())
    return _write(d, _artifact(model, **kw))


def test_tree_forest_and_gbdt_kinds_evaluate_their_trees():
    t = _tree(0, 1.0, 0.8, 0.1)
    near, far = [0.5] + [0.0] * (N - 1), [3.0] + [0.0] * (N - 1)
    tree, _ = load(_write_tmp({"kind": "tree", "tree": t}))
    assert tree.probability(near) == 0.8 and tree.probability(far) == 0.1
    forest, _ = load(_write_tmp({"kind": "forest", "trees": [t, _tree(0, 2.0, 0.6, 0.3)]}))
    assert forest.probability(near) == pytest.approx(0.7)
    assert forest.probability(far) == pytest.approx(0.2)
    gb, _ = load(_write_tmp({"kind": "gbdt", "init": 0.0, "learning_rate": 1.0,
                             "trees": [_tree(0, 1.0, 2.0, -2.0)]}))
    assert gb.probability(near) == pytest.approx(1 / (1 + math.exp(-2.0)))
    p = gb.predict(near)
    assert p["conflict"] is True and p["confidence"] == 0.9


def test_missing_corrupt_tampered_and_mismatched_models_are_unavailable(tmp_path):
    pred, status = load(str(tmp_path / "absent.json"))
    assert pred is None and status.startswith("unavailable: model artifact not found")
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    assert load(str(bad))[0] is None
    art = _artifact(LOGREG)
    art["model"]["intercept"] = 5.0                         # tampered after hashing
    pred, status = load(_write(tmp_path, art, "tampered.json"))
    assert pred is None and "integrity" in status
    pred, status = load(_write(tmp_path, _artifact(LOGREG, features=FEATURE_NAMES[::-1]), "f.json"),
                        expected_features=FEATURE_NAMES)
    assert pred is None and "features do not match" in status
    no_cal = _artifact(LOGREG)
    del no_cal["calibration"]
    assert load(_write(tmp_path, no_cal, "nocal.json"))[1].startswith("unavailable")


def test_missing_model_leaves_the_product_on_its_deterministic_fallback(tmp_path):
    policy = make_swarmos_policy()
    policy.edge_ai = policy.predictive_coordination = True
    status = attach_edge_ai(policy, str(tmp_path / "absent.json"))
    assert status.startswith("unavailable") and policy.edge_advisor is None
    ref = make_swarmos_policy()
    scen = get_scenario("overlap_batch")
    a = SimEngine(scen, seed=31, policy=policy)
    b = SimEngine(scen, seed=31, policy=ref)
    a.run(300)
    b.run(300)
    assert a.trace_hash == b.trace_hash                     # identical to V0
    assert describe_policy(policy)["edge_status"].startswith("unavailable")


class _Raising:
    threshold, horizon_ticks, version = 0.5, 15, "raising"

    def predict(self, x):
        raise RuntimeError("model crashed")


def test_inference_error_at_runtime_disables_the_advisor_and_run_continues():
    policy = make_swarmos_policy()
    policy.edge_ai = policy.predictive_coordination = True
    policy.attach_edge_advisor(_Raising(), "ok")
    eng = SimEngine(get_scenario("overlap_batch"), seed=31, policy=policy)
    eng.run(300)
    st = policy.stats()["edge_ai"]
    assert st["errors"] == 1 and st["status"].startswith("unavailable: inference error")
    assert eng.safety_summary()["verdict"] == "PASS"


class _Hostile:
    """Always screams 'conflict' with full confidence, for every pair."""
    threshold, horizon_ticks, version = 0.5, 15, "hostile"

    def predict(self, x):
        return {"probability": 1.0, "conflict": True, "confidence": 1.0,
                "horizon_ticks": 15, "model": "hostile", "model_sha256": "0"}


class _Blind:
    """Always says 'no conflict' - the model cannot grant motion either."""
    threshold, horizon_ticks, version = 0.5, 15, "blind"

    def predict(self, x):
        return {"probability": 0.0, "conflict": False, "confidence": 1.0,
                "horizon_ticks": 15, "model": "blind", "model_sha256": "0"}


@pytest.mark.parametrize("advisor", [_Hostile(), _Blind()])
def test_a_hostile_or_blind_model_cannot_break_safety(advisor):
    policy = make_swarmos_policy()
    policy.edge_ai = policy.predictive_coordination = True
    policy.attach_edge_advisor(advisor, "ok")
    scen = get_scenario("rush_50")
    scen = type(scen)(**{**scen.__dict__, "fleet_size": 16})
    eng = SimEngine(scen, seed=17, policy=policy)
    eng.run(900)
    s = eng.safety_summary()
    assert s["verdict"] == "PASS", s
    assert all(v == 0 for v in s["counts"].values())


def test_the_safety_kernel_never_references_the_model():
    src = inspect.getsource(SwarmPolicy._monitor)
    for name in ("edge_advisor", "_edge_preds", "proactive", "edge_ai", "task_auction"):
        assert name not in src, f"_monitor must not consult {name}"


def test_runtime_never_imports_numpy_or_sklearn():
    offenders = {}
    for path in sorted((ROOT / "app").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        mods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module.split(".")[0])
        bad = mods & {"numpy", "sklearn", "torch", "scipy"}
        if bad:
            offenders[str(path.relative_to(ROOT))] = sorted(bad)
    assert offenders == {}


@pytest.mark.skipif(not pathlib.Path(DEFAULT_ARTIFACT).exists(), reason="model not trained")
def test_shipped_artifact_loads_verifies_and_matches_the_runtime_features():
    pred, status = load(DEFAULT_ARTIFACT, expected_features=FEATURE_NAMES)
    assert status == "ok" and isinstance(pred, EdgePredictor)
    art = json.loads(pathlib.Path(DEFAULT_ARTIFACT).read_text())
    assert pred.sha256 == art["content_sha256"]
    parity = ROOT / "reports" / "advanced_v1" / "model_parity.json"
    if parity.exists():
        rec = json.loads(parity.read_text())
        assert rec["shipped_sha256"] == pred.sha256 == rec["refit_sha256"]
        assert rec["decision_disagreements"] == 0
