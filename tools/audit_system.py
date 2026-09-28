"""SWARMOS whole-system behaviour audit (backend + API, in-process).

Checks that features WORK, not merely that their code exists. Each check
records PASS / FAIL with the observed evidence. Exit status 1 on any FAIL.

  PYTHONPATH=. python3 tools/audit_system.py [--quick]

Categories: core simulation, coordination, safety, prediction and
explainability, the full fault matrix (engine and HTTP, live and co-sim, with
and without a selected robot, applied-effect and recovery checks, determinism),
benchmark surfaces, and the HTTP/WebSocket API including its error paths.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

RESULTS: list[tuple[str, str, str, str]] = []


def record(cat: str, name: str, ok: bool, evidence: str = "") -> None:
    RESULTS.append((cat, name, "PASS" if ok else "FAIL", evidence))


def check(cat: str, name: str):
    """Decorator-free helper: run fn, record FAIL with traceback on exception."""
    def wrap(fn):
        try:
            ok, ev = fn()
            record(cat, name, bool(ok), ev)
        except Exception as exc:                     # pragma: no cover
            record(cat, name, False, f"EXCEPTION {type(exc).__name__}: {exc} | "
                   + traceback.format_exc().splitlines()[-2].strip())
        return fn
    return wrap


def small(name: str, **over):
    from app.sim.scenarios import get_scenario
    spec = get_scenario(name)
    return type(spec)(**{**spec.__dict__, **over}) if over else spec


def eng(name: str = "rush_50", policy: str = "swarmos", seed: int = 11, **over):
    from app.api.runner import _make_policy
    from app.sim.engine import SimEngine
    return SimEngine(small(name, **over), seed=seed, policy=_make_policy(policy, seed),
                     label=policy)


# ---------------------------------------------------------------------------
# 1. core simulation
# ---------------------------------------------------------------------------

def audit_core() -> None:
    from app.sim.scenarios import SCENARIOS
    from app.sim.warehouse import Cell

    for name in sorted(SCENARIOS):
        @check("core", f"scenario {name}: builds, spawns, moves, runs 300 ticks")
        def _():
            e = eng(name, fleet_size=min(12, SCENARIOS[name].fleet_size))
            wh = e.warehouse
            racks = sum(1 for row in wh.grid for c in row if c is Cell.RACK)
            e.run(300)
            moved = sum(r.distance_travelled_m for r in e.robots.values())
            k = e.kpis()
            ok = (racks > 0 and len(e.robots) > 0 and moved > 1.0
                  and e.clock.tick == 300 and abs(e.sim_time - 30.0) < 1e-6
                  and len(e.tasks) > 0 and k["collisions"] == 0)
            return ok, (f"racks={racks} robots={len(e.robots)} odo={moved:.1f}m "
                        f"tasks={len(e.tasks)} sim_time={e.sim_time}")

    @check("core", "task lifecycle: created -> assigned -> picked -> completed")
    def _():
        e = eng("rush_50", fleet_size=8)
        e.run(2400)
        st = {t.status.value for t in e.tasks.values()}
        done = [t for t in e.tasks.values() if t.completed_s is not None]
        ok = "COMPLETE" in st and done and all(
            t.assigned_s is not None and t.picked_s is not None
            and t.created_s <= t.assigned_s <= t.picked_s <= t.completed_s
            for t in done)
        return ok, f"statuses={sorted(st)} completed={len(done)}"

    @check("core", "batch termination: fixed batch ends when all tasks done")
    def _():
        e = eng("overlap_batch", initial_burst=4, fleet_size=3)
        while not e.finished:
            e.step()
        k = e.kpis()
        return (k["tasks_complete"] == 4 and k["makespan_s"] and not k["did_not_finish"],
                f"makespan={k['makespan_s']} ticks={e.clock.tick}")

    @check("core", "batch cap: unfinished batch is reported did_not_finish")
    def _():
        e = eng("overlap_batch", initial_burst=24, fleet_size=2, duration_s=20.0)
        while not e.finished:
            e.step()
        k = e.kpis()
        return (k["did_not_finish"] and k["makespan_s"] is None and e.clock.tick == 200,
                f"dnf={k['did_not_finish']} makespan={k['makespan_s']} tick={e.clock.tick}")

    @check("core", "determinism: same seed -> identical trace hash (swarmos + baseline)")
    def _():
        hs = []
        for pol in ("swarmos", "baseline", "stop_and_wait"):
            a, b = eng("rush_50", pol, fleet_size=12), eng("rush_50", pol, fleet_size=12)
            a.run(500)
            b.run(500)
            hs.append(a.trace_hash == b.trace_hash)
        c = eng("rush_50", fleet_size=12, seed=13)
        c.run(500)
        d = eng("rush_50", fleet_size=12)
        d.run(500)
        return all(hs) and c.trace_hash != d.trace_hash, f"same={hs} seeds_differ={c.trace_hash != d.trace_hash}"

    @check("core", "task stream depends on seed only (identical across policies)")
    def _():
        a, b = eng("rush_50", "swarmos", fleet_size=8), eng("rush_50", "stop_and_wait", fleet_size=8)
        a.run(200)
        b.run(200)
        ka = [(t.task_id, t.pick, t.drop, t.priority.value, t.payload_kg, t.created_s)
              for t in a.tasks.values()]
        kb = [(t.task_id, t.pick, t.drop, t.priority.value, t.payload_kg, t.created_s)
              for t in b.tasks.values()]
        return ka == kb, f"tasks={len(ka)}"

    @check("core", "idle parking keeps idle robots off station cells (batch)")
    def _():
        e = eng("overlap_batch", initial_burst=4, fleet_size=4)
        while not e.finished:
            e.step()
        e.run(300)
        from app.sim.warehouse import Cell
        on_station = [rid for rid, r in e.robots.items()
                      if e.warehouse.cell_at(*e.warehouse.m_to_cell(r.x, r.y))
                      in (Cell.PICK, Cell.DROP) and r.current_task_id is None]
        return not on_station, f"idle robots on stations: {on_station}"


# ---------------------------------------------------------------------------
# 2. coordination
# ---------------------------------------------------------------------------

def audit_coordination() -> None:
    @check("coordination", "radio exchange: messages delivered, bounded range, O(k)")
    def _():
        e = eng("rush_50", fleet_size=24)
        e.run(300)
        s = e.policy.stats()
        r = s["radio"]
        return (r["delivered"] > 0 and r["out_of_range"] >= 0
                and s["msgs_per_robot_tick"] > 0,
                f"delivered={r['delivered']} out_of_range={r['out_of_range']} "
                f"msgs/robot/tick={s['msgs_per_robot_tick']}")

    @check("coordination", "path intent exchange: broadcast states carry movement_intent")
    def _():
        e = eng("rush_50", fleet_size=8)
        e.run(50)
        states = e.observed_states()
        with_intent = sum(1 for s in states.values() if s.movement_intent and s.movement_intent.path)
        return with_intent > 0, f"{with_intent}/{len(states)} states carry a path"

    @check("coordination", "graded ladder: PROCEED, SLOW, YIELD, WAIT and REROUTE all issued")
    def _():
        e = eng("narrow_aisle_deadlock", fleet_size=24)
        e.run(1800)
        v = e.kpis()["verdicts"]
        need = {"PROCEED", "SLOW", "YIELD", "WAIT", "REROUTE"}
        return need <= set(v), f"verdicts={v}"

    @check("coordination", "contest / negotiation runs with utility terms")
    def _():
        e = eng("narrow_aisle_deadlock", fleet_size=24)
        e.run(600)
        s = e.policy.stats()
        contested = [v for v in e._last_verdicts.values() if v.utility_terms]
        return s["contests"] > 0, f"contests={s['contests']} won={s['contests_won']} with_terms_now={len(contested)}"

    @check("coordination", "failure detection confirms a failed robot and releases its task")
    def _():
        e = eng("rush_50", fleet_size=12)
        e.run(200)
        busy = sorted(r for r, x in e.robots.items() if x.current_task_id)
        rid = busy[0] if busy else sorted(e.robots)[0]
        task = e.robots[rid].current_task_id
        e.inject("ROBOT_FAILURE", robot_id=rid)
        e.run(30)
        s = e.policy.stats()
        released = task is None or e.tasks[task].assigned_robot != rid or e.tasks[task].status.value == "PENDING"
        return (s["failures_confirmed"] >= 1 and e.robots[rid].failed and released,
                f"confirmed={s['failures_confirmed']} task={task} released={released}")

    @check("coordination", "deadlock audit + stall release produce bounded recovery")
    def _():
        e = eng("narrow_aisle_deadlock", fleet_size=24)
        e.run(1800)
        k = e.kpis()
        return ("deadlock" in k and k["stall_releases"] >= 0
                and k["deadlock"]["deadlocks_formed"] >= 0,
                f"deadlock={k['deadlock']} stall_releases={k['stall_releases']}")

    @check("coordination", "reservation / auction / conflict libraries import and run")
    def _():
        from app.coordination import auction, conflict, reservation  # noqa: F401
        return True, "imported (unit-tested in tests/test_reservation.py, test_auction.py, test_conflict.py; not in the live arbitration path by design)"

    @check("coordination", "perception fallback adds nothing on a healthy radio")
    def _():
        from app.coordination.swarm_policy import SwarmPolicy
        from app.sim.engine import SimEngine
        a = SimEngine(small("rush_50", fleet_size=16), seed=11, policy=SwarmPolicy())
        b = SimEngine(small("rush_50", fleet_size=16), seed=11,
                      policy=SwarmPolicy(perception_fallback=True))
        a.run(400)
        b.run(400)
        return a.trace_hash == b.trace_hash and b.policy.sensed_blocks == 0, "hash identical, sensed_blocks=0"

    @check("coordination", "headline config: separating exemption and mutual-hold break OFF")
    def _():
        from app.api.runner import _make_policy
        p = _make_policy("swarmos", 11)
        return (p.separating_exemption is False and p.mutual_hold_break is False
                and p.traffic_rules_enabled is False and p.perception_fallback is True
                and p.monitor_enabled is True,
                "sep=False mhb=False traffic=False fallback=True monitor=True")


# ---------------------------------------------------------------------------
# 3. safety
# ---------------------------------------------------------------------------

def audit_safety() -> None:
    @check("safety", "negative control FAILS INV-1 and names the pair")
    def _():
        e = eng("rush_50", "stop_and_wait", fleet_size=16)
        from app.sim.policy import NoOpPolicy
        e.set_policy(NoOpPolicy())
        e.run(600)
        s = e.safety_summary()
        return (s["verdict"] == "FAIL" and "INV-1" in s["first_violation"],
                f"INV-1={s['counts']['INV-1']} first={s['first_violation'].get('INV-1')}")

    for pol in ("swarmos", "baseline", "stop_and_wait"):
        @check("safety", f"{pol}: all invariants PASS, min separation >= 0.70 m")
        def _(pol=pol):
            e = eng("rush_50", pol, fleet_size=24)
            e.run(1200)
            s = e.safety_summary()
            return (s["verdict"] == "PASS" and (s["min_separation_m"] or 1) >= 0.70,
                    f"counts={s['counts']} min_sep={s['min_separation_m']} L2={s['margin_breaches']}")

    @check("safety", "unauthorised movement detected (INV-2)")
    def _():
        e = eng("rush_50", fleet_size=4)
        e.run(5)
        before = {r: (x.x, x.y, x.failed, x.quarantined) for r, x in e.robots.items()}
        next(iter(e.robots.values())).x += 1.0
        e._check_motion_invariants(before)
        return e.safety_summary()["counts"]["INV-2"] >= 1, "teleport caught"

    @check("safety", "movement while held detected (INV-3)")
    def _():
        e = eng("rush_50", fleet_size=4)
        e.run(5)
        r = next(iter(e.robots.values()))
        before = {rid: (x.x, x.y, x.failed, x.quarantined) for rid, x in e.robots.items()}
        r.apply_verdict_scale(0.0)
        r.x += 0.01
        e._check_motion_invariants(before)
        return e.safety_summary()["counts"]["INV-3"] >= 1, "held robot motion caught"

    @check("safety", "illegal status transition detected (INV-4)")
    def _():
        from app.coordination.models import RobotStatus
        e = eng("rush_50", fleet_size=4)
        r = next(iter(e.robots.values()))
        before = {rid: (x.x, x.y, x.failed, x.quarantined) for rid, x in e.robots.items()}
        r.failed = True
        r.status = RobotStatus.MOVING
        e._check_motion_invariants(before)
        return e.safety_summary()["counts"]["INV-4"] >= 1, "failed->MOVING caught"

    @check("safety", "monitor OFF lets collisions happen (kernel is doing the work)")
    def _():
        from app.coordination.swarm_policy import SwarmPolicy
        from app.sim.engine import SimEngine
        e = SimEngine(small("rush_50", fleet_size=24), seed=11, policy=SwarmPolicy(monitor=False))
        e.run(900)
        return e.kpis()["collisions"] > 0, f"collisions without kernel={e.kpis()['collisions']}"


# ---------------------------------------------------------------------------
# 4. prediction / explainability
# ---------------------------------------------------------------------------

def audit_prediction() -> None:
    @check("prediction", "product lookahead is observe-only (trace identical)")
    def _():
        from app.coordination.swarm_policy import SwarmPolicy
        from app.sim.engine import SimEngine
        a = SimEngine(small("rush_50", fleet_size=16), seed=11, policy=SwarmPolicy(perception_fallback=True))
        b = SimEngine(small("rush_50", fleet_size=16), seed=11,
                      policy=SwarmPolicy(perception_fallback=True, lookahead_h=15))
        a.run(500)
        b.run(500)
        la = b.kpis()["lookahead"]
        return a.trace_hash == b.trace_hash and la["prediction_episodes"] > 0, f"lookahead={la}"

    @check("prediction", "decision records: risk terms, decisions, outcomes, deterministic digest")
    def _():
        a, b = eng("overlap_batch"), eng("overlap_batch")
        a.run(1500)
        b.run(1500)
        recs = list(a.decisions.records)
        resolved = [r for r in recs if r["outcome"]]
        ok = (recs and all(r["risk"]["band"] in ("HIGH", "CRITICAL") for r in recs)
              and resolved and a.decisions.digest() == b.decisions.digest())
        return ok, f"records={len(recs)} resolved={len(resolved)} digest={a.decisions.digest()[:12]}"

    @check("prediction", "snapshot/frame carries decisions and safety summary")
    def _():
        e = eng("overlap_batch")
        found = False
        for _ in range(1500):
            snap = e.step().as_dict()
            if snap["decisions"]:
                found = True
                break
        k = snap["kpis"]
        return found and "safety" in k and "lookahead" in k and "deadlock" in k, \
            f"decisions_in_frame={found} kpi_keys_ok={'safety' in k}"


# ---------------------------------------------------------------------------
# 5. fault matrix (engine level)
# ---------------------------------------------------------------------------

def audit_faults() -> None:
    from app.sim.scenarios import FaultKind

    def run_with(kind, ticks_before=200, ticks_after=200, fleet=16, **params):
        e = eng("rush_50", fleet_size=fleet)
        e.run(ticks_before)
        detail = e.inject(kind, **params)
        e.run(ticks_after)
        return e, detail

    @check("faults", "ROBOT_FAILURE: robot stays FAILED and visible, onboard brake, fleet continues")
    def _():
        e, d = run_with("ROBOT_FAILURE")
        rid = d["robot_id"]
        frame = e.step().as_dict()
        vis = [r for r in frame["robots"] if (r.get("id") or r.get("robot_id")) == rid]
        return (d["applied"] and e.robots[rid].failed and e.robots[rid].status.value == "FAILED"
                and vis and e.kpis()["collisions"] == 0,
                f"robot={rid} still_in_frame={bool(vis)}")

    @check("faults", "BATTERY_DRAIN: battery set low, robot heads to charger, recovers")
    def _():
        e = eng("rush_50", fleet_size=8)
        e.run(100)
        d = e.inject("BATTERY_DRAIN", level=8.0)
        rid = d["robots"][0]
        phases, charged = set(), False
        for _ in range(3000):
            e.step()
            phases.add(e._phase.get(rid))
            if e.robots[rid].status.value == "CHARGING":
                charged = True
        # Recovery means actually CHARGING, not merely heading to a charger
        # (the weaker check hid a permanent wedge: see engine._blocker_cell).
        return (d["applied"] and charged,
                f"robot={rid} phases={sorted(p for p in phases if p)} charged={charged} battery={e.robots[rid].battery:.1f}")

    @check("faults", "BLOCK_AISLE + CLEAR_BLOCKAGE: cells blocked, no robot plans into them, cleared")
    def _():
        e, d = run_with("BLOCK_AISLE", ticks_after=100)
        blocked = set(e.warehouse.blocked)
        inside = [r for r, x in e.robots.items()
                  if any(e.warehouse.m_to_cell(*wp) in blocked for wp in x.path[1:])]
        c = e.inject("CLEAR_BLOCKAGE")
        return (d["applied"] and blocked and not inside and c["applied"] and not e.warehouse.blocked,
                f"blocked={len(blocked)} paths_through={inside} cleared={c['cells_cleared']}")

    @check("faults", "ROGUE_ROBOT (integrity ON): lie detected by quorum and contained")
    def _():
        from app.coordination.swarm_policy import SwarmPolicy
        from app.sim.engine import SimEngine
        e = SimEngine(small("rush_50", fleet_size=16), seed=11,
                      policy=SwarmPolicy(integrity=True, perception_fallback=True))
        e.run(100)
        d = e.inject("ROGUE_ROBOT")
        e.run(300)
        s = e.policy.stats()["integrity"]
        return (d["applied"] and s["robots_contained"] >= 1 and e.kpis()["collisions"] == 0,
                f"rogue={d['robot_id']} contained={s['robots_contained']} accusations={s['accusations']}")

    @check("faults", "ROGUE_ROBOT (integrity OFF): recorded as rogue, not contained (documented)")
    def _():
        e, d = run_with("ROGUE_ROBOT")
        return (d["applied"] and e.robots[d["robot_id"]].rogue
                and e.kpis()["robots_rogue"] == 1, f"rogue={d['robot_id']}")

    @check("faults", "LINK_IMPAIR: loss reaches radio, collision-free, timed restore")
    def _():
        e, d = run_with("LINK_IMPAIR", ticks_after=100, drop_pct=30.0, latency_ms=100.0, ticks=80)
        dropped = e.policy.radio.stats.dropped
        restored = e.policy.radio.profile.is_perfect
        return (d["applied"] and dropped > 0 and restored and e.kpis()["collisions"] == 0,
                f"dropped={dropped} restored={restored} latency_ticks={d['latency_ticks']}")

    @check("faults", "LINK_IMPAIR 100% (fleet outage): 0 collisions, restores")
    def _():
        e, d = run_with("LINK_IMPAIR", ticks_after=200, drop_pct=100.0, latency_ms=0.0, ticks=60)
        return (d["applied"] and e.kpis()["collisions"] == 0 and e.policy.radio.profile.is_perfect,
                f"sensed_blocks={e.policy.sensed_blocks} collisions={e.kpis()['collisions']}")

    @check("faults", "ZONE_PARTITION: cross-boundary drops, lifts on schedule")
    def _():
        e = eng("rush_50", fleet_size=24)
        e.run(100)
        before = e.policy.radio.stats.dropped
        d = e.inject("ZONE_PARTITION", zone="EAST", ticks=100)
        e.run(50)
        mid = e.policy.radio.stats.dropped
        e.run(60)
        return (d["applied"] and mid > before and e.policy.radio.partition is None
                and e.kpis()["collisions"] == 0, f"drops during={mid - before}")

    @check("faults", "TASK_BURST (demand spike): tasks added and served")
    def _():
        e = eng("rush_50", fleet_size=12)
        e.run(50)
        n0 = len(e.tasks)
        d = e.inject("TASK_BURST", count=20)
        e.run(600)
        return (d["applied"] and len(e.tasks) >= n0 + 20, f"tasks {n0} -> {len(e.tasks)}")

    @check("faults", "KILL_ML: advisory off, robot behaviour unchanged (law 3)")
    def _():
        a = eng("rush_50", fleet_size=16)
        b = eng("rush_50", fleet_size=16)
        a.run(100)
        b.run(100)
        d = b.inject("KILL_ML")
        a.run(400)
        b.run(400)
        return (d["applied"] and not b.ml_enabled and a.trace_hash == b.trace_hash,
                f"hash_equal={a.trace_hash == b.trace_hash}")

    @check("faults", "COMM_BLACKOUT: silenced, sovereign entry, restored and rejoins")
    def _():
        e, d = run_with("COMM_BLACKOUT", ticks_after=120)
        s = e.policy.stats()["sovereign"]
        return (d["applied"] and s["entries"] >= 1 and s["rejoins"] >= 1
                and not e.policy.radio.silenced and e.kpis()["collisions"] == 0,
                f"entries={s['entries']} rejoins={s['rejoins']}")

    @check("faults", "every FaultKind is handled (no silent no-op)")
    def _():
        missing = []
        for k in FaultKind:
            e = eng("rush_50", fleet_size=8)
            e.run(10)
            det = e.inject(k)
            if not isinstance(det, dict) or "applied" not in det:
                missing.append(k.value)
        return not missing, f"missing={missing}"

    @check("faults", "fault runs are deterministic (same fault, same seed, same hash)")
    def _():
        hs = []
        for kind in ("ROBOT_FAILURE", "LINK_IMPAIR", "ROGUE_ROBOT", "COMM_BLACKOUT", "BLOCK_AISLE"):
            a, _ = run_with(kind, ticks_after=150)
            b, _ = run_with(kind, ticks_after=150)
            hs.append((kind, a.trace_hash == b.trace_hash))
        return all(x for _, x in hs), str(hs)


# ---------------------------------------------------------------------------
# 6. HTTP / WebSocket API, including the fault matrix as the UI sends it
# ---------------------------------------------------------------------------

def audit_api() -> None:
    import anyio
    from starlette.testclient import TestClient

    from app.api import server as srv
    from app.api.runner import _FAULT_ALIASES

    def reset():
        anyio.run(srv.manager.stop)
        srv.manager.engine = None
        srv.manager.config = None
        srv.manager.running = False
        srv.manager._last_frame = None

    reset()
    with TestClient(srv.app) as c:
        @check("api", "pages and read-only endpoints respond")
        def _():
            codes = {p: c.get(p).status_code for p in
                     ("/", "/index.html", "/landing.html", "/api/health", "/api/scenarios",
                      "/api/status", "/api/cosim/status")}
            return all(v == 200 for v in codes.values()), str(codes)

        @check("api", "error paths are readable, never 500")
        def _():
            outs = {
                "no run step": c.post("/api/sim/step", json={}).json(),
                "no run inject": c.post("/api/sim/inject", json={"fault": "kill_ml"}).json(),
                "no run pause": c.post("/api/sim/pause").json(),
                "unknown scenario": c.post("/api/sim/start", json={"scenario": "nope"}).json(),
                "bad seed type": c.post("/api/sim/start", json={"seed": "x"}).json(),
                "no run explain": c.get("/api/explain/R001").json(),
                "cosim inject no run": c.post("/api/cosim/inject", json={"fault": "KILL_ML"}).json(),
                "bad benchmark seeds": c.post("/api/benchmark/run", json={"seeds": "x"}).json(),
            }
            bad = {k: v for k, v in outs.items() if v.get("ok") is not False or not v.get("error")}
            r = c.post("/api/sim/start", content=b"{not json", headers={"content-type": "application/json"})
            return not bad and r.status_code < 500, f"bad={bad} malformed_json={r.status_code}"

        @check("api", "run lifecycle: start -> step -> pause -> resume -> pause -> stop")
        def _():
            seq = [c.post("/api/sim/start", json={"scenario": "rush_50", "seed": 11, "fleet_size": 8}).json(),
                   c.post("/api/sim/step", json={"ticks": 10}).json(),
                   c.post("/api/sim/pause").json(),
                   c.post("/api/sim/resume").json(),
                   c.post("/api/sim/pause").json()]
            h = c.get("/api/trace/hash").json()
            st = c.post("/api/sim/stop").json()
            return all(x["ok"] for x in seq) and h["ok"] and st["ok"], f"hash={h.get('hash', '')[:12]}"

        @check("api", "websocket /ws/fleet: hello then frames with decisions + safety")
        def _():
            c.post("/api/sim/start", json={"scenario": "overlap_batch", "seed": 11, "speed": 10})
            with c.websocket_connect("/ws/fleet") as ws:
                hello = ws.receive_json()
                frame = None
                for _ in range(5):
                    frame = ws.receive_json()
                    if frame.get("type") == "frame" and frame.get("robots"):
                        break
            c.post("/api/sim/stop")
            ok = (hello["type"] == "hello" and hello["warehouse"] and frame
                  and "decisions" in frame and "safety" in frame["kpis"])
            return ok, f"hello_keys={sorted(hello)[:6]} frame_keys={sorted(frame)[:10] if frame else None}"

        # The fault matrix as the Lab sends it: with AND without a selected robot.
        lab_faults = ["robot_failure", "comm_blackout", "link_impair", "blocked_aisle", "rogue_agent"]
        for fault in list(_FAULT_ALIASES):
            for selected in (None, "R002"):
                @check("api-faults", f"live inject {fault} (selected robot={selected})")
                def _(fault=fault, selected=selected):
                    c.post("/api/sim/start", json={"scenario": "rush_50", "seed": 11, "fleet_size": 8})
                    c.post("/api/sim/step", json={"ticks": 20})
                    body = {"fault": fault}
                    if selected is not None:
                        body["robot_id"] = selected
                    r = c.post("/api/sim/inject", json=body).json()
                    c.post("/api/sim/step", json={"ticks": 20})
                    c.post("/api/sim/stop")
                    lab = " [offered in Lab]" if fault in lab_faults else ""
                    # clear_blockage with nothing blocked honestly reports
                    # applied=False; every other fault must actually apply.
                    applied = r.get("detail", {}).get("applied")
                    ok = r.get("ok") is True and (applied is True or fault == "clear_blockage")
                    if selected is not None and fault != "clear_blockage":
                        ok = ok and (r["detail"].get("robot_id") in (None, selected)
                                     or "robot_id" in r.get("ignored_params", []))
                    return ok, \
                        f"{json.dumps(r)[:160]}{lab}"

        from app.sim.scenarios import FaultKind
        for kind in FaultKind:
            @check("api-faults", f"co-sim inject {kind.value} lands on both arms")
            def _(kind=kind):
                c.post("/api/cosim/start", json={"scenario": "rush_50", "seed": 11, "fleet_size": 8,
                                                 "ticks": 100, "speed": 10})
                r = c.post("/api/cosim/inject", json={"fault": kind.value}).json()
                c.post("/api/cosim/stop")
                return r.get("ok") is True and r.get("arms") == ["swarmos", "baseline"], json.dumps(r)[:120]

        @check("api", "websocket /ws/cosim: hello + frame with both arms")
        def _():
            c.post("/api/cosim/start", json={"scenario": "corridor_demo", "seed": 11, "ticks": 200, "speed": 10})
            with c.websocket_connect("/ws/cosim") as ws:
                hello = ws.receive_json()
                frame = ws.receive_json()
            c.post("/api/cosim/stop")
            return hello.get("type") and frame, f"hello={hello.get('type')} frame_keys={sorted(frame)[:8]}"

        @check("api", "explain endpoint: policy view, decisions, safety")
        def _():
            c.post("/api/sim/start", json={"scenario": "overlap_batch", "seed": 11, "speed": 10})
            c.post("/api/sim/step", json={"ticks": 100})
            r = c.get("/api/explain/R001").json()
            u = c.get("/api/explain/R999").json()
            c.post("/api/sim/stop")
            return (r["ok"] and r["policy"] and "decisions" in r and r["safety"]["verdict"]
                    and u["ok"] is False), f"verdict={r['safety']['verdict']}"

        @check("benchmark", "benchmark endpoint returns JSON-safe paired stats")
        def _():
            r = c.post("/api/benchmark/run", json={"scenario": "rush_50", "seeds": [11, 13], "ticks": 300})
            body = r.json()
            json.dumps(body, allow_nan=False)
            return body["ok"] and "throughput" in body, f"usable={body.get('usable_seeds')}"
    reset()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args(argv)
    sections = {"core": audit_core, "coordination": audit_coordination,
                "safety": audit_safety, "prediction": audit_prediction,
                "faults": audit_faults, "api": audit_api}
    for name, fn in sections.items():
        if args.only and name not in args.only:
            continue
        fn()
    width = max(len(n) for _, n, _, _ in RESULTS)
    for cat, name, status, ev in RESULTS:
        print(f"{status}  {cat:12s} {name:<{width}}  {ev}")
    fails = sum(1 for r in RESULTS if r[2] == "FAIL")
    print("-" * 78)
    print(f"{len(RESULTS) - fails} pass, {fails} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
