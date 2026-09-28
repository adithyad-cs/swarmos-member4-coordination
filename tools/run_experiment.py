"""Reproducible SWARMOS experiments: arms x scenarios x seeds (x conditions).

Every run is recorded so a judge can check the numbers are genuine:

  reports/experiments/<UTC>_<name>/
    config.json   git revision, python, full scenario specs, arms, seeds,
                  conditions, the exact command line
    runs.jsonl    one line per run: every reported metric + the trace hash
    summary.json  paired statistics (Student-t 95% CI, app/db/stats.py)
    summary.md    the same, human-readable

Re-run any stored run with tools/replay_check.py <dir>; it must reproduce the
trace hash bit-for-bit.

Batch scenarios are scored on MAKESPAN (time the last task of the fixed batch
completed). A run that hits the scenario cap is reported as did-not-finish and
its makespan is CENSORED at the cap. Censoring UNDERSTATES the true makespan of
the arm that failed to finish, so it FLATTERS whichever arm finishes less. It
cannot manufacture an improvement for the treatment only when the treatment
never fails on a seed the reference finishes; the frozen C2 protocol
(docs/C2_FROZEN_PROTOCOL.md) makes that a condition of claiming C2, and the
finished-only and both-finished statistics are reported beside it. The number
of censored runs per arm is printed next to every result.

Usage:
  PYTHONPATH=. python3 tools/run_experiment.py --name c2 \\
      --scenarios overlap_batch open_floor_batch \\
      --arms stop_and_wait baseline swarmos --reference stop_and_wait
  PYTHONPATH=. python3 tools/run_experiment.py --name comm --comm-sweep \\
      --scenarios rush_50 --fleet 16 --ticks 1200 --arms swarmos swarmos_nofb
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DEFAULT_SEEDS = (11, 13, 17, 19, 23, 29, 31, 37, 41)

# Frozen C2 evaluation seeds (docs/C2_FROZEN_PROTOCOL.md). Chosen by a fixed
# rule BEFORE any run on them: 40 consecutive integers from 900001, a range no
# development run, test or stored experiment has used (tests/test_c2_protocol.py
# checks that). Never tune anything on these seeds.
C2_EVAL_SEEDS = tuple(range(900001, 900041))

# Development seeds for the post-C2 improvement cycle
# (docs/C2_ROOT_CAUSE_ANALYSIS.md, section D). Declared before any fix was
# measured on them; disjoint from C2_EVAL_SEEDS and every earlier seed. Every
# fix in the cycle is judged on this whole block, never on one seed.
DEV_SEEDS = tuple(range(700001, 700021))

# Frozen C2 v2 evaluation seeds (docs/C2_FROZEN_PROTOCOL_V2.md). Fixed by rule
# BEFORE any run on them: the 40 consecutive integers from 800001, a block no
# development run, test or stored experiment has used (checked by
# tests/test_c2_protocol.py). 40 keeps the v2 result comparable with the
# 40-seed v1 evaluation. Never choose, drop, replace or reorder them.
C2V2_EVAL_SEEDS = tuple(range(800001, 800041))

# Frozen C2 v3 evaluation seeds (docs/C2_FROZEN_PROTOCOL_V3.md): the PRODUCT
# default validation. Same rule: 40 consecutive integers from 600001, a block
# never used by any development run, test, earlier evaluation or stored
# experiment (checked by tests/test_c2_protocol.py). Never choose, drop,
# replace or reorder them.
C2V3_EVAL_SEEDS = tuple(range(600001, 600041))

# Advanced-intelligence development seeds (ablation, variant sweeps) and the
# Edge-AI dataset blocks (train / validation / test, tools/edge_ai_dataset.py).
ADV_DEV_SEEDS = tuple(range(1000001, 1000041))

# Frozen ADVANCED-INTELLIGENCE evaluation seeds
# (docs/ADVANCED_FROZEN_PROTOCOL_V1.md). Same rule: 40 consecutive integers
# from 1400001, never used by any development run, dataset split, test or
# stored experiment (checked by tests/test_advanced_protocol.py). Never
# choose, drop, replace or reorder them.
ADV_EVAL_SEEDS = tuple(range(1400001, 1400041))

# Arm name -> (description, factory spec). Factories are rebuilt inside each
# worker process from this table, so the record fully determines the policy.
ARMS = {
    "stop_and_wait": "Traditional stop-and-wait (TextbookStopAndWaitPolicy, "
                     "STUCK_TICKS=30): the SIH C2 comparison arm",
    "baseline": "Stop-and-wait TUNED (STUCK_TICKS=8): the stronger honesty check",
    "swarmos": "SWARMOS product policy (graded ladder + Simplex kernel + "
               "perception fallback)",
    "swarmos_lookahead": "SWARMOS + observe-only predictive lookahead (H=15); "
                         "identical motion, adds prediction scoring",
    "swarmos_traffic": "SWARMOS + one-way lanes on single-file segments",
    "swarmos_nofb": "SWARMOS WITHOUT the perception fallback (comm-safety control)",
    "swarmos_mhb": "SWARMOS + mutual-hold break (ladder only; kernel unchanged)",
    "swarmos_mhb_sep": "SWARMOS + mutual-hold break + separating-motion exemption "
                       "(kernel change, under evaluation)",
    "noop": "No coordination at all: negative control for the safety monitor",
}

# Communication conditions: name -> list of (tick, fault, params).
COMM_CONDITIONS = {
    "normal": [],
    "loss10": [(100, "LINK_IMPAIR", {"drop_pct": 10.0, "latency_ms": 0.0})],
    "loss30": [(100, "LINK_IMPAIR", {"drop_pct": 30.0, "latency_ms": 0.0})],
    "latency100ms": [(100, "LINK_IMPAIR", {"drop_pct": 0.0, "latency_ms": 100.0})],
    "latency500ms": [(100, "LINK_IMPAIR", {"drop_pct": 0.0, "latency_ms": 500.0})],
    "outage3s": [(300, "LINK_IMPAIR", {"drop_pct": 100.0, "latency_ms": 0.0,
                                       "ticks": 30})],
    "outage6s": [(300, "LINK_IMPAIR", {"drop_pct": 100.0, "latency_ms": 0.0,
                                       "ticks": 60})],
    "blackout_one": [(300, "COMM_BLACKOUT", {})],
    "partition_east": [(100, "ZONE_PARTITION", {"zone": "EAST", "ticks": 300})],
}


# Improvement-cycle fixes (docs/C2_ROOT_CAUSE_ANALYSIS.md, section C). An arm
# "<base>+F1+F3" is the base arm with those fixes switched on; the base arms
# themselves are unchanged. Policy-level fixes are applied in make_policy,
# engine-level ones in run_one.
FIXES = {
    "F1": "polyline sweep in the safety check (both arms)",
    "F3": "leader keeps right of way in the contest band (SWARMOS ladder)",
    "F5": "standoff breaker: deterministic loser replans around the peer (SWARMOS)",
    "F6": "stall release does not hand the task back to the same robot for 30 s (engine, all arms)",
    "EAI": "EDGE_AI_PREDICTOR: runtime Edge-AI conflict prediction (advisory, SWARMOS)",
    "PC": "PREDICTIVE_COORDINATION: prediction-driven PRE-HOLD (SWARMOS ladder)",
    "AU": "LIVE_DISTRIBUTED_AUCTION: radio-exchanged task bids + WMS lease ledger (SWARMOS)",
}
F6_COOLDOWN_TICKS = 300


def split_arm(arm: str) -> tuple[str, list[str]]:
    base, *fixes = arm.split("+")
    if base not in ARMS:
        raise ValueError(f"unknown arm {base!r}")
    bad = [f for f in fixes if f not in FIXES]
    if bad:
        raise ValueError(f"unknown fix(es) {bad} in {arm!r}")
    return base, fixes


def make_policy(arm: str, seed: int):
    base, fixes = split_arm(arm)
    policy = _make_base_policy(base, seed)
    if "F1" in fixes:
        if hasattr(policy, "polyline_sweep"):
            policy.polyline_sweep = True
        else:
            policy.POLYLINE_SWEEP = True
    if "F3" in fixes:
        if not hasattr(policy, "leader_rule"):
            raise ValueError("F3 is a SWARMOS ladder fix")
        policy.leader_rule = True
    if "F5" in fixes:
        if not hasattr(policy, "standoff_breaker"):
            raise ValueError("F5 is a SWARMOS recovery fix")
        policy.standoff_breaker = True
    adv = {k: True for f, k in (("EAI", "EDGE_AI_PREDICTOR"), ("PC", "PREDICTIVE_COORDINATION"),
                                ("AU", "LIVE_DISTRIBUTED_AUCTION")) if f in fixes}
    if adv:
        if not hasattr(policy, "live_auction"):
            raise ValueError("EAI/PC/AU are SWARMOS features")
        from app.product import apply_advanced

        apply_advanced(policy, {k: adv.get(k, False) for k in
                                ("EDGE_AI_PREDICTOR", "PREDICTIVE_COORDINATION",
                                 "LIVE_DISTRIBUTED_AUCTION")})
    return policy


def arm_config(arm: str) -> dict:
    """The configuration an arm ACTUALLY runs with, read back from the built
    policy and engine settings rather than restated by hand. Recorded in
    config.json so the frozen record shows every enabled flag and threshold."""
    policy = make_policy(arm, 0)
    base, fixes = split_arm(arm)
    keys = ("name", "polyline_sweep", "leader_rule", "standoff_breaker",
            "separating_exemption", "mutual_hold_break", "traffic_rules_enabled",
            "perception_fallback", "lookahead_h", "integrity_enabled",
            "monitor_enabled", "POLYLINE_SWEEP", "STUCK_TICKS",
            "SAFE_SEPARATION_M", "MAX_STEP_M", "edge_ai", "predictive_coordination",
            "live_auction", "edge_status")
    out = {"base": base, "fixes": fixes, "policy_class": type(policy).__name__,
           "engine_release_cooldown_ticks": (
               F6_COOLDOWN_TICKS if "F6" in fixes
               else int(getattr(policy, "release_cooldown_ticks", 0) or 0))}
    for k in keys:
        if hasattr(policy, k):
            v = getattr(policy, k)
            out[k] = v if isinstance(v, (bool, int, float, str)) else str(v)
    advisor = getattr(policy, "edge_advisor", None)
    out["edge_model"] = advisor.describe() if advisor is not None else None
    try:
        from app.coordination import swarm_policy as sp
        from app.sim import engine as en
        out["constants"] = {
            "HARD_STOP_M": sp.HARD_STOP_M, "CONFLICT_M": sp.CONFLICT_M,
            "COMMIT_TICKS": sp.COMMIT_TICKS, "YIELD_PATIENCE": sp.YIELD_PATIENCE,
            "MONITOR_STUCK_TICKS": sp.MONITOR_STUCK_TICKS,
            "STANDOFF_TICKS": sp.STANDOFF_TICKS,
            "STANDOFF_SWAP_TICKS": sp.STANDOFF_SWAP_TICKS,
            "STANDOFF_AVOID_M": sp.STANDOFF_AVOID_M,
            "STALL_RELEASE_TICKS": en.STALL_RELEASE_TICKS,
            "WIP_FRACTION": en.WIP_FRACTION,
            "MARGIN_BREACH_M": en.MARGIN_BREACH_M,
        }
    except Exception as exc:                              # pragma: no cover
        out["constants"] = f"unavailable: {exc}"
    return out


def _make_base_policy(arm: str, seed: int):
    from app.api.runner import _make_policy
    from app.coordination.swarm_policy import SwarmPolicy
    from app.sim.policy import NoOpPolicy

    if arm in ("stop_and_wait", "baseline", "swarmos"):
        return _make_policy(arm, seed)
    if arm == "swarmos_lookahead":
        return SwarmPolicy(perception_fallback=True, lookahead_h=15)
    if arm == "swarmos_traffic":
        return SwarmPolicy(perception_fallback=True, traffic_rules=True)
    if arm == "swarmos_nofb":
        return SwarmPolicy(perception_fallback=False)
    if arm == "swarmos_mhb":
        return SwarmPolicy(perception_fallback=True, lookahead_h=15,
                           mutual_hold_break=True)
    if arm == "swarmos_mhb_sep":
        return SwarmPolicy(perception_fallback=True, lookahead_h=15,
                           mutual_hold_break=True, separating_exemption=True)
    if arm == "noop":
        return NoOpPolicy()
    raise ValueError(f"unknown arm {arm!r}")


def build_scenario(name: str, overrides: dict):
    from app.sim.scenarios import get_scenario

    spec = get_scenario(name)
    if overrides:
        spec = type(spec)(**{**spec.__dict__, **overrides})
    return spec


def run_one(job: dict) -> dict:
    """Execute one (scenario, arm, seed, condition) run. Runs in a worker."""
    from app.sim.engine import SimEngine

    spec = build_scenario(job["scenario"], job["overrides"])
    policy = make_policy(job["arm"], job["seed"])
    eng = SimEngine(spec, seed=job["seed"], policy=policy, label=job["arm"])
    if "F6" in split_arm(job["arm"])[1]:
        eng.release_cooldown_ticks = F6_COOLDOWN_TICKS
    injections = [tuple(x) for x in job["injections"]]
    started = time.monotonic()
    limit = job.get("ticks")
    while not eng.finished and (limit is None or eng.clock.tick < limit):
        for at, fault, params in injections:
            if eng.clock.tick == at:
                eng.inject(fault, **params)
        eng.step()
    wall = time.monotonic() - started
    k = eng.kpis()
    cap_s = spec.duration_s
    makespan = k["makespan_s"]
    stats = eng.policy.stats() if hasattr(eng.policy, "stats") else {}
    radio = stats.get("radio", {}) if isinstance(stats, dict) else {}
    return {
        **{key: job[key] for key in ("scenario", "arm", "seed", "condition")},
        "ticks": eng.clock.tick,
        "sim_time_s": k["sim_time_s"],
        "trace_hash": eng.trace_hash,
        "tasks_total": k["tasks_total"],
        "tasks_complete": k["tasks_complete"],
        "makespan_s": makespan,
        "did_not_finish": k["did_not_finish"],
        "makespan_censored_s": (makespan if makespan is not None
                                else (cap_s if spec.batch else None)),
        "total_completion_s": k["total_completion_s"],
        "avg_completion_s": k["avg_completion_s"],
        "avg_wait_s": k["avg_wait_s"],
        "tasks_per_min": k["tasks_per_min"],
        "replans": k["replans"],
        "stall_releases": k["stall_releases"],
        "cooldown_skips": k.get("cooldown_skips"),
        "standoff_breaks": getattr(eng.policy, "standoff_breaks", None),
        "leader_grants": getattr(eng.policy, "leader_grants", None),
        "livelock_episodes": k["livelock_episodes"],
        "livelock_ticks": k["livelock_ticks"],
        "path_efficiency": k["path_efficiency"],
        "collisions": k["collisions"],
        "margin_breaches": k["margin_breaches"],
        "floor_entries": k["safety"]["margin_breaches"],
        "floor_pair_ticks": k["safety"].get("floor_pair_ticks"),
        "longest_floor_episode_ticks": k["safety"].get("longest_floor_episode_ticks"),
        "frozen_pairs": k["safety"].get("frozen_pairs"),
        "recovery_actions": (k["stall_releases"] + k["verdicts"].get("REROUTE", 0)),
        "min_separation_m": k["min_separation_m"],
        "safety_verdict": k["safety"]["verdict"],
        "invariants": k["safety"]["counts"],
        "deadlock": k["deadlock"],
        "lookahead": k["lookahead"],
        "compute_p95_ms": k["compute"].get("p95_ms"),
        "msgs_per_robot_tick": stats.get("msgs_per_robot_tick"),
        "radio_delivered": radio.get("delivered"),
        "radio_dropped": radio.get("dropped"),
        "sensed_blocks": (stats.get("perception_fallback") or {}).get("sensed_blocks"),
        "t90_s": k["t90_s"],
        "t90_censored_s": (k["t90_s"] if k["t90_s"] is not None
                           else (cap_s if spec.batch else None)),
        "verdicts": k["verdicts"],
        "wait_count": k["verdicts"].get("WAIT", 0),
        "yield_count": k["verdicts"].get("YIELD", 0),
        "reroute_count": k["verdicts"].get("REROUTE", 0),
        "stop_events": k["stop_events"],
        "held_work_ticks": k["held_work_ticks"],
        "backtracks_dropped": k["backtracks_dropped"],
        "conflicts": k["lookahead"]["actual_conflicts"],
        "resolved_conflicts": k["lookahead"]["resolved_conflicts"],
        "predicted_conflicts": k["lookahead"]["prediction_episodes"],
        "comm_hold_ticks": (stats.get("perception_fallback") or {}).get("comm_hold_ticks"),
        "sovereign_ticks": (stats.get("sovereign") or {}).get("ticks"),
        "invariant_failures": sum(k["safety"]["counts"].values()),
        "decision_oscillations": k.get("decision_oscillations"),
        # advanced intelligence (None when the feature is off)
        "allocation": k.get("allocation"),
        "edge_ai": _edge_block(k),
        "proactive": ((k.get("advanced") or {}).get("proactive")
                      if (k.get("advanced") or {}).get("proactive", {}).get("enabled") else None),
        "edge_mean_inference_us": ((k.get("advanced") or {}).get("edge_ai") or {}).get("mean_inference_us"),
        "decision_records": k["decisions"],
        "wall_s": round(wall, 2),
    }


def _edge_block(k: dict):
    """Edge-AI counters WITHOUT wall-clock timing (those vary between
    machines and are reported separately, never replay-checked)."""
    e = (k.get("advanced") or {}).get("edge_ai") or {}
    if not e.get("enabled"):
        return None
    return {x: e.get(x) for x in ("status", "calls", "positives", "errors",
                                  "prediction_reversals")} | {
        "model_sha256": (e.get("model") or {}).get("sha256")}


def _git_rev() -> str:
    try:
        rev = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                      text=True).strip()
        dirty = subprocess.call(["git", "diff", "--quiet"], cwd=ROOT) != 0
        return rev + ("+uncommitted-changes" if dirty else "")
    except Exception:                                     # pragma: no cover
        return "unknown"


# Files whose content determines a run's behaviour. The code identity is a
# sha256 over (path, content-sha256) of every such file, tracked OR untracked,
# so it identifies the exact code even when nothing has been committed.
IDENTITY_PATHS = ("app", "tools", "pyproject.toml")


def code_identity() -> dict:
    import hashlib

    try:
        out = subprocess.check_output(
            ["git", "ls-files", "-co", "--exclude-standard", "--", *IDENTITY_PATHS],
            cwd=ROOT, text=True)
        files = sorted({f for f in out.splitlines() if f.endswith((".py", ".toml"))})
    except Exception:
        # Not a git checkout (e.g. an isolated development copy): walk the
        # same paths so the identity still names the exact code.
        files = []
        for base in IDENTITY_PATHS:
            full = os.path.join(ROOT, base)
            if os.path.isfile(full):
                files.append(base)
                continue
            for d, _dirs, names in os.walk(full):
                if "__pycache__" in d:
                    continue
                files += [os.path.relpath(os.path.join(d, n), ROOT) for n in names
                          if n.endswith((".py", ".toml"))]
        files = sorted(set(files))
    outer = hashlib.sha256()
    for rel in files:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        outer.update(f"{rel}\0{digest}\n".encode())
    return {"sha256": outer.hexdigest(), "files": len(files),
            "paths": list(IDENTITY_PATHS)}


def summarise(runs: list[dict], reference: str, target_pct: float) -> dict:
    from app.db.stats import paired

    out: dict = {}
    for scenario in sorted({r["scenario"] for r in runs}):
        for cond in sorted({r["condition"] for r in runs if r["scenario"] == scenario}):
            rows = [r for r in runs if r["scenario"] == scenario and r["condition"] == cond]
            key = f"{scenario}/{cond}"
            arms = sorted({r["arm"] for r in rows})
            per_arm = {}
            for arm in arms:
                rs = [r for r in rows if r["arm"] == arm]
                done = [r["tasks_complete"] for r in rs]
                per_arm[arm] = {
                    "runs": len(rs),
                    "did_not_finish": sum(1 for r in rs if r["did_not_finish"]),
                    "collisions_total": sum(r["collisions"] for r in rs),
                    "margin_breaches_total": sum(r["margin_breaches"] for r in rs),
                    "safety_fail_runs": sum(1 for r in rs if r["safety_verdict"] != "PASS"),
                    "tasks_complete_mean": round(sum(done) / len(done), 2) if done else None,
                    "makespan_censored_mean": _mean([r["makespan_censored_s"] for r in rs]),
                    "stall_releases_mean": _mean([r["stall_releases"] for r in rs]),
                    "livelock_episodes_mean": _mean([r.get("livelock_episodes") for r in rs]),
                    "deadlocks_formed_mean": _mean([r["deadlock"]["deadlocks_formed"] for r in rs]),
                    "persistent_deadlocks_mean": _mean(
                        [r["deadlock"]["persistent_deadlocks"] for r in rs]),
                    "replans_mean": _mean([r["replans"] for r in rs]),
                    "path_efficiency_mean": _mean([r["path_efficiency"] for r in rs]),
                    "avg_wait_s_mean": _mean([r["avg_wait_s"] for r in rs]),
                    "compute_p95_ms_mean": _mean([r["compute_p95_ms"] for r in rs]),
                    "msgs_per_robot_tick_mean": _mean([r["msgs_per_robot_tick"] for r in rs]),
                    "min_separation_m_min": _min([r["min_separation_m"] for r in rs]),
                    "finish_rate": round(sum(1 for r in rs if not r["did_not_finish"]) / len(rs), 4)
                    if rs else None,
                    "makespan_finished_mean": _mean([r["makespan_s"] for r in rs]),
                    "makespan_finished_median": _median([r["makespan_s"] for r in rs]),
                    "t90_censored_mean": _mean([r.get("t90_censored_s") for r in rs]),
                    "throughput_tpm_mean": _mean([r["tasks_per_min"] for r in rs]),
                    "wait_count_mean": _mean([r.get("wait_count") for r in rs]),
                    "yield_count_mean": _mean([r.get("yield_count") for r in rs]),
                    "reroute_count_mean": _mean([r.get("reroute_count") for r in rs]),
                    "stop_events_mean": _mean([r.get("stop_events") for r in rs]),
                    "held_work_ticks_mean": _mean([r.get("held_work_ticks") for r in rs]),
                    "backtracks_mean": _mean([r.get("backtracks_dropped") for r in rs]),
                    "conflicts_mean": _mean([r.get("conflicts") for r in rs]),
                    "resolved_conflicts_mean": _mean([r.get("resolved_conflicts") for r in rs]),
                    "predicted_conflicts_mean": _mean([r.get("predicted_conflicts") for r in rs]),
                    "comm_hold_ticks_mean": _mean([r.get("comm_hold_ticks") for r in rs]),
                    "invariant_failures_total": sum(r.get("invariant_failures") or 0 for r in rs),
                    "floor_entries_total": sum(r.get("floor_entries") or 0 for r in rs),
                    "floor_pair_ticks_mean": _mean([r.get("floor_pair_ticks") for r in rs]),
                    "frozen_pairs_total": sum(r.get("frozen_pairs") or 0 for r in rs),
                    "runs_with_frozen_pair": sum(1 for r in rs if (r.get("frozen_pairs") or 0) > 0),
                    "recovery_actions_mean": _mean([r.get("recovery_actions") for r in rs]),
                }
                la = [r["lookahead"] for r in rs if r["lookahead"]["prediction_episodes"]]
                if la:
                    tp = sum(x["true_positives"] for x in la)
                    fp = sum(x["false_positives"] for x in la)
                    fn = sum(x["false_negatives"] for x in la)
                    leads = [x["mean_lead_ticks"] for x in la if x["mean_lead_ticks"] is not None]
                    per_arm[arm]["lookahead"] = {
                        "precision": round(tp / (tp + fp), 4) if tp + fp else None,
                        "recall": round(tp / (tp + fn), 4) if tp + fn else None,
                        "mean_lead_ticks": _mean(leads),
                        "tp": tp, "fp": fp, "fn": fn,
                    }
            comparisons = {}
            dnf_pairs = {}
            ref_rows = {r["seed"]: r for r in rows if r["arm"] == reference}
            for arm in arms:
                if arm == reference or not ref_rows:
                    continue
                arm_rows = {r["seed"]: r for r in rows if r["arm"] == arm}
                seeds = sorted(set(ref_rows) & set(arm_rows))
                comp = {}
                # Censoring flatters the arm that fails to finish, so a censored
                # improvement is only admissible when the treatment never fails
                # a seed the reference finished (docs/C2_FROZEN_PROTOCOL.md).
                treat_only_dnf = [s for s in seeds if arm_rows[s]["did_not_finish"]
                                  and not ref_rows[s]["did_not_finish"]]
                ref_only_dnf = [s for s in seeds if ref_rows[s]["did_not_finish"]
                                and not arm_rows[s]["did_not_finish"]]
                # makespan_s is None for a DNF run, so its pairs are exactly the
                # seeds on which BOTH arms finished - the uncensored view.
                metric_pairs = {
                    "makespan_censored_s": (True, "makespan_censored_s"),
                    "makespan_s (both finished)": (True, "makespan_s"),
                    "t90_censored_s": (True, "t90_censored_s"),
                    "tasks_complete": (False, "tasks_complete"),
                }
                for label, (lower, field) in metric_pairs.items():
                    data = {s: (float(ref_rows[s][field]), float(arm_rows[s][field]))
                            for s in seeds
                            if ref_rows[s].get(field) is not None
                            and arm_rows[s].get(field) is not None}
                    if len(data) < 2:
                        continue
                    pc = paired(label, data, lower_is_better=lower, target_pct=target_pct)
                    ci = pc.interval_pct()
                    comp[label] = {
                        "n": ci.n,
                        "mean_improvement_pct": _r(ci.mean),
                        "ci95_low_pct": _r(ci.low),
                        "ci95_high_pct": _r(ci.high),
                        "wins": pc.wins,
                        "target_pct": target_pct,
                        "target_met": bool(ci.low >= target_pct) if ci.n >= 2 else False,
                    }
                    if field == "makespan_censored_s" and treat_only_dnf:
                        comp[label]["target_met"] = False
                        comp[label]["not_admissible"] = (
                            f"treatment did not finish on {len(treat_only_dnf)} seed(s) "
                            "the reference finished; censoring would flatter it")
                comparisons[f"{arm} vs {reference}"] = comp
                dnf_pairs[f"{arm} vs {reference}"] = {
                    "treatment_only_dnf_seeds": treat_only_dnf,
                    "reference_only_dnf_seeds": ref_only_dnf,
                }
            out[key] = {"arms": per_arm, "comparisons": comparisons, "dnf_pairs": dnf_pairs}
    return out


def _r(x):
    try:
        import math
        return round(x, 2) if math.isfinite(x) else None
    except TypeError:
        return None


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 4) if xs else None


def _median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else round((xs[m - 1] + xs[m]) / 2.0, 4)


def _min(xs):
    xs = [x for x in xs if x is not None]
    return min(xs) if xs else None


def render_md(name: str, config: dict, summary: dict) -> str:
    lines = [f"# Experiment `{name}`", "",
             f"- git: `{config['git']}`",
             f"- code identity (sha256): `{(config.get('code_identity') or {}).get('sha256')}`",
             f"- created: {config['created_utc']}",
             f"- seeds: {config['seeds']}", f"- reference arm: `{config['reference']}`",
             f"- command: `{config['command']}`", "",
             "Makespan for runs that did not finish is CENSORED at the scenario "
             "cap. That understates the failing arm's true time, so it flatters "
             "the arm that finishes less; a censored target is marked MET only "
             "when the treatment never failed a seed the reference finished.", ""]
    for key, block in summary.items():
        lines += [f"## {key}", "",
                  "| arm | DNF | tasks done (mean) | makespan censored (mean s) | "
                  "collisions | margin breaches | safety FAIL runs | wait-cycles (mean) "
                  "| persistent deadlocks >=1 s (mean) | stall releases (mean) "
                  "| livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for arm, a in block["arms"].items():
            lines.append(
                f"| {arm} | {a['did_not_finish']}/{a['runs']} | {a['tasks_complete_mean']} "
                f"| {a['makespan_censored_mean']} | {a['collisions_total']} "
                f"| {a['margin_breaches_total']} | {a['safety_fail_runs']} "
                f"| {a['deadlocks_formed_mean']} | {a['persistent_deadlocks_mean']} "
                f"| {a['stall_releases_mean']} | {a['livelock_episodes_mean']} "
                f"| {a['replans_mean']} | {a['path_efficiency_mean']} "
                f"| {a['min_separation_m_min']} |")
        lines += ["", "| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) "
                  "| throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks "
                  "| conflicts / resolved | predicted | comm holds | invariant failures |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for arm, a in block["arms"].items():
            lines.append(
                f"| {arm} | {a['finish_rate']} | {a['makespan_finished_mean']} / "
                f"{a['makespan_finished_median']} | {a['t90_censored_mean']} "
                f"| {a['throughput_tpm_mean']} | {a['wait_count_mean']} | {a['yield_count_mean']} "
                f"| {a['reroute_count_mean']} | {a['stop_events_mean']} | {a['backtracks_mean']} "
                f"| {a['conflicts_mean']} / {a['resolved_conflicts_mean']} "
                f"| {a['predicted_conflicts_mean']} | {a['comm_hold_ticks_mean']} "
                f"| {a['invariant_failures_total']} |")
        lines += ["", "| arm | floor entries (total) | floor pair-ticks (mean) | frozen pairs (total) "
                  "| runs with a frozen pair | recovery actions (mean: stall releases + REROUTE) |",
                  "|---|---|---|---|---|---|"]
        for arm, a in block["arms"].items():
            lines.append(
                f"| {arm} | {a.get('floor_entries_total')} | {a.get('floor_pair_ticks_mean')} "
                f"| {a.get('frozen_pairs_total')} | {a.get('runs_with_frozen_pair')} "
                f"| {a.get('recovery_actions_mean')} |")
        la = {arm: a["lookahead"] for arm, a in block["arms"].items() if "lookahead" in a}
        if la:
            lines += ["", "Lookahead (observe-only scoring):", ""]
            for arm, x in la.items():
                lines.append(f"- `{arm}`: precision {x['precision']}, recall {x['recall']}, "
                             f"mean lead {x['mean_lead_ticks']} ticks "
                             f"(TP {x['tp']}, FP {x['fp']}, FN {x['fn']})")
        if block["comparisons"]:
            lines += ["", "| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |",
                      "|---|---|---|---|---|---|---|"]
            for cname, comp in block["comparisons"].items():
                for metric, c in comp.items():
                    lines.append(
                        f"| {cname} | {metric} | {c['n']} | {c['mean_improvement_pct']} "
                        f"| [{c['ci95_low_pct']}, {c['ci95_high_pct']}] | {c['wins']}/{c['n']} "
                        f"| {'MET' if c['target_met'] else 'not met'} |")
            for cname, d in block.get("dnf_pairs", {}).items():
                lines.append("")
                lines.append(f"- `{cname}`: treatment-only DNF seeds "
                             f"{d['treatment_only_dnf_seeds'] or 'none'}; reference-only DNF "
                             f"seeds {d['reference_only_dnf_seeds'] or 'none'}")
        lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--name", required=True)
    ap.add_argument("--scenarios", nargs="+", required=True)
    ap.add_argument("--arms", nargs="+", required=True,
                    help=f"base arms {sorted(ARMS)}, optionally +FIX for FIX in {sorted(FIXES)}")
    ap.add_argument("--reference", default=None)
    ap.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    ap.add_argument("--fleet", type=int, default=None)
    ap.add_argument("--burst", type=int, default=None)
    ap.add_argument("--cap-s", type=float, default=None)
    ap.add_argument("--ticks", type=int, default=None,
                    help="hard tick limit (for non-batch scenarios)")
    ap.add_argument("--comm-sweep", action="store_true")
    ap.add_argument("--conditions", nargs="+", default=None)
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--target-pct", type=float, default=20.0)
    ap.add_argument("--out", default=os.path.join(ROOT, "reports", "experiments"))
    ap.add_argument("--expect-identity", default=None,
                    help="refuse to run unless the code identity sha256 equals this "
                         "(the frozen C2 protocol passes the frozen value)")
    args = ap.parse_args(argv)

    identity = code_identity()
    if args.expect_identity and identity["sha256"] != args.expect_identity:
        print(f"REFUSED: code identity {identity['sha256']} != expected "
              f"{args.expect_identity}; the code changed since the protocol was frozen.",
              file=sys.stderr)
        return 2

    overrides = {}
    if args.fleet is not None:
        overrides["fleet_size"] = args.fleet
    if args.burst is not None:
        overrides["initial_burst"] = args.burst
    if args.cap_s is not None:
        overrides["duration_s"] = args.cap_s

    if args.comm_sweep:
        conditions = args.conditions or list(COMM_CONDITIONS)
    else:
        conditions = args.conditions or ["normal"]
    for a in args.arms:
        split_arm(a)
    reference = args.reference or args.arms[0]

    jobs = [
        {"scenario": s, "arm": a, "seed": seed, "condition": c,
         "overrides": overrides, "injections": COMM_CONDITIONS[c],
         "ticks": args.ticks}
        for s in args.scenarios for c in conditions
        for a in args.arms for seed in args.seeds
    ]

    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    outdir = os.path.join(args.out, f"{stamp}_{args.name}")
    os.makedirs(outdir, exist_ok=True)
    config = {
        "name": args.name,
        "created_utc": stamp,
        "git": _git_rev(),
        "code_identity": identity,
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "workers": args.workers,
        "arm_configs": {a: arm_config(a) for a in args.arms},
        "command": "PYTHONPATH=. python3 tools/run_experiment.py " + " ".join(
            sys.argv[1:] if argv is None else argv),
        "scenarios": {s: build_scenario(s, overrides).as_dict() for s in args.scenarios},
        "overrides": overrides,
        "arms": {a: ARMS[split_arm(a)[0]] + "".join(
            f" | {f}: {FIXES[f]}" for f in split_arm(a)[1]) for a in args.arms},
        "reference": reference,
        "seeds": args.seeds,
        "conditions": {c: COMM_CONDITIONS[c] for c in conditions},
        "tick_limit": args.ticks,
        "target_pct": args.target_pct,
    }
    with open(os.path.join(outdir, "config.json"), "w") as fh:
        json.dump(config, fh, indent=2, sort_keys=True)

    print(f"{len(jobs)} runs -> {outdir}", flush=True)
    runs: list[dict] = []
    with ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool, \
            open(os.path.join(outdir, "runs.jsonl"), "w") as fh:
        for rec in pool.map(run_one, jobs):
            runs.append(rec)
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
            fh.flush()
            print(f"  {rec['scenario']:18s} {rec['condition']:14s} {rec['arm']:18s} "
                  f"seed={rec['seed']:>3} done={rec['tasks_complete']}/{rec['tasks_total']} "
                  f"makespan={rec['makespan_s']} col={rec['collisions']} "
                  f"({rec['wall_s']}s)", flush=True)

    summary = summarise(runs, reference, args.target_pct)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    md = render_md(args.name, config, summary)
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(md)
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
