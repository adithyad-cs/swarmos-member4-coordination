"""SWARMOS M4 - explainable conflict risk (severity) score.

Not every predicted conflict matters equally. This scores a PredictedConflict
in [0, 1] as a fixed weighted sum of six terms, each in [0, 1], so every score
can be decomposed on screen ("0.86 = head-on 1.0, no alternative 1.0, ...").

Deterministic and hand-set on purpose: the weights are defaults chosen for
auditability, NOT tuned or learned, and they are reported as such. A learned
score would be harder to defend in a safety-adjacent role and would add
nothing the measurements could verify in the time available.

The score informs decisions and logging only. It never touches the safety
kernel, whose veto is independent of any score.
"""

from __future__ import annotations

from dataclasses import dataclass

# Each weight, and why it has the value it has.
WEIGHTS = {
    # Sooner conflicts leave less time to act; the single strongest signal.
    "temporal": 0.30,
    # How deep inside the conflict band the pair is predicted to get.
    "spatial": 0.20,
    # Head-on is the only geometry that cannot resolve by itself in a lane.
    "geometry": 0.20,
    # How long the pair is predicted to stay close (sustained vs. glancing).
    "overlap": 0.10,
    # A late CRITICAL task costs more than a late BULK one.
    "urgency": 0.10,
    # No way around (single-file lane) turns a conflict into a deadlock risk.
    "no_alternative": 0.10,
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

GEOMETRY_TERM = {"head-on": 1.0, "crossing": 0.6, "same-direction": 0.2}

BANDS = (
    (0.80, "CRITICAL"),
    (0.60, "HIGH"),
    (0.35, "MEDIUM"),
    (0.00, "LOW"),
)

# Priority weight of the most urgent class (TaskPriority.CRITICAL = 8.0).
MAX_PRIORITY_WEIGHT = 8.0


@dataclass(frozen=True)
class Risk:
    score: float
    band: str
    terms: dict

    def as_dict(self) -> dict:
        return {"score": round(self.score, 3), "band": self.band,
                "terms": {k: round(v, 3) for k, v in self.terms.items()}}


def band_of(score: float) -> str:
    for floor, name in BANDS:
        if score >= floor:
            return name
    return "LOW"


def _clamp(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def score(conflict, *, threshold_m: float, priority_weight: float = 2.0,
          in_corridor: bool = False) -> Risk:
    """Severity of one PredictedConflict (see lookahead.py)."""
    terms = {
        "temporal": _clamp(1.0 - (conflict.lead_ticks - 1) / max(1, conflict.horizon)),
        "spatial": _clamp(1.0 - conflict.min_dist_m / threshold_m),
        "geometry": GEOMETRY_TERM.get(conflict.geometry, 0.6),
        "overlap": _clamp(conflict.overlap_ticks / max(1, conflict.horizon)),
        "urgency": _clamp(priority_weight / MAX_PRIORITY_WEIGHT),
        "no_alternative": 1.0 if in_corridor else 0.3,
    }
    s = sum(WEIGHTS[k] * v for k, v in terms.items())
    return Risk(score=s, band=band_of(s), terms=terms)
