"""Network-independent safety floor (perception-backed kernel fallback).

Measured on the unfixed code (3 seeds x 1200 ticks): collisions under every
degraded-radio condition tried, including 20 in a 6 s fleet-wide outage on the
narrow-aisle map. These tests pin the two properties the fix must have:

  1. with a healthy radio it adds NOTHING - the trace hash is bit-identical;
  2. with the radio degraded it keeps the fleet collision-free.
"""

from __future__ import annotations

import pytest

from app.coordination.swarm_policy import SwarmPolicy
from app.sim.engine import SimEngine
from app.sim.scenarios import get_scenario


def _run(scenario, fleet, seed, fallback, ticks, inject=()):
    scen = get_scenario(scenario)
    scen = type(scen)(**{**scen.__dict__, "fleet_size": fleet})
    eng = SimEngine(scen, seed=seed,
                    policy=SwarmPolicy(perception_fallback=fallback))
    for _ in range(ticks):
        for at, kind, kw in inject:
            if eng.clock.tick == at:
                eng.inject(kind, **kw)
        eng.step()
    return eng


def test_fallback_changes_nothing_when_the_radio_is_healthy():
    off = _run("rush_50", 16, 11, False, 400)
    on = _run("rush_50", 16, 11, True, 400)
    assert on.trace_hash == off.trace_hash
    assert on.policy.sensed_blocks == 0


OUTAGE = ((300, "LINK_IMPAIR", {"drop_pct": 100.0, "latency_ms": 0.0,
                                "ticks": 60}),)


@pytest.mark.parametrize("seed", [11, 13])
def test_fleet_wide_outage_stays_collision_free_with_fallback(seed):
    eng = _run("narrow_aisle_deadlock", 24, seed, True, 900, OUTAGE)
    assert eng.kpis()["collisions"] == 0
    assert eng.policy.sensed_blocks > 0      # it actually did the work


def test_the_gap_is_real_without_the_fallback():
    """The negative control for this fix: same outage, fallback off. If this
    ever starts passing with zero collisions the scenario no longer exercises
    the gap and the positive tests above prove nothing."""
    total = sum(
        _run("narrow_aisle_deadlock", 24, seed, False, 900, OUTAGE)
        .kpis()["collisions"] for seed in (11, 13)
    )
    assert total > 0


def test_single_robot_blackout_is_collision_free_with_fallback():
    inject = ((300, "COMM_BLACKOUT", {}),)
    for seed in (11, 13, 17):
        assert _run("rush_50", 16, seed, True, 900, inject).kpis()["collisions"] == 0
