"""Read-only diagnostic tracer. Does not modify engine or policy behaviour."""
import sys, json, collections
sys.path.insert(0, "/home/user/swarmos-member4-coordination")
from tools.run_experiment import build_scenario, make_policy
from app.sim.engine import SimEngine

def run(scenario, arm, seed, max_ticks=None, keep_every=1):
    spec = build_scenario(scenario, {})
    pol = make_policy(arm, seed)
    eng = SimEngine(spec, seed=seed, policy=pol, label=arm)
    log = []            # per tick: {rid: (kind, reason, conflict, yield_to)}
    orig = eng.policy.arbitrate
    def wrapped(tick, t, states):
        v = orig(tick, t, states)
        log.append({rid: (x.kind.value, x.reason, tuple(x.conflict_with), x.yield_to, x.speed_scale) for rid, x in v.items()})
        return v
    eng.policy.arbitrate = wrapped
    events = []; snaps = {}
    done_at = []
    while not eng.finished and (max_ticks is None or eng.clock.tick < max_ticks):
        eng.step()
        for e in eng._events_this_tick:
            if e["kind"] in ("task_completed","task_assigned","task_stalled","task_released","unreachable","livelock_suspected"):
                events.append(e)
        if len(eng.completed) != (done_at[-1][1] if done_at else 0):
            done_at.append((eng.clock.tick, len(eng.completed)))
        snaps_tick = eng.clock.tick
        snaps[snaps_tick] = {rid: dict(cell=eng.warehouse.m_to_cell(r.x, r.y), xy=(round(r.x,2), round(r.y,2)),
                              status=r.status.value, task=r.current_task_id, phase=eng._phase.get(rid),
                              goal=eng._goal_cell.get(rid) or eng._park_goal.get(rid), path=len(r.path or []),
                              batt=round(r.battery,1)) for rid, r in eng.robots.items()} if snaps_tick % keep_every == 0 else None
    return eng, log, events, done_at, snaps
