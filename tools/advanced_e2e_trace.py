"""Extract one complete, machine-checked advanced-intelligence chain from a
real run, then replay the run and prove it reproduces.

Chain (every link is read from the engine's own event log and DecisionRecords;
nothing is synthesised):
  task -> auction opened -> robots' bids -> winner -> WMS lease -> execution
  (task picked) -> Edge-AI prediction for the winner -> PRE-HOLD proposal ->
  safety kernel approves (final verdict holds, speed 0) -> prediction clears
  without the pair entering the conflict band -> RESUME -> task complete ->
  the records the Decision Inspector shows for that robot -> replay identical.

Usage: PYTHONPATH=. python3 tools/advanced_e2e_trace.py [--scenario S] [--seed N]
Writes reports/advanced_v1/e2e_trace.json.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.product import ADVANCED_FLAGS, describe_policy, make_swarmos_policy  # noqa: E402
from app.sim.engine import SimEngine  # noqa: E402
from app.sim.scenarios import get_scenario  # noqa: E402

OUT = os.path.join(ROOT, "reports", "advanced_v1", "e2e_trace.json")


def run(scenario: str, seed: int, cap: int):
    policy = make_swarmos_policy(advanced={k: True for k in ADVANCED_FLAGS})
    eng = SimEngine(get_scenario(scenario), seed=seed, policy=policy)
    records, events, verdict_log = [], [], {}
    for _ in range(cap):
        eng.step()
        records.extend(json.loads(json.dumps(r, default=str)) for r in eng.decisions.fresh())
        events.extend(e for e in eng._events_this_tick)
        k = eng.kpis()
        if k["tasks_total"] and k["tasks_complete"] >= k["tasks_total"] and not eng.pending:
            break
        for rid, v in (eng.policy._last_decisions or {}).items():
            if v.proactive:
                verdict_log.setdefault((rid, eng.clock.tick), v.as_dict())
    return eng, records, events, verdict_log


def find_chain(records, events, consensus_only=True):
    """A chain whose auction the ROBOTS decided (consensus, >= 2 bidders
    agreeing) is preferred; consensus_only=False accepts a ledger-arbitrated one."""
    by_task_alloc = {}
    for r in records:
        if r.get("trigger") == "allocation" and r.get("status") == "WON" and r.get("lease"):
            if consensus_only and not (r.get("decided_by") == "consensus"
                                       and (r.get("agreeing_bidders") or 0) >= 2):
                continue
            by_task_alloc.setdefault(r["task"], r)
    for pre in records:
        if pre.get("trigger") != "proactive" or not pre.get("outcome"):
            continue
        out = pre["outcome"]
        if out.get("reason") != "cleared" or out.get("conflict_during_hold"):
            continue
        if pre["safety"]["verdict"] != "APPROVED":
            continue
        rid, t0 = pre["held"], pre["tick"]
        # the task the held robot was executing, won at auction before the hold
        for tid, alloc in by_task_alloc.items():
            if alloc["winner"] != rid or alloc["lease"]["granted_tick"] > t0:
                continue
            picked = [e for e in events if e["kind"] == "task_picked" and e["task_id"] == tid]
            done = [e for e in events if e["kind"] == "task_complete" and e["task_id"] == tid]
            if not done or done[0]["tick"] < out["tick"]:
                continue
            pred = [r for r in records if r.get("trigger") == "edge_ai" and r["detected_by"] == rid
                    and r["peer"] == pre["peer"] and r["tick"] <= t0]
            if not pred:
                continue
            return {"robot": rid, "task": tid, "allocation": alloc, "prediction": pred[-1],
                    "proactive": pre, "picked": picked[:1], "completed": done[0]}
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="overlap_batch")
    ap.add_argument("--seed", type=int, nargs="+", default=list(range(1000001, 1000011)))
    ap.add_argument("--cap", type=int, default=12000)
    a = ap.parse_args()
    for seed in a.seed:
        eng, records, events, vlog = run(a.scenario, seed, a.cap)
        chain = find_chain(records, events) or find_chain(records, events, consensus_only=False)
        if chain is None:
            print(f"seed {seed}: no complete chain", flush=True)
            continue
        rid = chain["robot"]
        assigned = [e for e in events if e["kind"] == "task_assigned" and e["task_id"] == chain["task"]
                    and e["robot_id"] == rid]
        t_hold = chain["proactive"]["tick"]
        kernel = vlog.get((rid, t_hold)) or vlog.get((rid, t_hold + 1))
        inspector = [r for r in records if rid in r.get("robots", [])
                     and r.get("trigger") in ("allocation", "edge_ai", "proactive")
                     and t_hold - 200 <= r["tick"] <= chain["proactive"]["outcome"]["tick"]]
        eng2, records2, _, _ = run(a.scenario, seed, a.cap)
        out = {
            "scenario": a.scenario, "seed": seed, "policy": describe_policy(eng.policy),
            "chain": {
                "1_task_and_auction": {k: chain["allocation"].get(k) for k in
                                       ("task", "auction", "version", "round", "tick")},
                "2_bids": chain["allocation"]["bids"],
                "3_winner": {k: chain["allocation"].get(k) for k in
                             ("winner", "cost", "factors", "latency_ticks", "agreeing_bidders", "bidders")},
                "4_lease": chain["allocation"]["lease"],
                "5_execution": {"assigned": assigned[:1], "picked": chain["picked"]},
                "6_edge_ai_prediction": chain["prediction"],
                "7_proactive_action": {k: chain["proactive"][k] for k in
                                       ("tick", "action", "held", "peer", "prediction", "coordination")},
                "8_safety_kernel": {**chain["proactive"]["safety"], "final_verdict": kernel},
                "9_conflict_clears_and_resume": chain["proactive"]["outcome"],
                "10_task_complete": chain["completed"],
                "11_decision_inspector_records": inspector,
            },
            "replay": {"trace_hash": eng.trace_hash, "replay_trace_hash": eng2.trace_hash,
                       "decision_digest": eng.decisions.digest(),
                       "replay_decision_digest": eng2.decisions.digest(),
                       "identical": eng.trace_hash == eng2.trace_hash
                       and eng.decisions.digest() == eng2.decisions.digest()
                       and records == records2},
            "safety": eng.safety_summary(),
        }
        with open(OUT, "w") as fh:
            json.dump(out, fh, indent=2, sort_keys=True, default=str)
        print(json.dumps({"seed": seed, "robot": rid, "task": chain["task"],
                          "hold_tick": t_hold, "resume": chain["proactive"]["outcome"],
                          "replay_identical": out["replay"]["identical"],
                          "safety": out["safety"]["verdict"]}, indent=1))
        return 0
    print("no seed produced a complete chain")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
