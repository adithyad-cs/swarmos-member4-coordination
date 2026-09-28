import sys, math
sys.path.insert(0, "/home/user/swarmos-member4-coordination")
from tools.run_experiment import build_scenario, make_policy
from app.sim.engine import SimEngine
sc, arm, seed, T0, T1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]); who = sys.argv[6:]
eng = SimEngine(build_scenario(sc, {}), seed=seed, policy=make_policy(arm, seed))
last = {}
orig = eng.policy.arbitrate
def w(tick, t, states):
    v = orig(tick, t, states); last.clear(); last.update(v); return v
eng.policy.arbitrate = w
while eng.clock.tick < T1:
    eng.step()
    t = eng.clock.tick - 1
    if t >= T0:
        evs = [e['kind'] for e in eng._events_this_tick if e.get('robot_id') in who]
        line = []
        for r in who:
            rr = eng.robots[r]; v = last[r]
            line.append(f"{r} {eng.warehouse.m_to_cell(rr.x, rr.y)} ({rr.x:.2f},{rr.y:.2f}) goal {eng._goal_cell.get(r)} {v.kind.value[:4]} next {[(round(p[0],1),round(p[1],1)) for p in (rr.path or [])[:2]]}")
        print(t, ' | '.join(line), evs if evs else '')
