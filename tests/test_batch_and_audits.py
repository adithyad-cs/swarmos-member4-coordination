"""Batch (fixed-workload) scenarios, the backtrack fix, the deadlock audit and
the explainable decision log."""

from __future__ import annotations

import math

import pytest

from app.api.runner import POLICIES, _make_policy
from app.coordination.models import RobotStatus
from app.coordination.traffic import TrafficRules
from app.sim.deadlock_audit import DeadlockAudit
from app.sim.engine import SimEngine, _drop_backtrack
from app.sim.policy import TextbookStopAndWaitPolicy, Verdict, VerdictKind
from app.sim.scenarios import get_scenario


def _small_batch(name="overlap_batch", tasks=4, fleet=3):
    spec = get_scenario(name)
    return type(spec)(**{**spec.__dict__, "initial_burst": tasks, "fleet_size": fleet})


# -- batch scenarios --------------------------------------------------------

def test_batch_scenarios_are_fixed_workloads():
    for name in ("overlap_batch", "open_floor_batch"):
        spec = get_scenario(name)
        assert spec.batch and spec.task_rate_per_s == 0.0 and spec.initial_burst > 0
        assert spec.idle_parking


@pytest.mark.parametrize("policy", ["stop_and_wait", "swarmos"])
def test_small_batch_finishes_with_a_makespan_and_no_collisions(policy):
    eng = SimEngine(_small_batch(), seed=11, policy=_make_policy(policy, 11))
    while not eng.finished:
        eng.step()
    k = eng.kpis()
    assert k["tasks_complete"] == k["tasks_total"] == 4
    assert k["makespan_s"] is not None and k["makespan_s"] > 0
    assert k["did_not_finish"] is False
    assert k["collisions"] == 0
    assert 0.0 < k["path_efficiency"] <= 1.2


def test_batch_run_is_deterministic():
    hashes = []
    for _ in range(2):
        eng = SimEngine(_small_batch(), seed=13, policy=_make_policy("swarmos", 13))
        while not eng.finished:
            eng.step()
        hashes.append((eng.trace_hash, eng.kpis()["makespan_s"],
                       eng.decisions.digest()))
    assert hashes[0] == hashes[1]            # includes INV-6: decision digest


def test_textbook_baseline_is_registered_and_untuned():
    assert "stop_and_wait" in POLICIES
    p = _make_policy("stop_and_wait", 11)
    assert isinstance(p, TextbookStopAndWaitPolicy)
    assert p.STUCK_TICKS == 30
    assert _make_policy("baseline", 11).STUCK_TICKS == 8


# -- the leading-waypoint backtrack fix ----------------------------------------

def test_waypoint_behind_the_robot_on_its_line_is_dropped():
    path = [(12.5, 17.5), (12.5, 0.5)]           # heading north (y decreasing)
    assert _drop_backtrack((12.5, 17.44), path) == path[1:]


def test_waypoint_ahead_or_off_line_is_kept():
    path = [(12.5, 17.5), (12.5, 0.5)]
    assert _drop_backtrack((12.5, 17.6), path) == path     # waypoint is ahead
    assert _drop_backtrack((12.8, 17.44), path) == path    # not on the line
    assert _drop_backtrack((1.0, 1.0), [(2.0, 2.0)]) == [(2.0, 2.0)]


def test_swarmos_pairs_stay_outside_the_kernel_floor_after_the_fix():
    """The traced defect pushed pairs inside 0.75 m, where the kernel freezes
    both robots. On the same seed the fix keeps every pair outside it."""
    spec = get_scenario("overlap_batch")
    eng = SimEngine(spec, seed=11, policy=_make_policy("swarmos", 11))
    eng.run(2000)
    s = eng.safety_summary()
    assert s["counts"]["INV-1"] == 0
    assert s["min_separation_m"] >= 0.70


# -- one-way lanes ---------------------------------------------------------------

@pytest.mark.parametrize("name", ["overlap_batch", "rush_50", "narrow_aisle_deadlock"])
def test_traffic_rules_keep_every_floor_strongly_connected(name):
    eng = SimEngine(get_scenario(name), seed=11)
    rules = TrafficRules(eng.warehouse)
    assert rules.strongly_connected()
    assert rules.corridor_cells


def test_traffic_rules_forbid_wrong_way_moves_in_a_corridor():
    eng = SimEngine(get_scenario("overlap_batch"), seed=11)
    rules = TrafficRules(eng.warehouse)
    cell = sorted(c for c in rules.corridor_cells if rules.direction[c][0] == 0)[0]
    dx, dy = rules.direction[cell]
    ahead = (cell[0] + dx, cell[1] + dy)
    behind = (cell[0] - dx, cell[1] - dy)
    assert rules.edge_allowed(cell, ahead) or ahead not in rules.direction
    assert not rules.edge_allowed(cell, behind)


# -- deadlock audit -----------------------------------------------------------------

def _v(rid, kind, peer):
    return Verdict(robot_id=rid, kind=kind, reason="t", conflict_with=(peer,))


def test_deadlock_audit_finds_cycles_and_times_them():
    audit = DeadlockAudit()
    cyc = {"A": _v("A", VerdictKind.WAIT, "B"), "B": _v("B", VerdictKind.YIELD, "C"),
           "C": _v("C", VerdictKind.WAIT, "A"), "D": _v("D", VerdictKind.WAIT, "A")}
    for tick in range(12):
        audit.observe(tick, cyc)
    audit.observe(12, {"A": Verdict(robot_id="A", kind=VerdictKind.PROCEED, reason="ok")})
    s = audit.summary()
    assert s["deadlocks_formed"] == 1
    assert s["max_duration_ticks"] == 12
    assert s["persistent_deadlocks"] == 1
    assert s["unresolved"] == 0


def test_moving_robots_form_no_wait_cycle():
    audit = DeadlockAudit()
    audit.observe(0, {"A": Verdict(robot_id="A", kind=VerdictKind.PROCEED, reason="ok",
                                   conflict_with=("B",)),
                      "B": _v("B", VerdictKind.WAIT, "A")})
    assert audit.summary()["deadlocks_formed"] == 0


# -- decision log -------------------------------------------------------------------

def test_decision_records_explain_prediction_risk_decision_and_outcome():
    eng = SimEngine(get_scenario("overlap_batch"), seed=11,
                    policy=_make_policy("swarmos", 11))
    eng.run(1500)
    recs = list(eng.decisions.records)
    assert recs, "expected at least one HIGH/CRITICAL predicted conflict"
    r = recs[0]
    assert r["risk"]["band"] in ("HIGH", "CRITICAL")
    assert set(r["risk"]["terms"]) >= {"temporal", "geometry", "no_alternative"}
    assert r["prediction"]["lead_ticks"] >= 1
    for rid in r["robots"]:
        assert r["decisions"][rid] is None or "reason" in r["decisions"][rid]
    resolved = [x for x in recs if x["outcome"] is not None]
    assert resolved and resolved[0]["outcome"]["result"] in (
        "conflict_occurred", "window_passed")


# -- reroute hint when the blocker shares the robot's cell --------------------

def test_blocker_in_same_cell_hints_the_adjacent_cell_toward_it():
    eng = SimEngine(get_scenario("rush_50"), seed=11, policy=_make_policy("swarmos", 11))
    a, b = sorted(eng.robots.values(), key=lambda r: r.robot_id)[:2]
    a.x, a.y = 22.98, 1.5
    b.x, b.y = 22.19, 1.5                 # same cell (22, 1), west of a
    assert eng.warehouse.m_to_cell(a.x, a.y) == eng.warehouse.m_to_cell(b.x, b.y)
    assert eng._blocker_cell(a, b) == (21, 1)
    b.x, b.y = 22.5, 1.9                  # same cell, mostly south of a
    a.x, a.y = 22.5, 1.1
    assert eng._blocker_cell(a, b) == (22, 2)
    b.x, b.y = 25.5, 1.5                  # different cell: the peer's own cell
    assert eng._blocker_cell(a, b) == (25, 1)


def test_battery_drained_robot_reaches_a_charger():
    """Regression: the drained robot wedged behind an idle peer sharing its
    cell for 5400+ ticks because the reroute hint was erased."""
    eng = SimEngine(type(get_scenario("rush_50"))(**{**get_scenario("rush_50").__dict__,
                                                      "fleet_size": 8}),
                    seed=11, policy=_make_policy("swarmos", 11))
    eng.run(100)
    rid = eng.inject("BATTERY_DRAIN", level=8.0)["robots"][0]
    for _ in range(3000):
        eng.step()
        if eng.robots[rid].status is RobotStatus.CHARGING:
            break
    assert eng.robots[rid].status is RobotStatus.CHARGING
    assert eng.safety_summary()["verdict"] == "PASS"


# -- livelock audit (moving but never closer to the goal) - observe-only ----

def _engine_with_a_working_robot():
    spec = type(get_scenario("overlap_batch"))(**{**get_scenario("overlap_batch").__dict__,
                                                   "initial_burst": 4, "fleet_size": 3})
    eng = SimEngine(spec, seed=11, policy=_make_policy("swarmos", 11))
    for _ in range(200):
        eng.step()
        busy = [r for r in sorted(eng.robots) if eng._goal_cell.get(r)
                and eng.robots[r].current_task_id]
        if busy:
            return eng, busy[0]
    raise AssertionError("no robot picked up a task")


def test_livelock_episode_opens_only_after_the_full_window_and_counts_once():
    from app.sim.engine import LIVELOCK_WINDOW_TICKS

    eng, rid = _engine_with_a_working_robot()
    robot = eng.robots[rid]
    goal = eng._goal_cell[rid]
    task = robot.current_task_id
    now = eng.clock.tick
    # best distance 0 can never be beaten, so only the window decides
    eng._progress[rid] = (goal, 0, now - LIVELOCK_WINDOW_TICKS + 1, False)
    assert eng._audit_livelock(rid, robot) is False
    eng._progress[rid] = (goal, 0, now - LIVELOCK_WINDOW_TICKS, False)
    assert eng._audit_livelock(rid, robot) is True
    assert eng._audit_livelock(rid, robot) is True          # same episode
    assert eng.livelock_episodes == 1 and eng.livelock_ticks == 2
    # observe-only: the task and the robot are untouched
    assert robot.current_task_id == task and eng._goal_cell[rid] == goal


def test_livelock_window_resets_on_a_new_best_distance_or_a_new_goal():
    eng, rid = _engine_with_a_working_robot()
    robot = eng.robots[rid]
    goal = eng._goal_cell[rid]
    old = eng.clock.tick - 10_000
    eng._progress[rid] = (goal, 10_000, old, True)          # any real distance is a new best
    assert eng._audit_livelock(rid, robot) is False
    assert eng._progress[rid][2] == eng.clock.tick and eng._progress[rid][3] is False
    eng._progress[rid] = ((-1, -1), 0, old, True)           # a different goal restarts
    assert eng._audit_livelock(rid, robot) is False
    assert eng._progress[rid][0] == goal and eng.livelock_episodes == 0


def test_textbook_lockstep_livelock_is_counted_not_hidden():
    """System-audit finding: seed 13, 3 robots, 4 tasks. Both stop-and-wait
    arms reroute a loaded robot and a parking-bound peer in lockstep through
    the same single-file aisle; the robots keep moving between hold-offs, so
    the stall release never fires. The run is a did-not-finish and the audits
    must say why. SWARMOS finishes the same batch."""
    from tools.run_experiment import run_one

    def run(arm):
        return run_one({"scenario": "overlap_batch", "arm": arm, "seed": 13,
                        "condition": "normal", "injections": [], "ticks": None,
                        "overrides": {"initial_burst": 4, "fleet_size": 3,
                                      "duration_s": 600.0}})
    saw = run("stop_and_wait")
    assert saw["did_not_finish"] is True
    assert saw["livelock_episodes"] >= 1
    assert saw["stall_releases"] == 0                       # invisible to the stall release
    assert saw["collisions"] == 0 and saw["safety_verdict"] == "PASS"
    sw = run("swarmos")
    assert sw["did_not_finish"] is False and sw["livelock_episodes"] == 0


def test_livelock_audit_does_not_change_the_trace():
    import app.sim.engine as E
    from tools.run_experiment import run_one

    job = {"scenario": "overlap_batch", "arm": "baseline", "seed": 11,
           "condition": "normal", "injections": [], "ticks": 3000,
           "overrides": {"initial_burst": 4, "fleet_size": 3}}
    with_audit = run_one(job)
    saved = E.LIVELOCK_WINDOW_TICKS
    E.LIVELOCK_WINDOW_TICKS = 10 ** 9
    try:
        without = run_one(job)
    finally:
        E.LIVELOCK_WINDOW_TICKS = saved
    assert with_audit["livelock_episodes"] >= 1 and without["livelock_episodes"] == 0
    assert with_audit["trace_hash"] == without["trace_hash"]
