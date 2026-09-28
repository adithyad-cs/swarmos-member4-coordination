"""F6: a stall release must not hand the task straight back to the same robot.

docs/C2_ROOT_CAUSE_ANALYSIS.md RC5 (traced: 88 release/re-assign cycles of
the same task to the same wedged robot). Engine-level, every policy alike.
"""

from __future__ import annotations

from app.api.runner import _make_policy
from app.sim.engine import SimEngine
from app.sim.scenarios import get_scenario


def _engine(cooldown):
    spec = type(get_scenario("overlap_batch"))(**{**get_scenario("overlap_batch").__dict__,
                                                   "initial_burst": 2, "fleet_size": 3})
    eng = SimEngine(spec, seed=3, policy=_make_policy("swarmos", 3))
    eng.release_cooldown_ticks = cooldown
    eng.run(5)
    return eng


def _force_stall(eng):
    from app.sim.engine import STALL_RELEASE_TICKS
    rid = next(r for r in sorted(eng.robots) if eng.robots[r].current_task_id)
    robot = eng.robots[rid]
    tid = robot.current_task_id
    eng._stall[rid] = (eng.clock.tick - STALL_RELEASE_TICKS, robot.x, robot.y)
    eng._check_stalls()
    return rid, tid


def test_released_robot_is_skipped_for_that_task_during_the_cooldown():
    eng = _engine(300)
    rid, tid = _force_stall(eng)
    assert eng.tasks[tid].assigned_robot is None
    eng._dispatch()
    assert eng.tasks[tid].assigned_robot != rid
    assert eng.cooldown_skips >= 1 or eng.tasks[tid].assigned_robot is None


def test_off_by_default_keeps_the_frozen_rule():
    eng = _engine(0)
    assert eng.release_cooldown_ticks == 0
    _force_stall(eng)
    assert eng._release_cooldown == {}
