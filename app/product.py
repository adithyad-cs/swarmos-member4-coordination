"""The ONE place the SWARMOS product and its reference controllers are built.

Before this module the live Compare tab built its SWARMOS arm with a private,
stale factory (`app/sim/cosim.make_treatment_policy`) that lacked the product
fixes F1/F3/F5/F6, so what a judge watched in Compare was not the configuration
that was benchmarked. Every runtime path - the Lab run (`app/api/runner`), the
Compare co-simulation (`app/sim/cosim`) and the API benchmark - now builds its
controllers here, and `describe_policy` reads back what was actually built so
the UI can show it.

This module sits ABOVE `app/coordination` and `app/ml`: it may wire an ML
advisor into a policy by injection, while `app/coordination` itself never
imports `app/ml` (law 3, tests/test_ml_fence.py).
"""

from __future__ import annotations

from typing import Any, Optional

from app.coordination.swarm_policy import SwarmPolicy
from app.sim.policy import StopAndWaitPolicy, TextbookStopAndWaitPolicy

# Tuned stop-and-wait timeout (the fairness sweep of the baseline itself).
BASELINE_STUCK_TICKS = 8

# F6 for the product: after a stall release the same robot may not retake the
# same task for 30 s. The engine reads it from the policy it runs.
PRODUCT_RELEASE_COOLDOWN_TICKS = 300

# Reference controllers a comparison may use, by name. "+F1+F6" means the
# shared fixes the frozen C2 evaluations gave the reference arms: the
# polyline safety sweep (can only veto more) and the release cooldown.
REFERENCE_KINDS = ("stop_and_wait", "baseline", "stop_and_wait+F1+F6",
                   "baseline+F1+F6")

# The reference the Compare tab uses: the frozen C2 v3 reference arm.
COMPARE_REFERENCE = "stop_and_wait+F1+F6"

# Advanced-intelligence features (docs/ADVANCED_INTELLIGENCE_V1.md). Each is an
# independent flag; the PRODUCT value of each is fixed here and only changed by
# a promotion decision backed by a frozen evaluation.
ADVANCED_FLAGS = ("EDGE_AI_PREDICTOR", "PREDICTIVE_COORDINATION", "LIVE_DISTRIBUTED_AUCTION")
PRODUCT_ADVANCED = {"EDGE_AI_PREDICTOR": False, "PREDICTIVE_COORDINATION": False,
                    "LIVE_DISTRIBUTED_AUCTION": False}


def attach_edge_ai(policy, artifact: Optional[str] = None) -> str:
    """Load the Edge-AI model and inject it into a SwarmPolicy. Returns the
    status. A missing/corrupt/mismatched model leaves the advisor OFF with the
    reason recorded; coordination then runs deterministically without it."""
    from app.coordination.edge_features import FEATURE_NAMES
    from app.ml.edge_predictor import DEFAULT_ARTIFACT, load

    pred, status = load(artifact or DEFAULT_ARTIFACT, expected_features=FEATURE_NAMES)
    policy.attach_edge_advisor(pred, status)
    return status


def apply_advanced(policy, flags: dict, *, artifact: Optional[str] = None):
    """Switch advanced features on a SwarmPolicy, independently."""
    unknown = set(flags) - set(ADVANCED_FLAGS)
    if unknown:
        raise ValueError(f"unknown advanced flag(s) {sorted(unknown)}")
    policy.edge_ai = bool(flags.get("EDGE_AI_PREDICTOR", False))
    policy.predictive_coordination = bool(flags.get("PREDICTIVE_COORDINATION", False))
    policy.live_auction = bool(flags.get("LIVE_DISTRIBUTED_AUCTION", False))
    if policy.edge_ai or policy.predictive_coordination:
        attach_edge_ai(policy, artifact)
    return policy


def make_swarmos_policy(*, integrity: bool = False,
                        advanced: Optional[dict] = None) -> SwarmPolicy:
    """The SWARMOS product controller, exactly as shipped.

    perception_fallback ON (network-independent safety floor); lookahead_h=15
    (analytic, observe-only); F1 polyline_sweep, F3 leader_rule, F5
    standoff_breaker ON; F6 release cooldown carried for the engine. The
    separating exemption (F2 a) and mutual-hold break stay OFF.
    """
    policy = SwarmPolicy(integrity=integrity, perception_fallback=True,
                         lookahead_h=15, polyline_sweep=True,
                         leader_rule=True, standoff_breaker=True)
    policy.release_cooldown_ticks = PRODUCT_RELEASE_COOLDOWN_TICKS
    if advanced is None:
        advanced = PRODUCT_ADVANCED
    if any(advanced.values()):
        apply_advanced(policy, advanced)
    return policy


def make_reference_policy(kind: str):
    """A named reference controller. See REFERENCE_KINDS."""
    if kind not in REFERENCE_KINDS:
        raise ValueError(f"unknown reference {kind!r}; one of {REFERENCE_KINDS}")
    base, _, rest = kind.partition("+")
    if base == "stop_and_wait":
        policy = TextbookStopAndWaitPolicy()
    else:
        tuned = type("TunedStopAndWait", (StopAndWaitPolicy,),
                     {"STUCK_TICKS": BASELINE_STUCK_TICKS})
        policy = tuned()
    if rest:                                    # "+F1+F6"
        policy.POLYLINE_SWEEP = True
        policy.release_cooldown_ticks = PRODUCT_RELEASE_COOLDOWN_TICKS
    return policy


def describe_policy(policy: Any, *, reference_kind: Optional[str] = None) -> dict:
    """What a built controller ACTUALLY runs with, read back from the object."""
    out: dict = {"class": type(policy).__name__,
                 "name": getattr(policy, "name", None)}
    if reference_kind is not None:
        out["reference"] = reference_kind
    for key in ("polyline_sweep", "leader_rule", "standoff_breaker",
                "separating_exemption", "mutual_hold_break",
                "traffic_rules_enabled", "perception_fallback", "lookahead_h",
                "integrity_enabled", "POLYLINE_SWEEP", "STUCK_TICKS",
                "SAFE_SEPARATION_M", "edge_ai", "predictive_coordination",
                "live_auction", "edge_status"):
        if hasattr(policy, key):
            value = getattr(policy, key)
            out[key] = value if isinstance(value, (bool, int, float, str)) else str(value)
    out["release_cooldown_ticks"] = int(getattr(policy, "release_cooldown_ticks", 0) or 0)
    fixes = []
    if out.get("polyline_sweep") or out.get("POLYLINE_SWEEP"):
        fixes.append("F1")
    if out.get("leader_rule"):
        fixes.append("F3")
    if out.get("standoff_breaker"):
        fixes.append("F5")
    if out["release_cooldown_ticks"] > 0:
        fixes.append("F6")
    out["fixes"] = fixes
    adv = [name for name, attr in (("EDGE_AI_PREDICTOR", "edge_ai"),
                                   ("PREDICTIVE_COORDINATION", "predictive_coordination"),
                                   ("LIVE_DISTRIBUTED_AUCTION", "live_auction"))
           if getattr(policy, attr, False)]
    out["advanced"] = adv
    advisor = getattr(policy, "edge_advisor", None)
    out["edge_model"] = advisor.describe() if advisor is not None and hasattr(advisor, "describe") else None
    return out
