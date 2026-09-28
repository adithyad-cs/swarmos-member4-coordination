"""Build the Edge-AI conflict-prediction dataset from real simulation runs.

  PYTHONPATH=. python3 tools/edge_ai_dataset.py --out reports/advanced_v1/dataset

Seeds are split BY RUN, never by tick: every row of a run belongs to exactly
one split. The blocks below were checked unused anywhere in the repository
before this tool was written (reports/advanced_v1/SEEDS.md).

For each sampled tick, every robot computes app/coordination/edge_features
.pair_features for every FRESH peer in its own inbox (exactly what it could
do at runtime). The label for horizon H is whether the TRUE pair distance
drops below CONFLICT_M (0.97 m) at any of the next H ticks. Labels for
several candidate horizons are stored so the horizon can be chosen on the
validation split only.

Data is generated with the V0 product policy (all advanced flags OFF), so
the model learns the world it will be deployed into.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

TRAIN_SEEDS = tuple(range(1100001, 1100031))
VALIDATION_SEEDS = tuple(range(1200001, 1200011))
TEST_SEEDS = tuple(range(1300001, 1300011))
SCENARIOS = {                      # name -> overrides
    "overlap_batch": {},
    "open_floor_batch": {},
    "rush_50": {"fleet_size": 16},
}
HORIZONS = (10, 15, 25)
TICK_CAP = 4000
SAMPLE_EVERY = 4
DATASET_VERSION = "edge-conflict-ds-v1"


def collect(job: dict) -> dict:
    from app.coordination.edge_features import FEATURE_NAMES, pair_features
    from app.coordination.swarm_policy import CONFLICT_M
    from app.product import make_swarmos_policy
    from app.sim.engine import SimEngine
    from app.sim.scenarios import get_scenario

    spec = get_scenario(job["scenario"])
    if job["overrides"]:
        spec = type(spec)(**{**spec.__dict__, **job["overrides"]})
    policy = make_swarmos_policy()
    eng = SimEngine(spec, seed=job["seed"], policy=policy, label="dataset")
    hmax = max(HORIZONS)
    positions: list[dict] = []           # arbitrate tick -> {rid: (x, y)}
    samples: list[tuple] = []
    orig = policy.arbitrate

    def hooked(tick, t, states):
        verdicts = orig(tick, t, states)
        positions.append({rid: (r.x, r.y) for rid, r in eng.robots.items()})
        if tick % SAMPLE_EVERY:
            return verdicts
        for rid in sorted(states):
            me = states[rid]
            fresh = policy._fresh(policy._views.get(rid, {}))
            pos = [(v.state.position.x, v.state.position.y) for p, v in fresh.items() if p != rid]
            for pid in sorted(fresh):
                if pid == rid:
                    continue
                f = pair_features(me, fresh[pid], now_tick=tick, inbox_positions=pos,
                                  my_yield_streak=policy._yield_streak.get(rid, 0),
                                  warehouse=policy._map, horizon=15, conflict_m=CONFLICT_M)
                if f is not None:
                    samples.append((len(positions) - 1, rid, pid, f))
        return verdicts

    policy.arbitrate = hooked
    while not eng.finished and eng.clock.tick < TICK_CAP:
        eng.step()
    rows = []
    for idx, rid, pid, f in samples:
        if idx + hmax >= len(positions):
            continue                     # label window runs past the run end
        labels = {}
        first = None
        for k in range(1, hmax + 1):
            a, b = positions[idx + k][rid], positions[idx + k][pid]
            if math.dist(a, b) < CONFLICT_M:
                first = k
                break
        for h in HORIZONS:
            labels[f"y{h}"] = 1 if (first is not None and first <= h) else 0
        rows.append({"scenario": job["scenario"], "seed": job["seed"], "split": job["split"],
                     "tick": idx, "robot": rid, "peer": pid, "x": f,
                     "ttc_ticks": first, **labels})
    return {"job": job, "rows": rows, "features": list(FEATURE_NAMES)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "reports", "advanced_v1", "dataset"))
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    jobs = []
    for split, seeds in (("train", TRAIN_SEEDS), ("validation", VALIDATION_SEEDS), ("test", TEST_SEEDS)):
        for sc, ov in SCENARIOS.items():
            for s in seeds:
                jobs.append({"split": split, "scenario": sc, "overrides": ov, "seed": s})
    counts: dict = {}
    features = None
    paths = {}
    handles = {sp: gzip.open(os.path.join(args.out, f"{sp}.jsonl.gz"), "wt")
               for sp in ("train", "validation", "test")}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for res in pool.map(collect, jobs):
            features = res["features"]
            sp = res["job"]["split"]
            for r in res["rows"]:
                handles[sp].write(json.dumps(r) + "\n")
            c = counts.setdefault(sp, {"rows": 0, "runs": 0, **{f"pos_y{h}": 0 for h in HORIZONS}})
            c["rows"] += len(res["rows"])
            c["runs"] += 1
            for r in res["rows"]:
                for h in HORIZONS:
                    c[f"pos_y{h}"] += r[f"y{h}"]
            print(sp, res["job"]["scenario"], res["job"]["seed"], len(res["rows"]), flush=True)
    for h in handles.values():
        h.close()
    for sp in handles:
        p = os.path.join(args.out, f"{sp}.jsonl.gz")
        with open(p, "rb") as fh:
            paths[sp] = {"file": os.path.basename(p), "sha256": hashlib.sha256(fh.read()).hexdigest()}
    manifest = {
        "dataset_version": DATASET_VERSION,
        "generator": "tools/edge_ai_dataset.py",
        "policy": "V0 product (app/product.make_swarmos_policy, advanced flags OFF)",
        "features": features, "horizons_ticks": list(HORIZONS),
        "label": "true pair distance < CONFLICT_M (0.97 m) within the next H arbitration ticks",
        "sample_every_ticks": SAMPLE_EVERY, "tick_cap": TICK_CAP,
        "scenarios": SCENARIOS,
        "seeds": {"train": list(TRAIN_SEEDS), "validation": list(VALIDATION_SEEDS),
                  "test": list(TEST_SEEDS)},
        "split_rule": "by run (seed); no run contributes rows to two splits",
        "counts": counts, "files": paths,
    }
    with open(os.path.join(args.out, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
    print(json.dumps(counts, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
