"""SWARMOS M4 - bounded predictive conflict lookahead.

A research-inspired bounded predictive coordination layer, NOT a new MAPF
algorithm. Predicting spatio-temporal overlap from announced plans is standard
practice (space-time reservation, temporal plan graphs); what this module adds
to SWARMOS is doing it DECENTRALIZED, per robot, on the intents peers already
broadcast within radio range - no new messages, no global view.

Each robot's broadcast AMRState carries its full remaining path and ETA
(`movement_intent`). Given two such states we sample both robots forward for
`horizon` ticks along their announced paths and report the first tick at which
their predicted separation drops below `threshold_m`.

The time model is deliberately simple and stated: each robot advances along
its own path at `max(current speed, min_speed_mps)`. It ignores future holds
and accelerations, so predictions are approximations - which is why their
precision and recall are MEASURED (engine prediction scoring) rather than
assumed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from app.sim.clock import TICK_SECONDS

Point = tuple[float, float]

DEFAULT_HORIZON_TICKS = 15
# Average driving speed measured for a lone nominal robot on the standard
# floor (0.59 m/s over 300 s, accelerations and turns included). Used when a
# robot is currently stopped, so a parked robot with a plan is still predicted
# to move rather than to stay put forever.
MIN_SPEED_MPS = 0.6


@dataclass(frozen=True)
class PredictedConflict:
    """One predicted encounter between `robot` and `peer`."""

    robot: str
    peer: str
    lead_ticks: int              # ticks from now until predicted separation < threshold
    min_dist_m: float            # smallest predicted separation within the horizon
    at: Point                    # midpoint of the pair at the predicted tick
    heading_cos: float           # cos of the angle between the two motion directions
    overlap_ticks: int           # predicted ticks inside the threshold
    horizon: int

    @property
    def geometry(self) -> str:
        if self.heading_cos <= -0.7:
            return "head-on"
        if self.heading_cos >= 0.7:
            return "same-direction"
        return "crossing"

    def as_dict(self) -> dict:
        return {
            "robot": self.robot,
            "peer": self.peer,
            "lead_ticks": self.lead_ticks,
            "min_dist_m": round(self.min_dist_m, 3),
            "at": [round(self.at[0], 2), round(self.at[1], 2)],
            "geometry": self.geometry,
            "heading_cos": round(self.heading_cos, 3),
            "overlap_ticks": self.overlap_ticks,
            "horizon": self.horizon,
        }


def _waypoints(state) -> list[Point]:
    here = (state.position.x, state.position.y)
    intent = getattr(state, "movement_intent", None)
    if intent is None or not intent.path:
        return [here]
    return [here] + [(p.x, p.y) for p in intent.path]


def trajectory(state, horizon: int, *, min_speed_mps: float = MIN_SPEED_MPS
               ) -> list[Point]:
    """Predicted positions at ticks 1..horizon along the announced path."""
    pts = _waypoints(state)
    speed = max(float(state.velocity or 0.0), min_speed_mps)
    step = speed * TICK_SECONDS
    out: list[Point] = []
    seg = 0
    pos = pts[0]
    for _ in range(horizon):
        remaining = step
        while remaining > 0.0 and seg < len(pts) - 1:
            nxt = pts[seg + 1]
            d = math.dist(pos, nxt)
            if d <= remaining:
                pos = nxt
                remaining -= d
                seg += 1
            else:
                f = remaining / d
                pos = (pos[0] + (nxt[0] - pos[0]) * f, pos[1] + (nxt[1] - pos[1]) * f)
                remaining = 0.0
        out.append(pos)
    return out


def _direction(traj: list[Point], start: Point) -> Optional[Point]:
    end = traj[-1] if traj else start
    dx, dy = end[0] - start[0], end[1] - start[1]
    n = math.hypot(dx, dy)
    if n < 1e-6:
        return None
    return (dx / n, dy / n)


def predict_pair(me, peer, *, horizon: int = DEFAULT_HORIZON_TICKS,
                 threshold_m: float, min_speed_mps: float = MIN_SPEED_MPS
                 ) -> Optional[PredictedConflict]:
    """First predicted breach of `threshold_m` between two broadcast states.

    Returns None when the pair is predicted to stay apart for the whole
    horizon, and also when it is ALREADY inside the threshold now - that is an
    actual conflict, not a prediction, and the reactive ladder owns it.
    """
    here = (me.position.x, me.position.y)
    there = (peer.position.x, peer.position.y)
    if math.dist(here, there) < threshold_m:
        return None
    reach = 2 * horizon * max(MIN_SPEED_MPS, 2.0) * TICK_SECONDS + threshold_m
    if math.dist(here, there) > reach:
        return None
    a = trajectory(me, horizon, min_speed_mps=min_speed_mps)
    b = trajectory(peer, horizon, min_speed_mps=min_speed_mps)
    first: Optional[int] = None
    best = float("inf")
    at = here
    inside = 0
    for k in range(horizon):
        d = math.dist(a[k], b[k])
        if d < best:
            best = d
        if d < threshold_m:
            inside += 1
            if first is None:
                first = k + 1
                at = ((a[k][0] + b[k][0]) / 2.0, (a[k][1] + b[k][1]) / 2.0)
    if first is None:
        return None
    da, db = _direction(a, here), _direction(b, there)
    cos = (da[0] * db[0] + da[1] * db[1]) if (da and db) else 0.0
    return PredictedConflict(
        robot=me.robot_id, peer=peer.robot_id, lead_ticks=first, min_dist_m=best,
        at=at, heading_cos=cos, overlap_ticks=inside, horizon=horizon,
    )
