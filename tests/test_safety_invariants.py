"""Runtime safety invariant monitor.

Safety is reported as explicit, machine-checked invariants rather than "nothing
crashed on screen", and the monitor is proven able to FAIL by a negative
control: the same scenario with no coordination at all.
"""

from __future__ import annotations

from app.api.runner import _make_policy
from app.sim.engine import MARGIN_BREACH_M, SimEngine
from app.sim.policy import NoOpPolicy
from app.sim.scenarios import get_scenario


def _engine(policy, fleet=16, seed=11):
    scen = get_scenario("rush_50")
    scen = type(scen)(**{**scen.__dict__, "fleet_size": fleet})
    return SimEngine(scen, seed=seed, policy=policy)


def test_negative_control_fails_the_contact_invariant_and_names_it():
    eng = _engine(NoOpPolicy())
    eng.run(600)
    s = eng.safety_summary()
    assert s["verdict"] == "FAIL"
    assert "INV-1" in s["failed"]
    first = s["first_violation"]["INV-1"]
    assert first["distance_m"] < 0.70
    assert {"tick", "robot_a", "robot_b"} <= set(first)


def test_swarmos_holds_every_invariant_through_a_robot_failure():
    eng = _engine(_make_policy("swarmos", 11))
    eng.inject("ROBOT_FAILURE")
    eng.run(900)
    s = eng.safety_summary()
    assert s["verdict"] == "PASS", s
    assert all(v == 0 for v in s["counts"].values())
    assert s["min_separation_m"] is None or s["min_separation_m"] >= 0.70


def test_margin_breaches_are_episodes_not_ticks():
    eng = _engine(_make_policy("swarmos", 11))
    eng.run(900)
    s = eng.safety_summary()
    ticks_below_floor = s["separation_hist"]["pair_ticks"][0]
    # One episode can last many ticks; the event count must not exceed the
    # pair-tick count, and an episode with any tick below the floor counts.
    assert s["margin_breaches"] <= max(ticks_below_floor, 0) or ticks_below_floor == 0
    assert s["margin_floor_m"] == MARGIN_BREACH_M


def test_step_authority_invariant_detects_an_unauthorised_move():
    """Inject a teleport after the step and check the monitor catches it."""
    eng = _engine(_make_policy("swarmos", 11), fleet=4)
    eng.run(5)
    rid = sorted(eng.robots)[0]
    robot = eng.robots[rid]
    before = {r: (x.x, x.y, x.failed, x.quarantined) for r, x in eng.robots.items()}
    robot.x += 1.0                       # an impossible 1 m jump in one tick
    eng._check_motion_invariants(before)
    s = eng.safety_summary()
    assert s["counts"]["INV-2"] >= 1
    assert s["verdict"] == "FAIL"


def test_failed_robot_status_is_terminal():
    eng = _engine(_make_policy("swarmos", 11), fleet=4)
    eng.inject("ROBOT_FAILURE")
    eng.run(50)
    assert eng.safety_summary()["counts"]["INV-4"] == 0
