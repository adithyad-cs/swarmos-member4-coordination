"""LIVE_DISTRIBUTED_AUCTION: robot-side bids and gossip, WMS lease ledger."""

from __future__ import annotations

from app.coordination.models import AMRState, Position, RobotStatus
from app.coordination.task_auction import BID_WINDOW_TICKS, AuctionAgent, bid_cost
from app.sim.lease_ledger import LEASE_TTL_TICKS, MAX_ROUNDS, LeaseLedger

PROFILE = {"capacity_kg": 100.0, "max_speed_mps": 1.0}
TASK = {"task": "T1", "aid": "A-T1-v1", "version": 1, "tick": 0, "pick_m": [10.5, 5.5],
        "drop_m": [10.5, 20.5], "payload_kg": 20.0, "priority": "NORMAL", "excluded": []}


def _state(rid, x, y, *, battery=90.0, task=None):
    return AMRState(robot_id=rid, timestamp=0.0, position=Position(x=x, y=y), velocity=0.0,
                    heading=0.0, status=RobotStatus.AVAILABLE, battery=battery,
                    current_task_id=task)


def test_bid_uses_real_state_and_states_every_factor():
    b = bid_cost(_state("R001", 2.5, 5.5), PROFILE, TASK, [(10.0, 6.0), (30.0, 30.0)], 0.5)
    f = b["factors"]
    assert f["travel_s"] == 8.0 and f["congestion_peers"] == 1
    assert f["risk_s"] == 2.0 and f["battery_s"] == 0.0
    assert b["cost"] == round(f["travel_s"] + f["congestion_s"] + f["risk_s"] + f["battery_s"], 3)


def test_ineligible_robots_do_not_bid():
    assert bid_cost(_state("R001", 2.5, 5.5, task="T9"), PROFILE, TASK, [], 0.0) is None
    assert bid_cost(_state("R001", 2.5, 5.5), {**PROFILE, "capacity_kg": 10.0}, TASK, [], 0.0) is None
    assert bid_cost(_state("R001", 2.5, 5.5, battery=15.1), PROFILE, TASK, [], 0.0) is None


def test_congestion_and_risk_can_beat_distance():
    """Closer robot A in congestion with high predicted risk loses to B."""
    a = bid_cost(_state("R001", 8.5, 5.5), PROFILE, TASK, [(10, 5), (11, 6), (9, 4)], 1.5)
    b = bid_cost(_state("R002", 5.5, 5.5), PROFILE, TASK, [], 0.0)
    assert a["factors"]["travel_s"] < b["factors"]["travel_s"]
    assert b["cost"] < a["cost"]


def _gossip_line(agent, ids, rounds):
    """Radio line A - B - C: each round every robot hears only its neighbours."""
    nbrs = {ids[i]: [ids[j] for j in (i - 1, i + 1) if 0 <= j < len(ids)] for i in range(len(ids))}
    for _ in range(rounds):
        out = {rid: agent.outgoing(rid) for rid in ids}
        for rid in ids:
            for n in nbrs[rid]:
                if out[n]:
                    agent.on_receive(rid, out[n])


def test_full_table_gossip_converges_and_only_the_winner_claims():
    agent = AuctionAgent()
    agent.announce([TASK])
    for rid, x in (("R001", 30.5), ("R002", 20.5), ("R003", 11.5)):
        agent.make_bids(rid, _state(rid, x, 5.5), PROFILE, [], 0.0)
    _gossip_line(agent, ["R001", "R002", "R003"], rounds=2)
    # every robot now holds the SAME bid table, relayed across two hops
    for r in ("R001", "R002", "R003"):
        assert set(agent.known[r]["A-T1-v1"]) == {"R001", "R002", "R003"}
    agent.end_tick(BID_WINDOW_TICKS - 1, ["R001", "R002", "R003"])
    assert agent.claims == []                            # window still open
    agent.end_tick(BID_WINDOW_TICKS, ["R001", "R002", "R003"])
    assert [c["robot"] for c in agent.claims] == ["R003"]
    assert agent.agreement("A-T1-v1", "R003", ["R001", "R002", "R003"]) == (3, 3)


def test_tie_break_is_deterministic_by_robot_id():
    agent = AuctionAgent()
    agent.announce([TASK])
    for rid in ("R005", "R002"):
        agent.make_bids(rid, _state(rid, 2.5, 5.5), PROFILE, [], 0.0)
    for _ in range(2):
        for a, b in (("R005", "R002"), ("R002", "R005")):
            agent.on_receive(a, agent.outgoing(b))
    agent.end_tick(BID_WINDOW_TICKS, ["R002", "R005"])
    assert [c["robot"] for c in agent.claims] == ["R002"]


def test_bids_for_retired_auctions_are_ignored():
    agent = AuctionAgent()
    agent.announce([TASK])
    agent.make_bids("R001", _state("R001", 2.5, 5.5), PROFILE, [], 0.0)
    stale = agent.outgoing("R001")
    agent.retire("A-T1-v1")
    agent.on_receive("R002", stale)
    assert agent.known.get("R002", {}) == {}


def test_runner_up_claims_the_second_task_in_the_same_round():
    """R001 is cheapest for both tasks: it takes the first (queue order) and
    R002 claims the second at once - no idle re-auction round."""
    t2 = {**TASK, "task": "T2", "aid": "A-T2-v1", "pick_m": [11.5, 5.5]}
    agent = AuctionAgent()
    agent.announce([TASK, t2])
    agent.make_bids("R001", _state("R001", 10.5, 5.5), PROFILE, [], 0.0)
    agent.make_bids("R002", _state("R002", 14.5, 5.5), PROFILE, [], 0.0)
    for a, b in (("R001", "R002"), ("R002", "R001")):
        agent.on_receive(a, agent.outgoing(b))
    agent.end_tick(BID_WINDOW_TICKS, ["R001", "R002"])
    assert sorted((c["task"], c["robot"]) for c in agent.claims) == [("T1", "R001"), ("T2", "R002")]
    assert agent.agreement("A-T2-v1", "R002", ["R001", "R002"]) == (2, 2)


def test_a_robot_that_frees_up_during_the_window_can_still_bid():
    agent = AuctionAgent()
    agent.announce([TASK])
    agent.make_bids("R001", _state("R001", 2.5, 5.5, task="T9"), PROFILE, [], 0.0)
    assert "A-T1-v1" not in agent.own["R001"]
    agent.make_bids("R001", _state("R001", 2.5, 5.5), PROFILE, [], 0.0)
    assert agent.own["R001"]["A-T1-v1"]["robot"] == "R001"


def test_robots_known_busy_are_skipped_by_everyone():
    agent = AuctionAgent()
    agent.announce([TASK])
    for rid, x in (("R001", 9.5), ("R002", 20.5)):
        agent.make_bids(rid, _state(rid, x, 5.5), PROFILE, [], 0.0)
    for a, b in (("R001", "R002"), ("R002", "R001")):
        agent.on_receive(a, agent.outgoing(b))
    agent.end_tick(BID_WINDOW_TICKS, ["R001", "R002"],
                   {"R001": {"R001"}, "R002": {"R001"}})
    assert [c["robot"] for c in agent.claims] == ["R002"]


def _ledger_with_open():
    led = LeaseLedger()
    rec = led.open_auction({"task": "T1", "pick_m": [0, 0], "drop_m": [1, 1],
                            "payload_kg": 1.0, "priority": "NORMAL"}, 0, [])
    return led, rec


def _claim(rec, robot, cost):
    return {"aid": rec["aid"], "task": "T1", "version": rec["version"], "robot": robot,
            "cost": cost, "factors": {}, "tick": BID_WINDOW_TICKS}


def test_ledger_grants_one_lease_and_resolves_conflicting_claims():
    led, rec = _ledger_with_open()
    now = BID_WINDOW_TICKS + 1
    grants, fb, closed = led.resolve(now, [_claim(rec, "R003", 9.0), _claim(rec, "R001", 7.0)],
                                     lambda r, t: True, lambda a, w: (1, 2))
    assert [g[1]["robot"] for g in grants] == ["R001"]
    assert led.counters["conflicting_claims"] == 1
    assert led.leases["T1"].owner == "R001" and led.leases["T1"].version == 1
    assert led.counters["ownership_violations"] == 0


def test_ledger_rejects_stale_and_ineligible_claims():
    led, rec = _ledger_with_open()
    stale = {**_claim(rec, "R002", 1.0), "version": 99}
    grants, _, _ = led.resolve(BID_WINDOW_TICKS + 1, [stale, _claim(rec, "R004", 2.0)],
                               lambda r, t: r != "R004", lambda a, w: (0, 0))
    assert grants == []
    assert led.counters["claims_rejected_stale"] == 1
    assert led.counters["claims_rejected_ineligible"] == 1


def test_lease_renews_on_heartbeat_and_expires_without_it():
    led, rec = _ledger_with_open()
    led.resolve(BID_WINDOW_TICKS + 1, [_claim(rec, "R001", 1.0)], lambda r, t: True, lambda a, w: (1, 1))
    t0 = BID_WINDOW_TICKS + 1
    assert led.heartbeat("T1", True, t0 + 10) is False
    assert led.leases["T1"].expires_tick == t0 + 10 + LEASE_TTL_TICKS
    assert led.heartbeat("T1", False, t0 + 20) is False                 # not yet expired
    assert led.heartbeat("T1", False, t0 + 10 + LEASE_TTL_TICKS) is True
    assert "T1" not in led.leases and led.counters["leases_expired"] == 1


def test_no_winner_reauctions_then_falls_back_deterministically():
    led = LeaseLedger()
    fallbacks = []
    for r in range(MAX_ROUNDS):
        rec = led.open_auction({"task": "T1", "pick_m": [0, 0], "drop_m": [1, 1],
                                "payload_kg": 1.0, "priority": "NORMAL"}, r * 10, [])
        _, fb, _ = led.resolve(r * 10 + BID_WINDOW_TICKS + 1, [], lambda a, b: True, lambda a, w: (0, 0))
        fallbacks += fb
    assert led.counters["re_auctions"] == MAX_ROUNDS - 1
    assert [f["task"] for f in fallbacks] == ["T1"]
    lease = led.grant_fallback("T1", "R002", 99)
    assert lease.owner == "R002" and led.counters["fallback_allocations"] == 1
