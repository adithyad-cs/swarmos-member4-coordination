"""PREDICTIVE_COORDINATION: pre-hold decisions and their anti-oscillation rules."""

from __future__ import annotations

from app.coordination.models import AMRState, MovementIntent, Position, RobotStatus
from app.coordination.proactive import (
    CONF_MIN,
    COOLDOWN_TICKS,
    MAX_HOLD_TICKS,
    MIN_HOLD_TICKS,
    OFF_RATIO,
    STALE_TICKS,
    ProactiveCoordinator,
    holder,
)
from app.coordination.swarm_policy import PeerView

THR = 0.5


def _s(rid, x, y, *, heading=0.0, v=0.0, path=None, task="T"):
    intent = None
    if path:
        intent = MovementIntent(target=Position(x=path[-1][0], y=path[-1][1]),
                                path=[Position(x=a, y=b) for a, b in path],
                                intent_id=f"i-{rid}")
    return AMRState(robot_id=rid, timestamp=0.0, position=Position(x=x, y=y), velocity=v,
                    heading=heading, status=RobotStatus.MOVING, battery=90.0,
                    current_task_id=task, movement_intent=intent)


def _pred(p, tick, *, conf=0.9):
    return {"probability": p, "conflict": p >= THR, "confidence": conf, "tick": tick,
            "ttc_s": 1.2, "horizon_ticks": 15, "model": "test"}


# A (R001) drives east towards B (R002), which drives north, across: A must hold.
A = _s("R001", 0.0, 0.0, heading=0.0, v=1.0, path=[(3, 0)])
B = _s("R002", 2.0, 0.0, heading=1.5708, v=1.0, path=[(2, 3)])
VIEWS = {"R002": PeerView(state=B)}


def test_holder_rule_is_symmetric_and_deterministic():
    assert holder(A, B) == holder(B, A) == "R001"          # closing robot holds
    idle = _s("R003", 0.0, 5.0, path=[(0, 9)], task=None)
    busy = _s("R004", 0.0, 9.0, path=[(0, 5)])
    # both closing: the robot without a task holds for the one with a task
    assert holder(idle, busy) == holder(busy, idle) == "R003"
    long_ = _s("R005", 0.0, 0.0, path=[(0, 1), (0, 9)])
    short = _s("R006", 0.0, 2.0, path=[(0, -1)])
    assert holder(long_, short) == holder(short, long_) == "R005"   # longer route holds
    twin_a = _s("R007", 0.0, 0.0, path=[(0, 1)])
    twin_b = _s("R008", 0.0, 1.0, path=[(0, 0)])
    assert holder(twin_a, twin_b) == holder(twin_b, twin_a) == "R008"


def test_pre_hold_enters_only_on_a_confident_fresh_positive():
    pc = ProactiveCoordinator()
    assert pc.decide("R001", A, VIEWS, {"R002": _pred(0.4, 0)}, 0, THR, imminent=False) is None
    assert pc.decide("R001", A, VIEWS, {"R002": _pred(0.9, 0, conf=CONF_MIN - 0.01)}, 0, THR,
                     imminent=False) is None
    assert pc.stats.rejected_low_confidence == 1
    assert pc.decide("R001", A, VIEWS, {"R002": _pred(0.9, 0)}, STALE_TICKS + 1, THR,
                     imminent=False) is None
    assert pc.stats.rejected_stale == 1
    h = pc.decide("R001", A, VIEWS, {"R002": _pred(0.9, 5)}, 5, THR, imminent=False)
    assert h is not None and h.peer == "R002"
    assert [e["type"] for e in pc.events] == ["PRE-HOLD"]


def test_the_robot_that_should_proceed_never_pre_holds():
    pc = ProactiveCoordinator()
    views = {"R001": PeerView(state=A)}
    assert pc.decide("R002", B, views, {"R001": _pred(0.9, 0)}, 0, THR, imminent=False) is None
    assert pc.stats.not_holder == 1


def test_no_pre_hold_for_a_peer_that_already_holds():
    pc = ProactiveCoordinator()
    views = {"R002": PeerView(state=B, holding=True)}
    assert pc.decide("R001", A, views, {"R002": _pred(0.9, 0)}, 0, THR, imminent=False) is None
    assert pc.stats.rejected_peer_holding == 1


def test_minimum_hold_hysteresis_and_release_on_clear():
    pc = ProactiveCoordinator()
    assert pc.decide("R001", A, VIEWS, {"R002": _pred(0.9, 0)}, 0, THR, imminent=False)
    # probability falls below the entry threshold but above OFF_RATIO x threshold: stay
    mid = THR * (OFF_RATIO + 1) / 2
    for t in range(1, MIN_HOLD_TICKS + 3):
        assert pc.decide("R001", A, VIEWS, {"R002": _pred(mid, t)}, t, THR, imminent=False)
    # a clear signal before MIN_HOLD would still hold; after it, the hold releases
    t = MIN_HOLD_TICKS + 3
    assert pc.decide("R001", A, VIEWS, {"R002": _pred(0.05, t)}, t, THR, imminent=False) is None
    assert pc.stats.released_cleared == 1
    assert pc.events[-1]["type"] == "RESUME" and pc.events[-1]["reason"] == "cleared"


def test_release_before_minimum_hold_is_refused():
    pc = ProactiveCoordinator()
    pc.decide("R001", A, VIEWS, {"R002": _pred(0.9, 0)}, 0, THR, imminent=False)
    for t in range(1, MIN_HOLD_TICKS):
        assert pc.decide("R001", A, VIEWS, {"R002": _pred(0.0, t)}, t, THR, imminent=False)
    assert pc.stats.resumes == 0


def test_stale_prediction_counts_as_clear_and_hard_cap_times_out():
    pc = ProactiveCoordinator()
    pc.decide("R001", A, VIEWS, {"R002": _pred(0.9, 0)}, 0, THR, imminent=False)
    assert pc.decide("R001", A, VIEWS, {"R002": _pred(0.9, 0)}, MIN_HOLD_TICKS, THR,
                     imminent=False) is None                  # stale -> not "still"
    pc2 = ProactiveCoordinator()
    pc2.decide("R001", A, VIEWS, {"R002": _pred(0.9, 0)}, 0, THR, imminent=False)
    released = None
    for t in range(1, MAX_HOLD_TICKS + 1):
        if pc2.decide("R001", A, VIEWS, {"R002": _pred(0.9, t)}, t, THR, imminent=False) is None:
            released = t
            break
    assert released == MAX_HOLD_TICKS and pc2.stats.released_timeout == 1


def test_imminent_conflict_hands_the_robot_back_to_the_reactive_ladder():
    pc = ProactiveCoordinator()
    pc.decide("R001", A, VIEWS, {"R002": _pred(0.9, 0)}, 0, THR, imminent=False)
    assert pc.decide("R001", A, VIEWS, {"R002": _pred(0.9, 1)}, 1, THR, imminent=True) is None
    assert pc.stats.released_imminent == 1
    assert pc.decide("R001", A, VIEWS, {"R002": _pred(0.9, 2)}, 2, THR, imminent=True) is None
    assert pc.stats.pre_holds == 1


def test_cooldown_prevents_hold_release_hold_oscillation():
    pc = ProactiveCoordinator()
    pc.decide("R001", A, VIEWS, {"R002": _pred(0.9, 0)}, 0, THR, imminent=False)
    t = MIN_HOLD_TICKS
    pc.decide("R001", A, VIEWS, {"R002": _pred(0.0, t)}, t, THR, imminent=False)
    # the prediction flips back positive every tick; no new pre-hold during cooldown
    holds = 0
    for u in range(t + 1, t + COOLDOWN_TICKS):
        if pc.decide("R001", A, VIEWS, {"R002": _pred(0.9, u)}, u, THR, imminent=False):
            holds += 1
            break
    assert holds == 0 and pc.stats.rejected_cooldown >= 1
    u = t + COOLDOWN_TICKS
    assert pc.decide("R001", A, VIEWS, {"R002": _pred(0.9, u)}, u, THR, imminent=False)
    assert pc.stats.repeat_holds_same_peer == 1
