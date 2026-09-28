"""Edge-AI conflict predictor: runtime inference, pure Python.

The model is trained OFFLINE by tools/edge_ai_train.py (scikit-learn, on
simulation data split by seed) and exported to a JSON artifact. At runtime
this module only evaluates that artifact: no numpy, no scikit-learn, no
network, a few microseconds per call - it runs inside each robot's decision
loop.

It is ADVISORY (law 3). It never sees or touches the safety kernel. The
coordination layer receives an EdgePredictor through injection
(app/product.py) and may use its output to shape a PROPOSAL; every proposal
still passes SwarmPolicy._monitor, which never consults this module.

Artifact integrity: the artifact stores `content_sha256`, the sha256 of the
canonical JSON of its `model` block. load() recomputes it; a missing file, bad
JSON, wrong feature list or hash mismatch makes the predictor UNAVAILABLE with
a stated reason, and the caller falls back to deterministic coordination.

Confidence: the probability that the thresholded decision (conflict / no
conflict) is correct, taken from the validation-set reliability table of the
probability bin the prediction falls in. It is an empirical, calibrated
quantity, not a restatement of the probability.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import struct
from typing import Optional

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
DEFAULT_ARTIFACT = os.path.join(MODELS_DIR, "edge_conflict_v1.json")


def canonical_sha256(model_block: dict) -> str:
    blob = json.dumps(model_block, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def _as_float32(x: list[float]) -> list[float]:
    """Round features to float32, as scikit-learn does before walking a tree,
    so a value exactly on a split threshold goes the same way as in training."""
    n = len(x)
    return list(struct.unpack(f"{n}f", struct.pack(f"{n}f", *x)))


def _tree_value(tree: dict, x: list[float]) -> float:
    node = 0
    feat, thr, left, right, val = tree["f"], tree["t"], tree["l"], tree["r"], tree["v"]
    while left[node] != -1:
        node = left[node] if x[feat[node]] <= thr[node] else right[node]
    return val[node]


class EdgePredictor:
    """A loaded, verified model. Construct with load()."""

    def __init__(self, artifact: dict, sha256: str) -> None:
        self.artifact = artifact
        m = artifact["model"]
        self.kind: str = m["kind"]
        self.version: str = artifact["version"]
        self.sha256: str = sha256
        self.feature_names: list[str] = list(artifact["features"])
        self.horizon_ticks: int = int(artifact["horizon_ticks"])
        self.threshold: float = float(artifact["threshold"])
        self._m = m
        cal = artifact["calibration"]
        self._edges: list[float] = cal["edges"]
        self._conf_pos: list[float] = cal["confidence_if_positive"]
        self._conf_neg: list[float] = cal["confidence_if_negative"]

    # -- inference --------------------------------------------------------

    def probability(self, x: list[float]) -> float:
        m = self._m
        if self.kind == "logreg":
            z = m["intercept"]
            for xi, mu, sd, w in zip(x, m["mean"], m["scale"], m["coef"]):
                z += w * ((xi - mu) / sd)
        elif self.kind == "gbdt":
            x = _as_float32(x)
            z = m["init"]
            lr = m["learning_rate"]
            for tree in m["trees"]:
                z += lr * _tree_value(tree, x)
        elif self.kind == "tree":
            x = _as_float32(x)
            return max(0.0, min(1.0, _tree_value(m["tree"], x)))
        elif self.kind == "forest":
            x = _as_float32(x)
            s = sum(_tree_value(t, x) for t in m["trees"])
            return max(0.0, min(1.0, s / len(m["trees"])))
        else:                                             # pragma: no cover
            raise ValueError(f"unknown model kind {self.kind}")
        if z >= 0:
            return 1.0 / (1.0 + math.exp(-z))
        e = math.exp(z)
        return e / (1.0 + e)

    def _bin(self, p: float) -> int:
        for i in range(len(self._edges) - 1):
            if p < self._edges[i + 1]:
                return i
        return len(self._edges) - 2

    def predict(self, x: list[float]) -> dict:
        if len(x) != len(self.feature_names):
            raise ValueError("feature vector length does not match the model")
        p = self.probability(x)
        positive = p >= self.threshold
        b = self._bin(p)
        conf = self._conf_pos[b] if positive else self._conf_neg[b]
        return {"probability": p, "conflict": positive, "confidence": conf,
                "horizon_ticks": self.horizon_ticks, "model": self.version,
                "model_sha256": self.sha256}

    def describe(self) -> dict:
        return {"version": self.version, "kind": self.kind, "sha256": self.sha256,
                "horizon_ticks": self.horizon_ticks, "threshold": self.threshold,
                "features": len(self.feature_names)}


def load(path: str = DEFAULT_ARTIFACT, *, expected_features=None
         ) -> tuple[Optional[EdgePredictor], str]:
    """Return (predictor, status). predictor is None when unavailable; status
    then says why. Never raises: an unavailable model is a normal state that
    the coordination layer must survive."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            artifact = json.load(fh)
    except FileNotFoundError:
        return None, f"unavailable: model artifact not found ({os.path.basename(path)})"
    except (OSError, ValueError) as exc:
        return None, f"unavailable: model artifact unreadable ({type(exc).__name__})"
    try:
        digest = canonical_sha256(artifact["model"])
        if digest != artifact.get("content_sha256"):
            return None, "unavailable: model artifact failed its integrity check"
        if expected_features is not None and list(artifact["features"]) != list(expected_features):
            return None, "unavailable: model features do not match the runtime features"
        return EdgePredictor(artifact, digest), "ok"
    except (KeyError, TypeError, ValueError) as exc:
        return None, f"unavailable: model artifact malformed ({type(exc).__name__})"
