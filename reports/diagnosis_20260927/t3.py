import sys, math
sys.path.insert(0, "/home/user/swarmos-member4-coordination")
from tools.run_experiment import build_scenario, make_policy
from app.sim.engine import SimEngine
from app.coordination.swarm_policy import project_step, MAX_STEP_M, segment_distance, _step_envelope
sc, arm, seed, T, a, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], sys.argv[6]
eng = SimEngine(build_scenario(sc, {}), seed=seed, policy=make_policy(arm, seed))
cap = {}
orig = eng.policy.arbitrate
def w(tick, t, states):
    v = orig(tick, t, states)
    if T - 2 <= tick <= T + 1:
        cap[tick] = (states[a], states[b], v[a], v[b])
    return v
eng.policy.arbitrate = w
while eng.clock.tick <= T + 1:
    before = (eng.robots[a].x, eng.robots[a].y, eng.robots[b].x, eng.robots[b].y)
    eng.step()
    t = eng.clock.tick - 1
    if t in cap:
        sa, sb, va, vb = cap[t]
        pa = (sa.position.x, sa.position.y); pb = (sb.position.x, sb.position.y)
        proj = project_step(sa, MAX_STEP_M); env = _step_envelope(pa, proj)
        ra = eng.robots[a]
        print(f"tick {t}: {a} obs {pa} true_before {before[:2]} speed {sa.speed if hasattr(sa,'speed') else '?'} proj {tuple(round(x,3) for x in proj)} env {tuple(round(x,3) for x in env)}")
        print(f"   verdict {va.kind.value} scale {va.speed_scale} | {b} obs {pb} verdict {vb.kind.value} {vb.speed_scale}")
        print(f"   actual after {(round(ra.x,3), round(ra.y,3))} step_len {round(math.dist(before[:2], (ra.x, ra.y)),3)} proj_len {round(math.dist(pa, env),3)}  seg gap planned {round(segment_distance((pa, env), (pb, pb)),3)}  true dist after {round(math.dist((ra.x,ra.y),(eng.robots[b].x,eng.robots[b].y)),3)}")
        print(f"   {a} path head {[(round(p[0],2),round(p[1],2)) for p in (ra.path or [])[:3]]}  intent {[(round(p.x,2),round(p.y,2)) for p in (sa.movement_intent.path[:3] if sa.movement_intent else [])]}")
