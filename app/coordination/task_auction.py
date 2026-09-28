"""Live distributed task auction - the ROBOT side (feature LIVE_DISTRIBUTED_AUCTION).

Protocol, per task (see app/sim/lease_ledger.py for the WMS side):

  1. ANNOUNCE  The WMS publishes an open auction (task id, version, pick,
               drop, payload, priority, excluded robots). This is the warehouse
               management system injecting work, as in any real warehouse; it
               reaches every live robot over the site network.
  2. BID       Every eligible robot computes its OWN cost from its OWN state,
               its onboard profile and its OWN radio inbox (see bid_cost). The
               bid is fixed the first tick the robot can serve the auction.
  3. EXCHANGE  Each tick every robot broadcasts, over the bounded 15 m peer
               radio (loss, latency, partitions and blackouts all apply), every
               bid it knows for every open auction; receivers merge them. This
               is full-table gossip: in a connected fleet every robot holds the
               same bid table after (radio diameter) ticks.
  4. CLAIM     When the bid window closes, every robot runs the same
               deterministic matching over the bids it knows (auctions in WMS
               queue order, each to its cheapest bidder not already matched or
               known busy) and claims the task it is matched to. A robot that
               is cheapest for two tasks takes the first; the runner-up claims
               the second in the SAME round instead of waiting a re-auction.
  5. LEASE     The WMS ledger records the lease. It ARBITRATES only when the
               radio consensus is incomplete: conflicting claims are resolved by
               the robots' own total order (cost, robot id), and an auction left
               with no valid claim is filled from the robots' own sealed bids
               (sent with their claims) instead of idling for a re-auction.
               Every close records which of the two decided it.

Honest scope: bid computation and exchange are done by the robots, and the
robots determine winners by consensus where their radio views agree; the WMS
announces tasks, keeps the lease register and arbitrates where the views do
not. It is therefore distributed bidding with WMS lease arbitration, not a
fully leaderless system; the consensus/arbitration split is measured.

Deterministic: bids are rounded to 1e-3 and ordered by (cost, robot id); all
iteration is sorted.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

BID_WINDOW_TICKS = 5          # gossip rounds before a claim (0.5 s)
W_CONGESTION_S = 3.0          # s per peer (own inbox) within CONG_RADIUS_M of the pick
CONG_RADIUS_M = 4.0
W_RISK_S = 4.0                # s per unit of predicted-conflict probability (own predictions)
W_BATTERY_S = 5.0             # s at an empty battery, linear above the reserve band
BATTERY_SOFT_PCT = 60.0

# Onboard energy model (the robot's own firmware knows its drain rates).
MOVE_DRAIN_PCT_PER_S = 0.020
PAYLOAD_DRAIN_PCT_PER_KG_S = 0.0004
BATTERY_RESERVE_PCT = 15.0


def bid_cost(me, profile: dict, task: dict, inbox_positions, predicted_risk: float,
             route_m=None) -> Optional[dict]:
    """This robot's cost for a task, or None if it is not eligible.

    cost_s = travel_s + congestion_s + risk_s + battery_s, where
      travel_s     = route length (m) to the pick / own max speed; the route is
                     planned on the robot's onboard static map when `route_m`
                     is given, else the Manhattan distance is used
      congestion_s = W_CONGESTION_S x peers in own inbox within 4 m of the pick
      risk_s       = W_RISK_S x sum of this robot's current predicted-conflict
                     probabilities (Edge-AI when on, else 0)
      battery_s    = W_BATTERY_S x (60 - battery) / 60 when battery < 60 %
    Eligibility: idle (no task), not failed, able to carry the payload, and
    predicted to finish the task above the battery reserve.
    """
    if me.current_task_id is not None:
        return None
    if str(getattr(me.status, "value", me.status)) in ("FAILED", "CHARGING"):
        return None
    if task["payload_kg"] > profile["capacity_kg"]:
        return None
    speed = max(profile["max_speed_mps"], 1e-6)
    px, py = task["pick_m"]
    dx, dy = task["drop_m"]
    x, y = me.position.x, me.position.y
    to_pick = abs(px - x) + abs(py - y)
    legs = to_pick + abs(dx - px) + abs(dy - py)
    drain = legs / speed * (MOVE_DRAIN_PCT_PER_S + PAYLOAD_DRAIN_PCT_PER_KG_S * task["payload_kg"])
    if me.battery - drain < BATTERY_RESERVE_PCT:
        return None
    if route_m is not None:
        r = route_m((x, y), (px, py))
        if r is None:
            return None                       # no route to the pick: cannot serve it
        to_pick = r
    travel_s = to_pick / speed
    cong = sum(1 for (qx, qy) in inbox_positions if math.hypot(qx - px, qy - py) <= CONG_RADIUS_M)
    congestion_s = W_CONGESTION_S * cong
    risk_s = W_RISK_S * predicted_risk
    battery_s = W_BATTERY_S * max(0.0, BATTERY_SOFT_PCT - me.battery) / BATTERY_SOFT_PCT
    cost = round(travel_s + congestion_s + risk_s + battery_s, 3)
    return {"cost": cost, "factors": {
        "travel_s": round(travel_s, 3), "congestion_s": round(congestion_s, 3),
        "congestion_peers": cong, "risk_s": round(risk_s, 3),
        "battery_s": round(battery_s, 3), "battery_pct": round(me.battery, 1)}}


def _key(entry: dict) -> tuple:
    return (entry["cost"], entry["robot"])


@dataclass
class AuctionAgent:
    """Every robot's auction knowledge, held per robot id. Nothing here is
    shared between robots except through announce() (the WMS) and the radio
    payloads produced by outgoing() and consumed by on_receive()."""

    open: dict = field(default_factory=dict)          # aid -> announcement
    own: dict = field(default_factory=dict)           # rid -> {aid: entry}
    known: dict = field(default_factory=dict)         # rid -> {aid: {bidder: entry}}
    matched: dict = field(default_factory=dict)       # rid -> {aid: winner} (last claim round)
    seen: dict = field(default_factory=dict)          # aid -> {bidder: entry} (explanation only)
    claims: list = field(default_factory=list)
    standing: list = field(default_factory=list)      # own sealed bids sent with the claim
    _seq: int = 0
    counters: dict = field(default_factory=lambda: {
        "bids": 0, "bid_messages": 0, "bid_entries_sent": 0, "entries_received": 0,
        "claims": 0, "ineligible": 0})

    def announce(self, auctions: list[dict]) -> None:
        """Auctions arrive in the WMS queue order (priority, then age); that
        order is kept as `seq` so every robot assigns tasks in the same order."""
        for a in auctions:
            self._seq += 1
            self.open[a["aid"]] = {**a, "seq": self._seq}

    def retire(self, aid: str) -> None:
        self.open.pop(aid, None)
        self.seen.pop(aid, None)
        for table in (self.own, self.known, self.matched):
            for rid in table:
                table[rid].pop(aid, None)

    def make_bids(self, rid: str, me, profile: dict, inbox_positions, predicted_risk: float,
                  route_m=None) -> None:
        """Fix this robot's bid for every open auction it can serve and has not
        bid on yet. A robot that is busy when it first sees an auction bids as
        soon as it becomes free, while the auction is still open."""
        mine = self.own.setdefault(rid, {})
        known = self.known.setdefault(rid, {})
        for aid in sorted(self.open):
            if aid in mine:
                continue
            a = self.open[aid]
            if rid in a.get("excluded", ()):
                continue
            b = bid_cost(me, profile, a, inbox_positions, predicted_risk, route_m)
            if b is None:
                self.counters["ineligible"] += 1
                continue
            entry = {"robot": rid, "cost": b["cost"], "factors": b["factors"],
                     "aid": aid, "tick": a["tick"]}
            mine[aid] = entry
            self.counters["bids"] += 1
            self.seen.setdefault(aid, {})[rid] = entry
            known.setdefault(aid, {})[rid] = entry

    def outgoing(self, rid: str) -> Optional[dict]:
        """One bundled radio payload: every bid this robot knows for every open
        auction (its own and relayed ones) - full-table gossip."""
        known = self.known.get(rid, {})
        entries = [known[aid][b] for aid in sorted(known) if aid in self.open
                   for b in sorted(known[aid])]
        if not entries:
            return None
        self.counters["bid_messages"] += 1
        self.counters["bid_entries_sent"] += len(entries)
        return {"bids": [{"aid": e["aid"], "robot": e["robot"], "cost": e["cost"],
                          "factors": e["factors"], "tick": e["tick"]} for e in entries]}

    def on_receive(self, rid: str, payload: dict) -> None:
        known = self.known.setdefault(rid, {})
        for e in payload.get("bids", []):
            if e["aid"] not in self.open:
                continue                      # stale bid for a closed/retired auction
            self.counters["entries_received"] += 1
            known.setdefault(e["aid"], {}).setdefault(e["robot"], e)
            self.seen.setdefault(e["aid"], {}).setdefault(e["robot"], e)

    def _match(self, rid: str, due: list[str], busy: set) -> dict:
        """The allocation THIS robot computes from the bids it knows: auctions
        in WMS queue order, each to its cheapest bidder not already matched or
        known busy (cost, then robot id). Every robot with the same bid table
        computes the same result, so the robots agree without a coordinator."""
        known = self.known.get(rid, {})
        taken: set = set(busy)
        out: dict = {}
        for aid in due:
            bids = [e for b, e in known.get(aid, {}).items() if b not in taken]
            if not bids:
                continue
            w = min(bids, key=_key)["robot"]
            out[aid] = w
            taken.add(w)
        return out

    def end_tick(self, now: int, live_ids, busy_view=None) -> None:
        """Robots claim the task their own matching assigns them.

        `busy_view[rid]` is the set of robots `rid` believes already hold a
        task (itself included) - from its own state and its radio inbox."""
        self.claims = []
        self.standing = []
        due = sorted((aid for aid, a in self.open.items() if now >= a["tick"] + BID_WINDOW_TICKS),
                     key=lambda aid: (self.open[aid]["seq"], aid))
        if not due:
            return
        for rid in sorted(live_ids):
            busy = (busy_view or {}).get(rid, set())
            m = self._match(rid, due, busy)
            self.matched[rid] = m
            if rid in busy:
                continue
            # The robot's own sealed bids for the due auctions travel with its
            # claim (robot -> WMS link). The ledger uses them ONLY to fill an
            # auction the radio consensus left without a valid claim.
            for aid in due:
                mine = self.own.get(rid, {}).get(aid)
                if mine is not None:
                    a = self.open[aid]
                    self.standing.append({"aid": aid, "task": a["task"], "version": a["version"],
                                          "robot": rid, "cost": mine["cost"],
                                          "factors": mine["factors"], "tick": now})
            for aid, w in m.items():
                if w == rid:
                    a = self.open[aid]
                    mine = self.own[rid][aid]
                    self.claims.append({"aid": aid, "task": a["task"], "version": a["version"],
                                        "robot": rid, "cost": mine["cost"],
                                        "factors": mine["factors"], "tick": now})
                    self.counters["claims"] += 1

    def agreement(self, aid: str, winner: str, live_ids) -> tuple[int, int]:
        """How many robots that bid computed the same winner (convergence metric)."""
        agree = total = 0
        for rid in sorted(live_ids):
            if aid not in self.own.get(rid, {}):
                continue
            total += 1
            if self.matched.get(rid, {}).get(aid) == winner:
                agree += 1
        return agree, total
