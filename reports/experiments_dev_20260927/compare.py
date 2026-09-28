"""Print the improvement-cycle metrics for one or more experiment dirs."""
import json, sys, glob, os, statistics as st
def load(d):
    return [json.loads(l) for l in open(os.path.join(d, "runs.jsonl"))]
rows = []
for d in sys.argv[1:]:
    rows += load(d)
def m(xs):
    xs = [x for x in xs if x is not None]; return round(st.mean(xs), 1) if xs else None
print(f"{'scenario':17s} {'arm':24s} {'n':>3s} {'finish':>7s} {'mksp fin mean':>13s} {'mksp cens':>9s} {'t90 cens':>8s} {'col':>4s} {'inv':>4s} {'brch':>5s} {'froz':>5s} {'runs frz':>8s} {'replans':>8s} {'reroute':>8s} {'stall':>6s} {'persist':>7s}")
for sc in ("overlap_batch", "open_floor_batch"):
    for arm in sorted({r["arm"] for r in rows if r["scenario"] == sc}, key=lambda a: (a.split("+")[0], a)):
        g = [r for r in rows if r["scenario"] == sc and r["arm"] == arm]
        fin = [r for r in g if not r["did_not_finish"]]
        print(f"{sc:17s} {arm:24s} {len(g):3d} {len(fin):3d}/{len(g):<3d} {str(m([r['makespan_s'] for r in fin])):>13s} "
              f"{str(m([r['makespan_censored_s'] for r in g])):>9s} {str(m([r['t90_censored_s'] for r in g])):>8s} "
              f"{sum(r['collisions'] for r in g):4d} {sum(r['invariant_failures'] for r in g):4d} "
              f"{sum(r['margin_breaches'] for r in g):5d} {sum((r.get('frozen_pairs') or 0) for r in g):5d} "
              f"{sum(1 for r in g if (r.get('frozen_pairs') or 0) > 0):8d} {str(m([r['replans'] for r in g])):>8s} "
              f"{str(m([r['reroute_count'] for r in g])):>8s} {str(m([r['stall_releases'] for r in g])):>6s} "
              f"{str(m([r['deadlock']['persistent_deadlocks'] for r in g])):>7s}")
