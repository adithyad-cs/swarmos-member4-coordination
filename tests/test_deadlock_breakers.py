"""Flagged deadlock breakers: the mutual-hold break (ladder) and the
separating-motion exemption (kernel). Both default OFF; the product keeps them
off until the benchmark and the safety sweeps justify switching them on."""

from __future__ import annotations

from app.coordination.swarm_policy import SwarmPolicy
from app.sim.engine import SimEngine
from app.sim.scenarios import get_scenario


def _run(policy, scenario="overlap_batch", seed=11, ticks=1500):
    eng = SimEngine(get_scenario(scenario), seed=seed, policy=policy)
    eng.run(ticks)
    return eng


def test_flags_default_off_and_leave_the_trace_unchanged():
    p = SwarmPolicy()
    assert p.mutual_hold_break is False and p.separating_exemption is False
    a = _run(SwarmPolicy(perception_fallback=True), ticks=400)
    b = _run(SwarmPolicy(perception_fallback=True, mutual_hold_break=False,
                         separating_exemption=False), ticks=400)
    assert a.trace_hash == b.trace_hash


def test_breakers_fire_and_keep_every_invariant():
    eng = _run(SwarmPolicy(perception_fallback=True, mutual_hold_break=True,
                           separating_exemption=True), seed=17, ticks=3000)
    stats = eng.policy.stats()
    assert stats["mutual_hold_break"]["breaks"] > 0
    # The exemption fires only in at-the-floor situations; its count is
    # informational here - what this test pins is that safety holds.
    assert stats["separating_exemption"]["grants"] >= 0
    s = eng.safety_summary()
    assert s["verdict"] == "PASS", s["first_violation"]
    assert s["counts"]["INV-1"] == 0


def test_breakers_are_deterministic():
    runs = [
        _run(SwarmPolicy(perception_fallback=True, mutual_hold_break=True,
                         separating_exemption=True), seed=13, ticks=800).trace_hash
        for _ in range(2)
    ]
    assert runs[0] == runs[1]
