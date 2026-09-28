"""Edge-AI features: what ONE robot can compute about ONE peer, at runtime.

Every feature below comes from information the robot actually has on board:
its own state, the peer's last BROADCAST state and message freshness from its
own radio inbox, its own ladder bookkeeping, and the static floor plan it
carries (attach_map). Nothing reads another robot's true state and nothing
reads the engine. The same function is used to build the training dataset
(tools/edge_ai_dataset.py) and to feed the runtime model, so the model sees at
inference exactly the features it was trained on.

Pure Python, no third-party imports: this runs inside the per-robot decision
loop, on an edge device.

| feature | unit | source | preprocessing |
|---|---|---|---|
| dist_m | m | own position, peer broadcast position | clipped to [0, RADIUS_M] |
| closing_mps | m/s | both velocities and headings | +ve = gap shrinking; clipped [-4, 4] |
| heading_cos | - | both headings | cos of angle between travel directions |
| tcpa_s | s | constant-velocity closest approach | clipped [0, TCPA_CAP_S]; cap if diverging |
| dcpa_m | m | same | clipped [0, RADIUS_M] |
| la_min_m | m | both broadcast intents, sampled H ticks | min predicted separation, clipped |
| la_lead_ticks | ticks | same | first tick below CONFLICT_M; H+1 if none |
| my_speed / peer_speed | m/s | own / broadcast velocity | raw |
| my_remaining_m / peer_remaining_m | m | own / broadcast intent path length | clipped [0, 30] |
| neighbours_3m | count | own inbox positions | robots within 3 m |
| peer_holding | 0/1 | peer broadcast `holding` bit | raw |
| msg_age_ticks | ticks | inbox heard_tick vs now | clipped [0, 10] |
| my_yield_streak / peer_yield_streak | ticks | own ladder / broadcast | clipped [0, 30] |
| my_free_nbrs | count | static map at own cell | 4-neighbours navigable (2 = single-file) |
| path_overlap | cells | both intents, next OVERLAP_CELLS cells | shared cell count |
| my_has_task / peer_has_task | 0/1 | own / broadcast current_task_id | raw |
"""

from __future__ import annotations

import math
from typing import Optional

from app.coordination.lookahead import trajectory

RADIUS_M = 6.0          # peers farther than this are not scored at all
FEATURE_LOOKAHEAD_H = 15  # horizon of the analytic la_* features (fixed; the model's own horizon is separate)
TCPA_CAP_S = 5.0
OVERLAP_CELLS = 10
TICK_S = 0.1

FEATURE_NAMES = (
    "dist_m", "closing_mps", "heading_cos", "tcpa_s", "dcpa_m",
    "la_min_m", "la_lead_ticks", "my_speed", "peer_speed",
    "my_remaining_m", "peer_remaining_m", "neighbours_3m", "peer_holding",
    "msg_age_ticks", "my_yield_streak", "peer_yield_streak", "my_free_nbrs",
    "path_overlap", "my_has_task", "peer_has_task",
)


def _vel(state) -> tuple[float, float]:
    v = float(state.velocity or 0.0)
    h = float(state.heading or 0.0)
    return (v * math.cos(h), v * math.sin(h))


def _remaining(state) -> float:
    intent = state.movement_intent
    if intent is None or not intent.path:
        return 0.0
    x, y = state.position.x, state.position.y
    total = 0.0
    for p in intent.path:
        total += math.hypot(p.x - x, p.y - y)
        x, y = p.x, p.y
    return total


def _cells(state, n: int) -> list[tuple[int, int]]:
    """Grid cells along the announced path, one per metre, first n."""
    intent = state.movement_intent
    out: list[tuple[int, int]] = []
    x, y = state.position.x, state.position.y
    if intent is None or not intent.path:
        return [(int(x), int(y))]
    for p in intent.path:
        seg = math.hypot(p.x - x, p.y - y)
        steps = max(1, int(seg))
        for k in range(1, steps + 1):
            cx = int(x + (p.x - x) * k / steps)
            cy = int(y + (p.y - y) * k / steps)
            if not out or out[-1] != (cx, cy):
                out.append((cx, cy))
            if len(out) >= n:
                return out
        x, y = p.x, p.y
    return out


def free_neighbours(warehouse, x: float, y: float) -> int:
    if warehouse is None:
        return 4
    cx, cy = warehouse.m_to_cell(x, y)
    return sum(1 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
               if warehouse.is_navigable(cx + dx, cy + dy))


def pair_features(me, view, *, now_tick: int, inbox_positions, my_yield_streak: int,
                  warehouse, horizon: int, conflict_m: float) -> Optional[list[float]]:
    """Feature vector for (me -> peer), or None if the peer is out of range
    or already inside the conflict threshold (an actual conflict is the
    reactive ladder's job, not a prediction)."""
    peer = view.state
    ax, ay = me.position.x, me.position.y
    bx, by = peer.position.x, peer.position.y
    dist = math.hypot(bx - ax, by - ay)
    if dist > RADIUS_M or dist < conflict_m:
        return None
    va, vb = _vel(me), _vel(peer)
    rx, ry = bx - ax, by - ay
    rvx, rvy = vb[0] - va[0], vb[1] - va[1]
    closing = -((rx * rvx + ry * rvy) / dist) if dist > 1e-9 else 0.0
    rv2 = rvx * rvx + rvy * rvy
    if rv2 < 1e-9:
        tcpa, dcpa = TCPA_CAP_S, dist
    else:
        t = -(rx * rvx + ry * rvy) / rv2
        if t <= 0:
            tcpa, dcpa = TCPA_CAP_S, dist
        else:
            tcpa = min(t, TCPA_CAP_S)
            dcpa = math.hypot(rx + rvx * tcpa, ry + rvy * tcpa)
    na, nb = math.hypot(*va), math.hypot(*vb)
    if na > 1e-6 and nb > 1e-6:
        hcos = (va[0] * vb[0] + va[1] * vb[1]) / (na * nb)
    else:
        hcos = math.cos(float(me.heading or 0.0) - float(peer.heading or 0.0))
    ta = trajectory(me, horizon)
    tb = trajectory(peer, horizon)
    la_min, la_lead = float("inf"), horizon + 1
    for k in range(horizon):
        d = math.hypot(ta[k][0] - tb[k][0], ta[k][1] - tb[k][1])
        if d < la_min:
            la_min = d
        if d < conflict_m and la_lead == horizon + 1:
            la_lead = k + 1
    near = sum(1 for (px, py) in inbox_positions
               if math.hypot(px - ax, py - ay) <= 3.0)
    ca, cb = _cells(me, OVERLAP_CELLS), set(_cells(peer, OVERLAP_CELLS))
    overlap = sum(1 for c in ca if c in cb)
    return [
        min(dist, RADIUS_M),
        max(-4.0, min(4.0, closing)),
        hcos,
        tcpa,
        min(dcpa, RADIUS_M),
        min(la_min, RADIUS_M),
        float(la_lead),
        float(me.velocity or 0.0),
        float(peer.velocity or 0.0),
        min(_remaining(me), 30.0),
        min(_remaining(peer), 30.0),
        float(near),
        1.0 if view.holding else 0.0,
        float(max(0, min(10, now_tick - view.heard_tick))),
        float(min(30, my_yield_streak)),
        float(min(30, view.yield_streak)),
        float(free_neighbours(warehouse, ax, ay)),
        float(overlap),
        1.0 if me.current_task_id else 0.0,
        1.0 if peer.current_task_id else 0.0,
    ]
