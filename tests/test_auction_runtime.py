"""LIVE_DISTRIBUTED_AUCTION inside the running engine: bids travel over the
peer radio, the winner executes under a lease, and failures re-auction."""

from __future__ import annotations

from app.product import describe_policy, make_swarmos_policy
from app.sim.engine import SimEngine
from app.sim.lease_ledger import LEASE_TTL_TICKS
from app.sim.scenarios import get_scenario

AU = {"LIVE_DISTRIBUTED_AUCTION": True}


def _engine(seed=5, scen="overlap_batch", policy=None):
    return SimEngine(get_scenario(scen), seed=seed,
                     policy=policy or make_swarmos_policy(advanced=AU))


def _ownership_ok(eng):
    """Ground truth: no task held by two robots, no robot with two leases."""
    held = [r.current_task_id for r in eng.robots.values() if r.current_task_id]
    owners = [l.owner for l in eng.lease_ledger.leases.values()]
    return len(held) == len(set(held)) and len(owners) == len(set(owners))


def test_auction_allocates_through_radio_bids_and_winners_execute():
    eng = _engine()
    for _ in range(1500):
        eng.step()
        assert _ownership_ok(eng)
    alloc = eng.kpis()["allocation"]
    assert alloc["leases_granted"] > 0 and alloc["ownership_violations"] == 0
    assigned = [e for e in eng.events if e["kind"] == "task_assigned"]
    assert assigned and {e["via"] for e in assigned} <= {"auction", "fallback"}
    assert any(e["via"] == "auction" for e in assigned)
    # bids really crossed the radio: robots received peers' bid entries, and
    # auctions closed with more than one bidder in contention
    c = eng.policy.task_auction.counters
    assert c["bid_messages"] > 0 and c["entries_received"] > 0
    assert alloc["bidders_at_close"] > alloc["leases_granted"]
    assert eng.kpis()["tasks_complete"] > 0
    assert eng.safety_summary()["verdict"] == "PASS"


def test_auction_run_is_deterministic():
    a, b = _engine(seed=9), _engine(seed=9)
    a.run(800)
    b.run(800)
    assert a.trace_hash == b.trace_hash
    assert a.kpis()["allocation"] == b.kpis()["allocation"]


def test_flag_off_keeps_the_greedy_dispatcher():
    eng = _engine(policy=make_swarmos_policy())
    eng.run(300)
    assert eng.kpis()["allocation"] is None
    assert {e["via"] for e in eng.events if e["kind"] == "task_assigned"} <= {"greedy"}
    assert describe_policy(make_swarmos_policy(advanced=AU))["advanced"] == ["LIVE_DISTRIBUTED_AUCTION"]


def _first_owner(eng, limit=600):
    for _ in range(limit):
        eng.step()
        if eng.lease_ledger.leases:
            tid = sorted(eng.lease_ledger.leases)[0]
            return tid, eng.lease_ledger.leases[tid].owner
    raise AssertionError("no lease granted")


def test_winner_blackout_expires_the_lease_and_the_task_is_reauctioned():
    eng = _engine(seed=5)
    tid, owner = _first_owner(eng)
    eng.inject("COMM_BLACKOUT", robot_id=owner, ticks=LEASE_TTL_TICKS * 3)
    for _ in range(LEASE_TTL_TICKS + 2):
        eng.step()
    c = eng.lease_ledger.counters
    assert c["leases_expired"] >= 1
    assert eng.robots[owner].current_task_id != tid
    assert tid in eng.pending                     # back on the queue at once
    # re-auctioned when the WIP gate next admits work (same rule as greedy)
    for _ in range(2000):
        eng.step()
        assert _ownership_ok(eng)
        lease = eng.lease_ledger.leases.get(tid)
        if lease is not None and lease.owner != owner:
            break
    lease = eng.lease_ledger.leases.get(tid)
    done = eng.tasks[tid].status.value == "COMPLETE"
    assert done or (lease is not None and lease.version > 1)
    assert c["ownership_violations"] == 0


def test_winner_failure_releases_the_lease_and_reauctions():
    eng = _engine(seed=5)
    tid, owner = _first_owner(eng)
    eng.inject("ROBOT_FAILURE", robot_id=owner)
    eng.step()
    assert tid not in eng.lease_ledger.leases or eng.lease_ledger.leases[tid].owner != owner
    assert eng.lease_ledger.counters["leases_released"] >= 1
    assert tid in eng.pending
    for _ in range(3000):
        eng.step()
        assert _ownership_ok(eng)
        if tid in eng.lease_ledger.leases:
            break
    assert eng.lease_ledger.leases[tid].owner != owner
    assert eng.safety_summary()["verdict"] == "PASS"


def test_heavy_packet_loss_still_allocates_without_duplicate_ownership():
    eng = _engine(seed=7)
    eng.inject("LINK_IMPAIR", drop_pct=60.0, latency_ms=300.0)
    for _ in range(1500):
        eng.step()
        assert _ownership_ok(eng)
    alloc = eng.kpis()["allocation"]
    assert alloc["leases_granted"] > 0 and alloc["ownership_violations"] == 0
    assert eng.safety_summary()["verdict"] == "PASS"


ALL = {"EDGE_AI_PREDICTOR": True, "PREDICTIVE_COORDINATION": True,
       "LIVE_DISTRIBUTED_AUCTION": True}


def test_silenced_fleet_gets_no_leases_then_recovers_after_the_blackout():
    """Auction timeout: nobody can bid, auctions close without a winner and
    re-open; no lease is granted to a robot the WMS cannot hear."""
    eng = _engine(seed=5)
    for rid in sorted(eng.robots):
        eng.inject("COMM_BLACKOUT", robot_id=rid, ticks=120)
    for _ in range(100):
        eng.step()
        assert all(not eng.policy.radio.is_silenced(l.owner)
                   for l in eng.lease_ledger.leases.values())
    c = eng.lease_ledger.counters
    assert c["leases_granted"] == 0 and c["re_auctions"] >= 1
    for _ in range(300):
        eng.step()
    assert eng.lease_ledger.counters["leases_granted"] > 0
    assert eng.safety_summary()["verdict"] == "PASS"


import pytest  # noqa: E402


@pytest.mark.parametrize("fault,params", [
    ("LINK_IMPAIR", {"drop_pct": 30.0, "latency_ms": 500.0}),
    ("ZONE_PARTITION", {"zone": "EAST"}),
    ("ROBOT_FAILURE", {}),
    ("COMM_BLACKOUT", {"ticks": 200}),
    ("TASK_BURST", {"count": 10}),
])
def test_all_three_features_survive_degraded_operation(fault, params):
    eng = SimEngine(get_scenario("rush_50"), seed=13,
                    policy=make_swarmos_policy(advanced=ALL))
    eng.run(200)
    eng.inject(fault, **params)
    for _ in range(900):
        eng.step()
        assert _ownership_ok(eng)
    k = eng.kpis()
    assert k["safety"]["verdict"] == "PASS", k["safety"]
    assert k["allocation"]["ownership_violations"] == 0
    assert k["tasks_complete"] > 0
    adv = k["advanced"]
    assert adv["edge_ai"]["status"] == "ok" and adv["edge_ai"]["calls"] > 0
