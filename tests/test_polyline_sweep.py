"""F1: the safety check tests the path a step really drives, not only its chord.

docs/C2_ROOT_CAUSE_ANALYSIS.md RC2 (evidence row RC2 names the traced run).
The geometry below is that trace: the chord cleared the 0.75 m floor by 6 mm,
the real L-shaped motion ended 0.735 m from a stationary peer and froze the
pair.
"""

from __future__ import annotations

import math
import random

from app.coordination.swarm_policy import HARD_STOP_M, MAX_STEP_M
from app.sim.policy import _segment_distance as seg
from app.sim.robot import SimRobot
from app.sim.sweep import build_sweep, is_point, path_polyline, point_sweep, sweep_distance

HERE = (30.456, 27.5)
PATH = [(30.5, 27.5), (30.5, 0.5)]
PEER = (31.235, 27.5)


def test_sweep_always_contains_the_old_chord():
    end = (30.509, 27.287)
    s = build_sweep(HERE, end, PATH, MAX_STEP_M, 1.0)
    assert s[0] == (HERE, end)
    half = build_sweep(HERE, end, PATH, MAX_STEP_M, 0.5)
    assert half[0][1] == (HERE[0] + (end[0] - HERE[0]) * 0.5, HERE[1] + (end[1] - HERE[1]) * 0.5)


def test_traced_corner_case_is_caught():
    end = (30.509, 27.287)                    # the old kernel's chord endpoint
    chord_gap = seg((HERE, end), (PEER, PEER))
    assert chord_gap >= HARD_STOP_M           # the old test let it through ...
    s = build_sweep(HERE, end, PATH, MAX_STEP_M, 1.0)
    assert sweep_distance(s, point_sweep(PEER), seg) < HARD_STOP_M   # ... F1 does not


def test_sweep_is_never_less_strict_than_the_chord():
    rng = random.Random(7)
    for _ in range(2000):
        here = (rng.uniform(0, 5), rng.uniform(0, 5))
        wps = [(rng.uniform(0, 5), rng.uniform(0, 5)) for _ in range(3)]
        end = path_polyline(here, wps, MAX_STEP_M)[-1]
        other = point_sweep((rng.uniform(0, 5), rng.uniform(0, 5)))
        for scale in (1.0, 0.75, 0.5, 0.25):
            s = build_sweep(here, end, wps, MAX_STEP_M, scale)
            assert sweep_distance(s, other, seg) <= seg(s[0], other[0]) + 1e-12


def test_real_robot_motion_stays_inside_its_sweep():
    """Drive a SimRobot one tick at full speed around random corners: every
    point it occupies lies on the polyline legs of its sweep."""
    rng = random.Random(11)
    from app.sim.robot import FLEET_MIX
    for trial in range(300):
        spec = FLEET_MIX[trial % len(FLEET_MIX)]
        r = SimRobot(robot_id="R001", spec=spec, x=5.0, y=5.0)
        wps = [(5.0 + rng.choice((-1, 1)) * rng.uniform(0.01, 0.3), 5.0)]
        wps.append((wps[0][0], 5.0 + rng.choice((-1, 1)) * 3.0))
        r.assign_path(list(wps), intent_id="I", target=wps[-1])
        r.velocity = spec.max_speed_mps
        r.speed_scale = 1.0
        here = (r.x, r.y)
        s = build_sweep(here, here, wps, MAX_STEP_M, 1.0)
        from app.sim.sensing import SensingProfile
        r.step(0.1, random.Random(0), SensingProfile())
        after = (r.x, r.y)
        d = min(seg(leg, (after, after)) for leg in s[1:]) if len(s) > 1 else math.dist(here, after)
        assert d < 1e-6, (trial, here, wps, after)


def test_point_sweep_helpers():
    assert is_point(point_sweep((1.0, 2.0)))
    assert not is_point(build_sweep((0.0, 0.0), (0.2, 0.0), [(1.0, 0.0)], MAX_STEP_M, 1.0))
