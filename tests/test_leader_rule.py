"""F3: in the contest band the robot that is not closing keeps right of way.

docs/C2_ROOT_CAUSE_ANALYSIS.md RC3. Ladder only; the kernel is unchanged.
"""

from __future__ import annotations

import math

from app.coordination.swarm_policy import SwarmPolicy, _Encounter
from app.sim.policy import VerdictKind
from tests.test_swarm_policy import EAST, state

NORTH = math.pi / 2


def _pair():
    # A (leader) at x=1.0 heading east, away from B; B behind it heading east,
    # straight at A.
    a = state("R001", 1.0, 0.0, heading=EAST)            # moving away from B
    b = state("R002", 0.2, 0.0, heading=EAST)            # closing on A
    return a, b


def test_leader_keeps_right_of_way_and_follower_yields_both_agree():
    a, b = _pair()
    pol = SwarmPolicy(leader_rule=True)
    enc_a = _Encounter(peer_id="R002", distance=0.8, following=False, peer_failed=False)
    enc_b = _Encounter(peer_id="R001", distance=0.8, following=False, peer_failed=False)
    va = pol._leader_verdict("R001", a, enc_a, b)
    vb = pol._leader_verdict("R002", b, enc_b, a)
    assert va.kind is VerdictKind.PROCEED
    assert vb.kind is VerdictKind.YIELD and vb.yield_to == "R001"


def test_symmetric_cases_fall_back_to_the_contest():
    pol = SwarmPolicy(leader_rule=True)
    enc = _Encounter(peer_id="R002", distance=0.8, following=False, peer_failed=False)
    head_on_a = state("R001", 0.0, 0.0, heading=EAST)
    head_on_b = state("R002", 0.8, 0.0, heading=math.pi)
    assert pol._leader_verdict("R001", head_on_a, enc, head_on_b) is None   # both closing
    apart_a = state("R001", 0.0, 0.0, heading=math.pi)
    apart_b = state("R002", 0.8, 0.0, heading=EAST)
    assert pol._leader_verdict("R001", apart_a, enc, apart_b) is None      # neither closing


def test_follower_hands_back_to_the_contest_after_patience():
    from app.coordination.swarm_policy import YIELD_PATIENCE

    a, b = _pair()
    pol = SwarmPolicy(leader_rule=True)
    enc_b = _Encounter(peer_id="R001", distance=0.8, following=False, peer_failed=False)
    pol._yield_streak["R002"] = YIELD_PATIENCE - 1
    assert pol._leader_verdict("R002", b, enc_b, a) is None


def test_flag_off_is_the_old_ladder():
    assert SwarmPolicy().leader_rule is False
