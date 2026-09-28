"""Prediction-driven proactive coordination (feature PREDICTIVE_COORDINATION).

The Edge-AI predictor (advisory, injected - see app/product.py) tells a robot
that it and a peer are likely to come within CONFLICT_M within the model
horizon. Acting on that BEFORE the pair reaches the contest band turns a late,
reactive standoff into an early, orderly pass: one robot PRE-HOLDs, the other
proceeds, and the held robot RESUMEs when the prediction clears.

What this module decides, and what it never does:
  - it only ever turns a PROCEED/SLOW proposal into a HOLD (zero motion). It
    never grants motion, so it cannot create a collision;
  - every verdict it shapes still passes the binding safety kernel
    (SwarmPolicy._monitor), which does not consult the model at all;
  - it acts only while the pair is NOT yet inside CONFLICT_M (the reactive
    ladder owns imminent conflicts).

Who holds is decided by a rule both robots evaluate identically from the same
broadcast states, so they agree without a message:
  1. a robot closing on a peer that is not closing on it holds (the F3 rule);
  2. otherwise a robot without a task holds for one with a task;
  3. otherwise the robot with the longer remaining route holds;
  4. otherwise the higher robot id holds.

Anti-oscillation, all measured in stats():
  - enter only at probability >= the model's decision threshold AND
    confidence >= CONF_MIN; stay while probability >= OFF_RATIO x threshold
    (hysteresis);
  - MIN_HOLD_TICKS before any release, MAX_HOLD_TICKS hard cap (after which
    the ordinary ladder takes over);
  - COOLDOWN_TICKS per pair after a release before a new pre-hold;
  - predictions older than STALE_TICKS are ignored.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

CONF_MIN = 0.6
OFF_RATIO = 0.6
MIN_HOLD_TICKS = 5
MAX_HOLD_TICKS = 25
COOLDOWN_TICKS = 40
STALE_TICKS = 2
CLOSING_COS = 0.05


def _closing(a, b) -> bool:
    """Is `a` moving towards `b` this tick (from broadcast heading/speed)?"""
    v = float(a.velocity or 0.0)
    if v < 1e-3:
        # A stopped robot with a plan is judged by where its path points.
        intent = a.movement_intent
        if intent is None or not intent.path:
            return False
        p = intent.path[0]
        dx, dy = p.x - a.position.x, p.y - a.position.y
    else:
        dx, dy = math.cos(a.heading or 0.0), math.sin(a.heading or 0.0)
    rx, ry = b.position.x - a.position.x, b.position.y - a.position.y
    norm = math.hypot(dx, dy) * math.hypot(rx, ry)
    # Closing means pointing within ~87 degrees of the peer; a perpendicular
    # pass is not closing (and float noise must not decide the holder).
    return norm > 0.0 and (dx * rx + dy * ry) / norm > CLOSING_COS


def _remaining(s) -> float:
    intent = s.movement_intent
    if intent is None or not intent.path:
        return 0.0
    x, y = s.position.x, s.position.y
    total = 0.0
    for p in intent.path:
        total += math.hypot(p.x - x, p.y - y)
        x, y = p.x, p.y
    return total


def holder(a, b) -> str:
    """robot_id of the robot that should PRE-HOLD in the pair (a, b)."""
    ca, cb = _closing(a, b), _closing(b, a)
    if ca != cb:
        return a.robot_id if ca else b.robot_id
    ta, tb = bool(a.current_task_id), bool(b.current_task_id)
    if ta != tb:
        return b.robot_id if ta else a.robot_id
    ra, rb = round(_remaining(a), 3), round(_remaining(b), 3)
    if ra != rb:
        return a.robot_id if ra > rb else b.robot_id
    return max(a.robot_id, b.robot_id)


@dataclass
class _Hold:
    peer: str
    since: int
    probability: float
    confidence: float
    ttc_s: Optional[float]


@dataclass
class ProactiveStats:
    pre_holds: int = 0
    resumes: int = 0
    released_cleared: int = 0
    released_timeout: int = 0
    released_imminent: int = 0
    rejected_low_confidence: int = 0
    rejected_stale: int = 0
    rejected_cooldown: int = 0
    rejected_peer_holding: int = 0
    not_holder: int = 0
    hold_ticks: int = 0
    repeat_holds_same_peer: int = 0
    last_peer: dict = field(default_factory=dict)


class ProactiveCoordinator:
    """Per-fleet bookkeeping; every decision is per robot, from that robot's
    own inbox view and its own predictions."""

    def __init__(self) -> None:
        self._holds: dict[str, _Hold] = {}
        self._cooldown: dict[tuple[str, str], int] = {}
        self.stats = ProactiveStats()
        self.events: list[dict] = []           # this tick's PRE-HOLD / RESUME events

    def begin_tick(self) -> None:
        self.events = []

    def holding(self, rid: str) -> Optional[_Hold]:
        return self._holds.get(rid)

    def _release(self, rid: str, now: int, why: str) -> None:
        h = self._holds.pop(rid, None)
        if h is None:
            return
        self._cooldown[tuple(sorted((rid, h.peer)))] = now + COOLDOWN_TICKS
        self.stats.resumes += 1
        if why == "cleared":
            self.stats.released_cleared += 1
        elif why == "timeout":
            self.stats.released_timeout += 1
        else:
            self.stats.released_imminent += 1
        self.events.append({"type": "RESUME", "robot": rid, "peer": h.peer, "tick": now,
                            "held_ticks": now - h.since, "reason": why})

    def decide(self, rid: str, me, views: dict, predictions: dict, now: int,
               threshold: float, *, imminent: bool) -> Optional[_Hold]:
        """Return the active pre-hold for `rid` this tick, or None.

        `predictions` maps peer id -> the robot's own latest Edge-AI output
        (dict with probability, confidence, tick, ttc_s). `imminent` is True
        when the reactive ladder already sees a peer inside CONFLICT_M; the
        ladder then owns the robot and any pre-hold is released.
        """
        h = self._holds.get(rid)
        if h is not None:
            if imminent:
                self._release(rid, now, "imminent")
                return None
            held = now - h.since
            pred = predictions.get(h.peer)
            fresh = pred is not None and now - pred["tick"] <= STALE_TICKS
            still = fresh and pred["probability"] >= OFF_RATIO * threshold
            if held >= MAX_HOLD_TICKS:
                self._release(rid, now, "timeout")
                return None
            if held >= MIN_HOLD_TICKS and not still:
                self._release(rid, now, "cleared")
                return None
            self.stats.hold_ticks += 1
            return h
        if imminent:
            return None
        best = None
        for pid in sorted(predictions):
            pred = predictions[pid]
            if not pred["conflict"]:
                continue
            if now - pred["tick"] > STALE_TICKS:
                self.stats.rejected_stale += 1
                continue
            if pred["confidence"] < CONF_MIN:
                self.stats.rejected_low_confidence += 1
                continue
            view = views.get(pid)
            if view is None:
                continue
            if view.holding:
                self.stats.rejected_peer_holding += 1
                continue
            if self._cooldown.get(tuple(sorted((rid, pid))), -1) > now:
                self.stats.rejected_cooldown += 1
                continue
            if holder(me, view.state) != rid:
                self.stats.not_holder += 1
                continue
            if best is None or pred["probability"] > best[1]["probability"]:
                best = (pid, pred)
        if best is None:
            return None
        pid, pred = best
        h = _Hold(peer=pid, since=now, probability=pred["probability"],
                  confidence=pred["confidence"], ttc_s=pred.get("ttc_s"))
        self._holds[rid] = h
        self.stats.pre_holds += 1
        if self.stats.last_peer.get(rid) == pid:
            self.stats.repeat_holds_same_peer += 1
        self.stats.last_peer[rid] = pid
        self.events.append({"type": "PRE-HOLD", "robot": rid, "peer": pid, "tick": now,
                            "probability": round(pred["probability"], 4),
                            "confidence": round(pred["confidence"], 4),
                            "ttc_s": pred.get("ttc_s"), "horizon_ticks": pred.get("horizon_ticks"),
                            "model": pred.get("model")})
        return h

    def forget(self, rid: str) -> None:
        self._holds.pop(rid, None)

    def summary(self) -> dict:
        s = self.stats
        return {k: v for k, v in s.__dict__.items() if k != "last_peer"}
