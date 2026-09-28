"""Read-only classifier for one run. Prints one JSON line."""
import sys, math, json, collections, itertools
sys.path.insert(0, "/home/user/swarmos-member4-coordination")
from tools.run_experiment import build_scenario, make_policy
from app.sim.engine import SimEngine
FLOOR = 0.75
def main(sc, arm, seed):
    eng = SimEngine(build_scenario(sc, {}), seed=seed, policy=make_policy(arm, seed))
    last = {}
    orig = eng.policy.arbitrate
    def w(tick, t, states):
        v = orig(tick, t, states); last.clear(); last.update(v); return v
    eng.policy.arbitrate = w
    ids = sorted(eng.robots)
    inside = set(); onsets = []; last_done = (0, 0)
    stall_ev = collections.Counter()
    while not eng.finished:
        pre = {r: (eng.robots[r].x, eng.robots[r].y, len(eng.robots[r].path or []),
                   eng.robots[r].current_task_id, eng._phase.get(r)) for r in ids}
        eng.step()
        for e in eng._events_this_tick:
            if e["kind"] == "task_stalled": stall_ev[e["robot_id"]] += 1
        if len(eng.completed) != last_done[1]: last_done = (eng.clock.tick, len(eng.completed))
        for a, b in itertools.combinations(ids, 2):
            ra, rb = eng.robots[a], eng.robots[b]
            d = math.hypot(ra.x - rb.x, ra.y - rb.y)
            if d < FLOOR and (a, b) not in inside:
                inside.add((a, b))
                info = {}
                for r in (a, b):
                    rr = eng.robots[r]; p = pre[r]
                    moved = math.hypot(rr.x - p[0], rr.y - p[1])
                    v = last.get(r)
                    info[r] = dict(moved=round(moved, 3), corner=(len(rr.path or []) < p[2] and moved > 0),
                                   verdict=v.kind.value if v else None, reason=(v.reason[:40] if v else None),
                                   task=p[3], phase=p[4])
                onsets.append(dict(tick=eng.clock.tick, pair=[a, b], d=round(d, 3), who=info))
            elif d >= FLOOR and (a, b) in inside:
                inside.discard((a, b))
    # terminal state
    term = []
    for r in ids:
        rr = eng.robots[r]
        if rr.current_task_id is None: continue
        v = last.get(r)
        peer = v.conflict_with[0] if v and v.conflict_with else (v.yield_to if v else None)
        dpeer = None; peer_idle = None; peer_verdict = None
        if peer in eng.robots:
            p = eng.robots[peer]; dpeer = round(math.hypot(rr.x - p.x, rr.y - p.y), 3)
            peer_idle = p.current_task_id is None; peer_verdict = last[peer].kind.value if peer in last else None
        term.append(dict(r=r, verdict=v.kind.value if v else None, reason=(v.reason[:45] if v else None), peer=peer,
                         d=dpeer, peer_idle=peer_idle, peer_verdict=peer_verdict, phase=eng._phase.get(r), stalls=stall_ev[r]))
    k = eng.kpis()
    persistent_floor = [list(p) for p in inside]
    print(json.dumps(dict(sc=sc, arm=arm, seed=seed, done=len(eng.completed), total=len(eng.tasks),
        finished=eng.batch_done_s is not None, last_done_tick=last_done[0], ticks=eng.clock.tick,
        onsets=onsets, inside_at_end=persistent_floor, terminal=term,
        margin_breaches=k["margin_breaches"])))
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
