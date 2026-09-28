import sys, json, collections
sys.path.insert(0, "/home/user/swarmos-member4-coordination")
from tools.run_experiment import build_scenario, make_policy
from app.sim.engine import SimEngine
sc, arm, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
eng = SimEngine(build_scenario(sc, {}), seed=seed, policy=make_policy(arm, seed))
picks = collections.Counter(t.pick for t in eng.tasks.values())
drops = collections.Counter(t.drop for t in eng.tasks.values())
eng.run(None) if False else None
while not eng.finished: eng.step()
hold = {r: eng._goal_cell.get(r) for r, rr in eng.robots.items() if rr.current_task_id}
g = collections.Counter(hold.values())
shared = sum(1 for v in hold.values() if g[v] > 1)
remaining = [t for t in eng.tasks.values() if t.status.value != 'COMPLETE']
print(json.dumps(dict(seed=seed, arm=arm, sc=sc, finished=eng.batch_done_s is not None, holders=len(hold), holders_sharing_goal=shared,
    goals=[list(v) if v else None for v in hold.values()], distinct_picks=len(picks), max_tasks_per_pick=max(picks.values()),
    distinct_drops=len(drops), remaining=len(remaining))))
