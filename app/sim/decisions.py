"""Explainable decision records for predicted conflicts (observation only).

For every predicted conflict whose risk is HIGH or CRITICAL, a record answers
the questions a judge asks:

  what was detected   pair, predicted lead time, geometry, predicted point
  how severe          risk score, band, and the six weighted terms behind it
  what was decided    each robot's actual verdict this tick and its reason,
                      including the right-of-way contest utilities when the
                      graded ladder ran one
  what happened       filled in later: the conflict occurred (and how long
                      after the prediction) or the predicted window passed
                      without it

Records are built by the simulation from what the policy published (its
per-robot predictions and its verdicts). This module never acts, never touches
the RNG or the trace hash. The same seed yields byte-identical records, which is
checked by digest() (invariant INV-6).
"""

from __future__ import annotations

import hashlib
import json
from collections import deque
from typing import Optional

LOGGED_BANDS = ("HIGH", "CRITICAL")
TOLERANCE_TICKS = 3
RING = 200


class DecisionLog:
    def __init__(self) -> None:
        self._seq = 0
        self.records: deque = deque(maxlen=RING)
        self._open: dict[tuple[str, str], dict] = {}
        self._fresh: list[dict] = []
        self._hash = hashlib.sha256()
        self.total = 0
        self.outcomes = {"conflict_occurred": 0, "window_passed": 0}
        # Advanced-intelligence records (EDGE_AI / PROACTIVE / AUCTION). Built
        # from what the policy and the WMS ledger published; never acted on.
        self._edge_open: dict[tuple[str, str], dict] = {}
        self._pre_open: dict[str, dict] = {}
        self._alloc_by_aid: dict[str, dict] = {}
        self._alloc_by_task: dict[str, dict] = {}
        self.ai_counts = {"edge_episodes": 0, "edge_conflict_followed": 0,
                          "edge_cleared": 0, "proactive_records": 0,
                          "proactive_conflict_during_hold": 0,
                          "allocation_records": 0}

    @staticmethod
    def _key(a: str, b: str) -> tuple[str, str]:
        return (a, b) if a < b else (b, a)

    @staticmethod
    def _verdict(v) -> Optional[dict]:
        if v is None:
            return None
        return {
            "kind": v.kind.value,
            "reason": v.reason,
            "speed_scale": v.speed_scale,
            "yield_to": v.yield_to,
            "winning_margin": (round(v.winning_margin, 4)
                               if v.winning_margin is not None else None),
            "utility_terms": {k: round(x, 4) for k, x in sorted(v.utility_terms.items())},
        }

    def observe(self, tick: int, predictions, verdicts: dict) -> None:
        self._fresh = []
        for pc, risk in predictions:
            if risk.band not in LOGGED_BANDS:
                continue
            key = self._key(pc.robot, pc.peer)
            if key in self._open:
                continue
            self._seq += 1
            rec = {
                "id": f"D{self._seq:06d}",
                "tick": tick,
                "trigger": "predicted",
                "robots": list(key),
                "detected_by": pc.robot,
                "prediction": pc.as_dict(),
                "predicted_tick": tick + pc.lead_ticks,
                "risk": risk.as_dict(),
                "decisions": {
                    rid: self._verdict(verdicts.get(rid)) for rid in key
                },
                "outcome": None,
            }
            self._open[key] = rec
            self.records.append(rec)
            self._fresh.append(rec)
            self.total += 1
            self._hash.update(json.dumps(rec, sort_keys=True).encode())

    def observe_actual(self, tick: int, conflict_pairs: set, new_pairs: set) -> None:
        for key in sorted(new_pairs):
            rec = self._open.pop(key, None)
            if rec is not None:
                rec["outcome"] = {"result": "conflict_occurred", "tick": tick,
                                  "after_ticks": tick - rec["tick"]}
                self.outcomes["conflict_occurred"] += 1
                self._fresh.append(rec)
        for key in sorted(self._open):
            rec = self._open[key]
            if tick > rec["predicted_tick"] + TOLERANCE_TICKS and key not in conflict_pairs:
                rec["outcome"] = {"result": "window_passed", "tick": tick}
                self.outcomes["window_passed"] += 1
                del self._open[key]
                self._fresh.append(rec)

    # -- advanced-intelligence records ------------------------------------

    def _add(self, rec: dict) -> dict:
        self._seq += 1
        rec["id"] = f"D{self._seq:06d}"
        self.records.append(rec)
        self._fresh.append(rec)
        self.total += 1
        return rec

    def _seal(self, rec: dict) -> None:
        self._hash.update(json.dumps(rec, sort_keys=True).encode())

    def observe_ai(self, tick: int, edge_events, proactive_events, allocation_events,
                   verdicts: dict) -> None:
        """Called after arbitration each tick with this tick's published events."""
        positive = set()
        for e in edge_events or ():
            key = (e["robot"], e["peer"])
            positive.add(key)
            if key in self._edge_open:
                continue
            rec = self._add({"tick": tick, "trigger": "edge_ai", "robots": sorted(key),
                             "detected_by": e["robot"], "peer": e["peer"],
                             "prediction": {k: e[k] for k in ("probability", "confidence",
                                                             "horizon_ticks", "ttc_s", "model")},
                             "decision": self._verdict(verdicts.get(e["robot"])),
                             "outcome": None})
            self._edge_open[key] = rec
            self.ai_counts["edge_episodes"] += 1
        for key in sorted(self._edge_open):
            if key not in positive:
                rec = self._edge_open.pop(key)
                if rec["outcome"] is None:
                    rec["outcome"] = {"result": "prediction_cleared", "tick": tick}
                    self.ai_counts["edge_cleared"] += 1
                self._fresh.append(rec)
                self._seal(rec)
        for e in proactive_events or ():
            if e["type"] == "PRE-HOLD":
                v = verdicts.get(e["robot"])
                rec = self._add({
                    "tick": tick, "trigger": "proactive", "robots": sorted((e["robot"], e["peer"])),
                    "action": "PRE-HOLD", "held": e["robot"], "peer": e["peer"],
                    "prediction": {k: e.get(k) for k in ("probability", "confidence", "ttc_s",
                                                         "horizon_ticks", "model")},
                    "coordination": "HOLD",
                    "safety": {"kernel_final": v.kind.value if v else None,
                               "speed_scale": v.speed_scale if v else None,
                               "verdict": "APPROVED" if v is not None and (v.speed_scale or 0.0) <= 0.0
                               else "OVERRIDDEN"},
                    "peer_decision": self._verdict(verdicts.get(e["peer"])),
                    "outcome": None, "_conflict": False})
                self._pre_open[e["robot"]] = rec
                self.ai_counts["proactive_records"] += 1
            elif e["type"] == "RESUME":
                rec = self._pre_open.pop(e["robot"], None)
                if rec is not None:
                    rec["outcome"] = {"result": "RESUMED", "reason": e["reason"], "tick": tick,
                                      "held_ticks": e["held_ticks"],
                                      "conflict_during_hold": rec.pop("_conflict", False)}
                    if rec["outcome"]["conflict_during_hold"]:
                        self.ai_counts["proactive_conflict_during_hold"] += 1
                    self._fresh.append(rec)
                    self._seal(rec)
        for e in allocation_events or ():
            t = e["type"]
            if t == "AUCTION_OPEN":
                rec = self._add({"tick": tick, "trigger": "allocation", "robots": [],
                                 "task": e["task"], "auction": e["aid"], "version": e["version"],
                                 "round": e["round"], "status": "BIDDING", "bids": [],
                                 "winner": None, "lease": None, "outcome": None})
                self._alloc_by_aid[e["aid"]] = rec
                self.ai_counts["allocation_records"] += 1
            elif t in ("AUCTION_CLOSED", "AUCTION_NO_WINNER"):
                rec = self._alloc_by_aid.pop(e["aid"], None)
                if rec is None:
                    continue
                rec["bids"] = e.get("bids", [])
                rec["robots"] = sorted({b["robot"] for b in rec["bids"]})
                if t == "AUCTION_CLOSED":
                    rec.update(status="WON", winner=e["winner"], cost=e["cost"],
                               factors=e["factors"], latency_ticks=e["latency_ticks"],
                               agreeing_bidders=e["agreeing_bidders"], bidders=e["bidders"],
                               decided_by=e.get("decided_by"))
                    self._alloc_by_task[e["task"]] = rec
                else:
                    rec.update(status="NO_WINNER", outcome={"result": "re-auction", "tick": tick})
                    self._seal(rec)
                self._fresh.append(rec)
            elif t == "LEASE_GRANTED":
                rec = self._alloc_by_task.get(e["task"])
                if rec is not None:
                    rec["lease"] = {"owner": e["owner"], "version": e["version"],
                                    "granted_tick": e["tick"], "expires_tick": e["expires_tick"],
                                    "status": "ACTIVE"}
            elif t == "FALLBACK_ALLOCATION":
                rec = self._add({"tick": tick, "trigger": "allocation", "robots": [e["owner"]],
                                 "task": e["task"], "status": "FALLBACK", "winner": e["owner"],
                                 "outcome": None})
                self._alloc_by_task[e["task"]] = rec
                self.ai_counts["allocation_records"] += 1
            elif t.startswith("LEASE_"):
                rec = self._alloc_by_task.pop(e["task"], None)
                if rec is not None:
                    if rec.get("lease"):
                        rec["lease"]["status"] = t[len("LEASE_"):]
                    rec["outcome"] = {"result": t[len("LEASE_"):], "reason": e.get("reason"),
                                      "tick": tick}
                    self._fresh.append(rec)
                    self._seal(rec)

    def observe_ai_actual(self, tick: int, conflict_pairs: set) -> None:
        """Mark prediction episodes / pre-holds during which the pair really
        came inside the conflict threshold."""
        if not conflict_pairs:
            return
        for key, rec in self._edge_open.items():
            if rec["outcome"] is None and self._key(*key) in conflict_pairs:
                rec["outcome"] = {"result": "conflict_occurred", "tick": tick,
                                  "after_ticks": tick - rec["tick"]}
                self.ai_counts["edge_conflict_followed"] += 1
        for rid, rec in self._pre_open.items():
            if self._key(rid, rec["peer"]) in conflict_pairs:
                rec["_conflict"] = True

    def fresh(self) -> list[dict]:
        """Records created or resolved this tick, for the per-tick frame."""
        return list(self._fresh)[:20]

    def for_robot(self, robot_id: str, limit: int = 20) -> list[dict]:
        out = [r for r in self.records if robot_id in r["robots"]]
        return out[-limit:]

    def digest(self) -> str:
        return self._hash.hexdigest()

    def summary(self) -> dict:
        return {"records": self.total, "open": len(self._open), **self.outcomes,
                **self.ai_counts, "digest": self.digest()[:16]}
