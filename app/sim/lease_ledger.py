"""WMS task-lease ledger - the WAREHOUSE side of the live task auction.

The robots bid, exchange bids over the peer radio and decide who won
(app/coordination/task_auction.py). This ledger is the warehouse management
system's register of who holds which task. It:

  - opens auctions for pending work (bounded by the same WIP limit the
    greedy dispatcher uses, so both allocators release work at the same rate);
  - records a LEASE when a claim arrives, with a version, the grant tick and
    an expiry that the owner's heartbeat keeps renewing;
  - ARBITRATES only when two claims conflict for one task (a partition split
    the robots' consensus), choosing by the robots' own total order
    (cost, robot id); it never overrides a converged result;
  - expires a lease whose owner failed, was contained, went silent or stopped
    holding the task, and returns the task for RE-AUCTION;
  - after MAX_ROUNDS auctions with no valid claim, falls back to deterministic
    allocation for that task and records it as a fallback.

Invariant, checked on every grant: at most one ACTIVE lease per task and per
robot. A violation is counted, never silently resolved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from app.coordination.task_auction import BID_WINDOW_TICKS

LEASE_TTL_TICKS = 50          # 5 s without a heartbeat and the lease lapses
MAX_ROUNDS = 3                # auctions per task before deterministic fallback


@dataclass
class Lease:
    task: str
    owner: str
    version: int
    granted_tick: int
    expires_tick: int
    status: str = "ACTIVE"          # ACTIVE | COMPLETED | RELEASED | EXPIRED
    cost: Optional[float] = None
    reason: Optional[str] = None

    def as_dict(self) -> dict:
        return dict(self.__dict__)


@dataclass
class LeaseLedger:
    auctions: dict = field(default_factory=dict)       # aid -> record
    leases: dict = field(default_factory=dict)         # task -> Lease (ACTIVE only)
    history: list = field(default_factory=list)        # closed leases (bounded)
    _version: dict = field(default_factory=dict)       # task -> last version
    _round: dict = field(default_factory=dict)         # task -> auctions so far
    events: list = field(default_factory=list)         # this tick's events
    counters: dict = field(default_factory=lambda: {
        "auctions_opened": 0, "re_auctions": 0, "claims_received": 0,
        "conflicting_claims": 0, "claims_rejected_ineligible": 0,
        "claims_rejected_stale": 0, "leases_granted": 0, "leases_completed": 0,
        "leases_released": 0, "leases_expired": 0, "fallback_allocations": 0,
        "ownership_violations": 0, "latency_ticks_total": 0,
        "agreeing_bidders": 0, "bidders_at_close": 0, "winning_cost_total": 0.0,
        "closed_by_consensus": 0, "closed_by_arbitration": 0})
    _seq: int = 0

    # -- auctions ------------------------------------------------------------

    def open_task_ids(self) -> set:
        return {a["task"] for a in self.auctions.values()}

    def open_auction(self, task: dict, now: int, excluded: list[str]) -> dict:
        tid = task["task"]
        v = self._version.get(tid, 0) + 1
        self._version[tid] = v
        self._round[tid] = self._round.get(tid, 0) + 1
        if self._round[tid] > 1:
            self.counters["re_auctions"] += 1
        self._seq += 1
        rec = {**task, "aid": f"A-{tid}-v{v}", "version": v, "tick": now, "seq": self._seq,
               "round": self._round[tid], "excluded": sorted(excluded)}
        self.auctions[rec["aid"]] = rec
        self.counters["auctions_opened"] += 1
        self.events.append({"type": "AUCTION_OPEN", "aid": rec["aid"], "task": tid,
                            "version": v, "round": rec["round"], "tick": now,
                            "excluded": rec["excluded"]})
        return rec

    def resolve(self, now: int, claims: list[dict], eligible: Callable[[str, str], bool],
                agreement: Callable[[str, str], tuple[int, int]], standing=None):
        """Close due auctions, in WMS queue order. Returns (grants, fallbacks,
        closed_aids). `standing` are the robots' own sealed bids, used only
        for an auction left without a valid claim."""
        bids_by_aid: dict = {}
        for b in standing or ():
            if b["aid"] in self.auctions and self.auctions[b["aid"]]["version"] == b["version"]:
                bids_by_aid.setdefault(b["aid"], []).append(b)
        by_aid: dict = {}
        for c in claims:
            self.counters["claims_received"] += 1
            if c["aid"] not in self.auctions or self.auctions[c["aid"]]["version"] != c["version"]:
                self.counters["claims_rejected_stale"] += 1
                continue
            by_aid.setdefault(c["aid"], []).append(c)
        grants, fallbacks, closed = [], [], []
        granted_robots = {l.owner for l in self.leases.values()}
        for aid in sorted(self.auctions, key=lambda a: (self.auctions[a]["tick"],
                                                         self.auctions[a].get("seq", 0), a)):
            rec = self.auctions[aid]
            if now <= rec["tick"] + BID_WINDOW_TICKS:
                continue                              # still gossiping
            valid = []
            for c in sorted(by_aid.get(aid, []), key=lambda c: (c["cost"], c["robot"])):
                if c["robot"] in granted_robots or not eligible(c["robot"], rec["task"]):
                    self.counters["claims_rejected_ineligible"] += 1
                    continue
                valid.append(c)
            closed.append(aid)
            by = "consensus"
            if not valid:
                # the radio consensus left this auction without a valid claim:
                # fill it from the robots' own sealed bids, same total order
                for b in sorted(bids_by_aid.get(aid, []), key=lambda b: (b["cost"], b["robot"])):
                    if b["robot"] not in granted_robots and eligible(b["robot"], rec["task"]):
                        valid, by = [b], "arbitration"
                        break
            if valid:
                if len(valid) > 1:
                    self.counters["conflicting_claims"] += len(valid) - 1
                self.counters[f"closed_by_{by}"] += 1
                win = valid[0]
                agree, total = agreement(aid, win["robot"])
                self.counters["agreeing_bidders"] += agree
                self.counters["bidders_at_close"] += total
                # CLOSED before LEASE_GRANTED: the lease belongs to this result.
                self.events.append({"type": "AUCTION_CLOSED", "aid": aid, "task": rec["task"],
                                    "winner": win["robot"], "cost": win["cost"],
                                    "factors": win["factors"], "claims": len(valid),
                                    "agreeing_bidders": agree, "bidders": total, "tick": now,
                                    "latency_ticks": now - rec["tick"], "decided_by": by})
                lease = self._grant(rec, win, now)
                granted_robots.add(win["robot"])
                grants.append((rec, win, lease))
            else:
                self.events.append({"type": "AUCTION_NO_WINNER", "aid": aid, "task": rec["task"],
                                    "round": rec["round"], "tick": now})
                if self._round.get(rec["task"], 0) >= MAX_ROUNDS:
                    fallbacks.append(rec)
        for aid in closed:
            self.auctions.pop(aid, None)
        return grants, fallbacks, closed

    # -- leases --------------------------------------------------------------

    def _grant(self, rec: dict, claim: dict, now: int) -> Lease:
        tid = rec["task"]
        if tid in self.leases or any(l.owner == claim["robot"] for l in self.leases.values()):
            self.counters["ownership_violations"] += 1
        lease = Lease(task=tid, owner=claim["robot"], version=rec["version"],
                      granted_tick=now, expires_tick=now + LEASE_TTL_TICKS,
                      cost=claim.get("cost"))
        self.leases[tid] = lease
        self._round.pop(tid, None)
        self.counters["leases_granted"] += 1
        self.counters["latency_ticks_total"] += now - rec["tick"]
        if claim.get("cost") is not None:
            self.counters["winning_cost_total"] += claim["cost"]
        self.events.append({"type": "LEASE_GRANTED", "task": tid, "owner": claim["robot"],
                            "version": rec["version"], "tick": now,
                            "expires_tick": lease.expires_tick})
        return lease

    def grant_fallback(self, tid: str, robot: str, now: int) -> Lease:
        self.counters["fallback_allocations"] += 1
        v = self._version.get(tid, 0) + 1
        self._version[tid] = v
        rec = {"task": tid, "version": v, "tick": now}
        lease = self._grant(rec, {"robot": robot, "cost": None}, now)
        self.events.append({"type": "FALLBACK_ALLOCATION", "task": tid, "owner": robot, "tick": now})
        return lease

    def heartbeat(self, tid: str, alive: bool, now: int) -> bool:
        """Renew on a live heartbeat. Returns True when the lease just expired."""
        lease = self.leases.get(tid)
        if lease is None:
            return False
        if alive:
            lease.expires_tick = now + LEASE_TTL_TICKS
            return False
        if now >= lease.expires_tick:
            self._close(tid, "EXPIRED", "no heartbeat from the owner before expiry", now)
            self.counters["leases_expired"] += 1
            return True
        return False

    def complete(self, tid: str, now: int) -> None:
        if tid in self.leases:
            self._close(tid, "COMPLETED", "task completed", now)
            self.counters["leases_completed"] += 1

    def release(self, tid: str, reason: str, now: int) -> None:
        if tid in self.leases:
            self._close(tid, "RELEASED", reason, now)
            self.counters["leases_released"] += 1
        self._round.pop(tid, None)

    def _close(self, tid: str, status: str, reason: str, now: int) -> None:
        lease = self.leases.pop(tid)
        lease.status, lease.reason = status, reason
        self.history.append(lease.as_dict())
        if len(self.history) > 500:
            del self.history[:100]
        self.events.append({"type": f"LEASE_{status}", "task": tid, "owner": lease.owner,
                            "version": lease.version, "tick": now, "reason": reason})

    def summary(self) -> dict:
        c = dict(self.counters)
        g = c["leases_granted"] - c["fallback_allocations"]
        c["mean_auction_latency_ticks"] = round(c["latency_ticks_total"] / c["leases_granted"], 2) if c["leases_granted"] else None
        c["winner_agreement_rate"] = round(c["agreeing_bidders"] / c["bidders_at_close"], 4) if c["bidders_at_close"] else None
        c["mean_winning_cost_s"] = round(c["winning_cost_total"] / g, 3) if g > 0 else None
        closes = c["closed_by_consensus"] + c["closed_by_arbitration"]
        c["consensus_close_rate"] = round(c["closed_by_consensus"] / closes, 4) if closes else None
        c["active_leases"] = len(self.leases)
        c["open_auctions"] = len(self.auctions)
        return c
