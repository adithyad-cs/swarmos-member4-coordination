"""Re-run stored experiment runs and verify they reproduce bit-for-bit.

  PYTHONPATH=. python3 tools/replay_check.py reports/experiments/<dir> [--all | --n K]

Reads config.json and runs.jsonl, rebuilds each selected run from the recorded
scenario overrides, arm, seed and communication condition, and checks that the
trace hash and the headline metrics are identical. Exit status 1 on any
mismatch. This is the check a judge can run to confirm the published numbers
come from the code, not from a spreadsheet.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.run_experiment import arm_config, code_identity, run_one  # noqa: E402

CHECKED = ("trace_hash", "tasks_complete", "makespan_s", "collisions",
           "margin_breaches", "min_separation_m", "t90_s", "livelock_episodes")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--n", type=int, default=2, help="runs to replay (spread evenly)")
    ap.add_argument("--workers", type=int, default=1,
                    help="parallel replays; runs are deterministic, so this changes "
                         "wall time only")
    ap.add_argument("--require-identity", action="store_true",
                    help="fail unless the current code identity equals the recorded one")
    args = ap.parse_args(argv)

    with open(os.path.join(args.directory, "config.json")) as fh:
        config = json.load(fh)
    with open(os.path.join(args.directory, "runs.jsonl")) as fh:
        runs = [json.loads(line) for line in fh if line.strip()]
    if not runs:
        print("no runs recorded")
        return 1
    recorded = (config.get("code_identity") or {}).get("sha256")
    current = code_identity()["sha256"]
    if recorded is None:
        print("code identity: not recorded (experiment predates identity hashing)")
    elif recorded == current:
        print(f"code identity: MATCH {current}")
    else:
        print(f"code identity: DIFFERENT (recorded {recorded}, current {current}); "
              "a trace mismatch then means the code changed, not that replay is broken")
        if args.require_identity:
            return 1
    recorded_arms = config.get("arm_configs") or {}
    drift = [a for a, c in recorded_arms.items() if arm_config(a) != c]
    if recorded_arms:
        print("arm configs: " + ("MATCH" if not drift else f"DIFFERENT for {drift}"))
        if drift and args.require_identity:
            return 1
    if args.all:
        chosen = runs
    else:
        step = max(1, len(runs) // max(1, args.n))
        chosen = runs[::step][: args.n]

    jobs = [{
        "scenario": rec["scenario"], "arm": rec["arm"], "seed": rec["seed"],
        "condition": rec["condition"], "overrides": config["overrides"],
        "injections": config["conditions"][rec["condition"]],
        "ticks": config.get("tick_limit"),
    } for rec in chosen]
    if args.workers > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(run_one, jobs))
    else:
        results = [run_one(j) for j in jobs]

    bad = 0
    for rec, again in zip(chosen, results):
        diff = {k: (rec[k], again[k]) for k in CHECKED
                if k in rec and rec[k] != again[k]}
        status = "OK " if not diff else "MISMATCH"
        print(f"{status} {rec['scenario']} {rec['condition']} {rec['arm']} "
              f"seed={rec['seed']} hash={again['trace_hash'][:16]} {diff or ''}")
        bad += bool(diff)
    print(f"{len(chosen) - bad}/{len(chosen)} reproduced exactly")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
