"""F5: a mutual hold is broken by exactly one deterministic loser.

docs/C2_ROOT_CAUSE_ANALYSIS.md RC4. It only turns a hold into a
hold-and-replan (REROUTE, zero motion this tick), so it grants no motion.
"""

from __future__ import annotations

import math

from app.coordination.swarm_policy import (
    STANDOFF_SWAP_TICKS,
    STANDOFF_TICKS,
    PeerView,
    SwarmPolicy,
)
from app.sim.policy import Verdict, VerdictKind
from tests.test_swarm_policy import EAST, state


def _held(rid, peer):
    return Verdict(robot_id=rid, kind=VerdictKind.WAIT, reason="held", conflict_with=(peer,))


def _run(pol, rid, me, peer_state, ticks, start_tick=0, holding=True):
    inbox = {peer_state.robot_id: PeerView(state=peer_state, holding=holding)}
    out = None
    for t in range(ticks):
        pol._tick = start_tick + t
        out = pol._break_standoff(rid, me, _held(rid, peer_state.robot_id), inbox)
    return out


def test_both_robots_agree_on_one_loser_after_the_window():
    a = state("R001", 0.0, 0.0, heading=EAST)
    b = state("R002", 0.78, 0.0, heading=math.pi)
    pa, pb = SwarmPolicy(standoff_breaker=True), SwarmPolicy(standoff_breaker=True)
    va = _run(pa, "R001", a, b, STANDOFF_TICKS)
    vb = _run(pb, "R002", b, a, STANDOFF_TICKS)
    kinds = {va.kind, vb.kind}
    assert kinds == {VerdictKind.WAIT, VerdictKind.REROUTE}      # exactly one gives way
    loser = vb if vb.kind is VerdictKind.REROUTE else va
    assert loser.robot_id == "R002"                               # epoch 0: higher id
    assert loser.speed_scale == 0.0 and loser.needs_replan        # no motion granted
    assert (0.0, 0.0) in loser.avoid_points                       # routes around the peer


def test_not_before_the_window_and_not_if_the_peer_is_moving():
    a = state("R001", 0.0, 0.0, heading=EAST)
    b = state("R002", 0.78, 0.0, heading=math.pi)
    pol = SwarmPolicy(standoff_breaker=True)
    assert _run(pol, "R002", b, a, STANDOFF_TICKS - 1).kind is VerdictKind.WAIT
    pol2 = SwarmPolicy(standoff_breaker=True)
    assert _run(pol2, "R002", b, a, STANDOFF_TICKS * 3, holding=False).kind is VerdictKind.WAIT


def test_the_loser_alternates_between_epochs():
    a = state("R001", 0.0, 0.0, heading=EAST)
    b = state("R002", 0.78, 0.0, heading=math.pi)
    pol = SwarmPolicy(standoff_breaker=True)
    v = _run(pol, "R001", a, b, STANDOFF_TICKS, start_tick=STANDOFF_SWAP_TICKS)
    assert v.kind is VerdictKind.REROUTE                          # epoch 1: lower id


def test_avoid_points_reach_the_engine_hint():
    from app.api.runner import _make_policy
    from app.sim.engine import SimEngine
    from app.sim.scenarios import get_scenario

    eng = SimEngine(get_scenario("rush_50"), seed=5, policy=_make_policy("swarmos", 5))
    eng.run(30)
    rid = sorted(eng.robots)[0]
    r = eng.robots[rid]
    if not r.path:
        r.assign_path([(r.x + 3.0, r.y)], intent_id="I")
    v = Verdict(robot_id=rid, kind=VerdictKind.REROUTE, reason="t",
                avoid_points=((10.5, 3.5),))
    eng._apply_verdicts({rid: v})
    assert eng.warehouse.m_to_cell(10.5, 3.5) in eng._avoid_hint[rid]


def test_flag_off_by_default():
    assert SwarmPolicy().standoff_breaker is False
