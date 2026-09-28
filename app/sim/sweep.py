"""Swept-path geometry shared by the SWARMOS kernel and the stop-and-wait
baseline (F1, docs/C2_ROOT_CAUSE_ANALYSIS.md RC2).

Both safety checks used to test ONE straight chord from a robot's position to
where one tick of motion along its path ends. A robot does not drive that
chord: SimRobot.step chases path[0] in a straight line and then the next
waypoint, so when the path turns within the step the real trajectory is an L
and the chord cuts the corner. Traced on the frozen C2 run (seed 900018, tick
2799): chord gap 0.756 m, real gap 0.735 m; every one of 45 traced floor
entries was of this kind.

A Sweep here is a tuple of segments. It always CONTAINS the old chord, and
adds the legs of the real path within the step, so a floor test over a Sweep
("every segment clears the floor") is at least as strict as the old test over
the chord alone. It can only veto more, never less.
"""

from __future__ import annotations

import math
from typing import Optional

Point = tuple[float, float]
Segment = tuple[Point, Point]
Sweep = tuple[Segment, ...]


def point_sweep(p: Point) -> Sweep:
    return ((p, p),)


def is_point(sweep: Sweep) -> bool:
    first = sweep[0][0]
    return all(a == first and b == first for a, b in sweep)


def path_polyline(here: Point, waypoints, budget: float) -> list[Point]:
    """Points the robot passes through travelling `budget` metres along its
    waypoints from `here`, exactly as SimRobot.step chases them."""
    pts = [here]
    x, y = here
    left = max(0.0, budget)
    for wx, wy in waypoints:
        if left <= 1e-12:
            break
        dx, dy = wx - x, wy - y
        leg = math.hypot(dx, dy)
        if leg <= 1e-12:
            continue
        if leg <= left:
            x, y = wx, wy
            left -= leg
            pts.append((x, y))
            continue
        r = left / leg
        pts.append((x + dx * r, y + dy * r))
        left = 0.0
        break
    return pts


def truncate(pts: list[Point], length: float) -> list[Point]:
    """The first `length` metres of a polyline."""
    out = [pts[0]]
    left = max(0.0, length)
    for a, b in zip(pts, pts[1:]):
        if left <= 1e-12:
            break
        leg = math.dist(a, b)
        if leg <= left:
            out.append(b)
            left -= leg
            continue
        r = left / leg if leg > 0 else 0.0
        out.append((a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r))
        break
    return out


def build_sweep(here: Point, chord_end: Point, waypoints, step_m: float,
                scale: float) -> Sweep:
    """Chord (the old test, scaled exactly as before) UNION the real path legs
    for `scale * step_m` metres of travel."""
    scale = max(0.0, min(1.0, scale))
    chord = (here, (here[0] + (chord_end[0] - here[0]) * scale,
                    here[1] + (chord_end[1] - here[1]) * scale))
    poly = truncate(path_polyline(here, waypoints, step_m), scale * step_m)
    legs = tuple((a, b) for a, b in zip(poly, poly[1:]) if a != b)
    return (chord,) + legs


def sweep_distance(a: Sweep, b: Sweep, seg_dist) -> float:
    return min(seg_dist(p, q) for p in a for q in b)


def waypoints_of(state) -> list[Point]:
    intent = getattr(state, "movement_intent", None)
    if intent is None or not intent.path:
        return []
    return [(p.x, p.y) for p in intent.path]
