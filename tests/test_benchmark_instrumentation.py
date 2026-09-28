"""C2 benchmark instrumentation and statistics.

Pins: every metric the frozen C2 protocol requires is recorded; the paired
statistics match a hand computation; censoring and DNF are handled as the
protocol states; instrumentation never changes the trace.
"""

from __future__ import annotations

import math

from app.api.runner import _make_policy
from app.db.stats import paired
from app.sim.engine import SimEngine
from app.sim.scenarios import get_scenario
from tools.run_experiment import run_one, summarise

REQUIRED = {
    "makespan_s", "did_not_finish", "tasks_complete", "tasks_per_min", "t90_s",
    "t90_censored_s", "makespan_censored_s", "deadlock", "collisions",
    "min_separation_m", "margin_breaches", "wait_count", "yield_count",
    "reroute_count", "conflicts", "resolved_conflicts", "predicted_conflicts",
    "backtracks_dropped", "replans", "stop_events", "held_work_ticks",
    "comm_hold_ticks", "invariant_failures", "trace_hash", "livelock_episodes",
}


def _job(arm, burst=4, fleet=3, cap=None, seed=11):
    over = {"initial_burst": burst, "fleet_size": fleet}
    if cap is not None:
        over["duration_s"] = cap
    return {"scenario": "overlap_batch", "arm": arm, "seed": seed,
            "condition": "normal", "overrides": over, "injections": [], "ticks": None}


def test_every_required_metric_is_recorded():
    for arm in ("stop_and_wait", "baseline", "swarmos"):
        rec = run_one(_job(arm))
        missing = REQUIRED - set(rec)
        assert not missing, (arm, missing)
        assert rec["deadlock"]["persistent_deadlocks"] >= 0
        assert rec["t90_s"] is not None and rec["t90_s"] <= rec["makespan_s"]


def test_dnf_is_explicit_and_censored_at_the_cap():
    rec = run_one(_job("swarmos", burst=24, fleet=2, cap=20.0))
    assert rec["did_not_finish"] is True
    assert rec["makespan_s"] is None
    assert rec["makespan_censored_s"] == 20.0
    assert rec["t90_censored_s"] == 20.0


def test_paired_ci_matches_hand_computation():
    # baseline 100 on every seed; treatment 80, 90, 70 -> reductions 20, 10, 30 %
    pc = paired("m", {1: (100.0, 80.0), 2: (100.0, 90.0), 3: (100.0, 70.0)})
    ci = pc.interval_pct()
    assert math.isclose(ci.mean, 20.0)
    assert math.isclose(ci.stdev, 10.0)
    half = 4.303 * 10.0 / math.sqrt(3)          # t(0.975, df=2) = 4.303
    assert math.isclose(ci.low, 20.0 - half, abs_tol=1e-2)
    assert math.isclose(ci.high, 20.0 + half, abs_tol=1e-2)
    assert pc.wins == 3


def test_summary_reports_finish_rate_finished_only_and_both_finished_pairs():
    runs = []
    for seed in (17, 19):                  # both arms finish both seeds
        for arm in ("stop_and_wait", "swarmos"):
            runs.append(run_one(_job(arm, seed=seed)))
    s = summarise(runs, "stop_and_wait", 20.0)["overlap_batch/normal"]
    a = s["arms"]["swarmos"]
    assert a["finish_rate"] == 1.0
    assert a["makespan_finished_median"] is not None
    assert s["arms"]["stop_and_wait"]["finish_rate"] == 1.0
    comp = s["comparisons"]["swarmos vs stop_and_wait"]
    assert comp["makespan_s (both finished)"]["n"] == 2
    assert {"makespan_censored_s", "makespan_s (both finished)", "t90_censored_s"} <= set(comp)


def test_instrumentation_does_not_change_the_trace():
    """stop_events / backtracks / t90 are read-only: two runs, same hash,
    and the counters are populated."""
    spec = type(get_scenario("overlap_batch"))(**{**get_scenario("overlap_batch").__dict__,
                                                   "initial_burst": 6, "fleet_size": 4})
    a = SimEngine(spec, seed=13, policy=_make_policy("swarmos", 13))
    b = SimEngine(spec, seed=13, policy=_make_policy("swarmos", 13))
    a.run(1500)
    b.run(1500)
    assert a.trace_hash == b.trace_hash
    k = a.kpis()
    assert k["stop_events"] >= 0 and k["held_work_ticks"] >= k["stop_events"]
    la = k["lookahead"]
    assert la["resolved_conflicts"] + la["open_conflicts"] == la["actual_conflicts"]


def test_comm_holds_zero_on_healthy_radio_positive_in_outage():
    spec = type(get_scenario("rush_50"))(**{**get_scenario("rush_50").__dict__, "fleet_size": 16})
    healthy = SimEngine(spec, seed=11, policy=_make_policy("swarmos", 11))
    healthy.run(400)
    assert healthy.policy.comm_hold_ticks == 0
    outage = SimEngine(spec, seed=11, policy=_make_policy("swarmos", 11))
    outage.run(100)
    outage.inject("LINK_IMPAIR", drop_pct=100.0, latency_ms=0.0, ticks=80)
    outage.run(200)
    assert outage.policy.comm_hold_ticks > 0


def _fake(arm, seed, makespan, cap=3000.0):
    dnf = makespan is None
    return {"scenario": "x", "condition": "normal", "arm": arm, "seed": seed,
            "did_not_finish": dnf, "makespan_s": makespan,
            "makespan_censored_s": cap if dnf else makespan, "t90_censored_s": None,
            "tasks_complete": 1, "collisions": 0, "margin_breaches": 0,
            "safety_verdict": "PASS", "stall_releases": 0, "replans": 0,
            "path_efficiency": None, "avg_wait_s": None, "compute_p95_ms": None,
            "msgs_per_robot_tick": None, "min_separation_m": 1.0, "tasks_per_min": 1.0,
            "deadlock": {"deadlocks_formed": 0, "persistent_deadlocks": 0},
            "lookahead": {"prediction_episodes": 0}}


def test_censored_target_is_not_admissible_when_the_treatment_dnfs_alone():
    """Censoring flatters the arm that fails. A treatment that DNFs on a seed
    the reference finished must never be credited with a censored MET."""
    seeds = range(1, 11)
    runs = [_fake("ref", s, 2000.0, cap=2100.0) for s in seeds]
    runs += [_fake("new", s, None if s == 1 else 500.0, cap=2100.0) for s in seeds]
    block = summarise(runs, "ref", 20.0)["x/normal"]
    c = block["comparisons"]["new vs ref"]["makespan_censored_s"]
    assert c["ci95_low_pct"] >= 20.0                 # the raw CI would say MET ...
    assert c["target_met"] is False and "not_admissible" in c   # ... it is refused
    assert block["dnf_pairs"]["new vs ref"]["treatment_only_dnf_seeds"] == [1]


def test_runner_refuses_when_the_code_identity_does_not_match(tmp_path, capsys):
    from tools.run_experiment import main

    rc = main(["--name", "t", "--scenarios", "overlap_batch", "--arms", "swarmos",
               "--seeds", "1", "--out", str(tmp_path), "--expect-identity", "0" * 64])
    assert rc == 2
    assert "REFUSED" in capsys.readouterr().err
    assert not list(tmp_path.iterdir())              # nothing was run or written
