"""Demo integrity: the Compare tab's SWARMOS arm IS the product policy.

Before this fix the co-simulation built SWARMOS with a private, stale factory
(no F1/F3/F5/F6), so what Compare showed was not what was benchmarked. These
tests pin PRODUCT_POLICY == COMPARE_SWARMOS_POLICY, the explicit reference arm,
and that cosim.py no longer constructs a controller of its own.
"""

from __future__ import annotations

import ast
import pathlib

from app.api.runner import _make_policy
from app.product import (
    COMPARE_REFERENCE,
    describe_policy,
    make_reference_policy,
    make_swarmos_policy,
)
from app.sim.cosim import ARM_BASELINE, ARM_TREATMENT, CoSimulation, make_baseline_policy, make_treatment_policy
from app.sim.engine import SimEngine
from app.sim.scenarios import get_scenario

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_compare_swarmos_policy_equals_the_product_policy():
    product = describe_policy(_make_policy("swarmos", 0))
    assert describe_policy(make_treatment_policy()) == product
    assert describe_policy(make_swarmos_policy()) == product
    assert product["fixes"] == ["F1", "F3", "F5", "F6"]
    assert product["separating_exemption"] is False and product["mutual_hold_break"] is False


def test_compare_reference_is_the_explicit_c2_reference():
    ref = describe_policy(make_baseline_policy())
    assert COMPARE_REFERENCE == "stop_and_wait+F1+F6"
    assert ref == describe_policy(make_reference_policy("stop_and_wait+F1+F6"))
    assert ref["STUCK_TICKS"] == 30 and ref["POLYLINE_SWEEP"] is True
    assert ref["release_cooldown_ticks"] == 300 and ref["fixes"] == ["F1", "F6"]


def test_compare_swarmos_arm_is_bit_identical_to_a_product_engine():
    scen = get_scenario("overlap_batch")
    cosim = CoSimulation(scen, seed=4242, fleet_size=None)
    cosim.run(400)
    solo = SimEngine(scen, seed=4242, policy=_make_policy("swarmos", 0))
    solo.run(400)
    assert cosim.treatment.trace_hash == solo.trace_hash
    assert cosim.treatment.release_cooldown_ticks == 300


def test_compare_frames_and_summary_expose_the_active_configuration():
    cosim = CoSimulation(get_scenario("rush_50"), seed=5, fleet_size=8)
    frame = cosim.run(20)
    cfg = frame["policy_config"]
    assert cfg[ARM_TREATMENT]["fixes"] == ["F1", "F3", "F5", "F6"]
    assert cfg[ARM_BASELINE]["reference"] == "stop_and_wait+F1+F6"
    assert cosim.summary()["policy_config"] == cfg


def test_cosim_module_builds_no_controller_of_its_own():
    tree = ast.parse((ROOT / "app" / "sim" / "cosim.py").read_text(encoding="utf-8"))
    built = {n.func.id for n in ast.walk(tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert not built & {"SwarmPolicy", "StopAndWaitPolicy", "TextbookStopAndWaitPolicy"}
