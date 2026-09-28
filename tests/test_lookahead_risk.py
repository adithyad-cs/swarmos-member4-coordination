"""Bounded predictive lookahead and the explainable risk score."""

from __future__ import annotations

from app.coordination.lookahead import predict_pair, trajectory
from app.coordination.models import AMRState, MovementIntent, Position, RobotStatus
from app.coordination.risk import WEIGHTS, band_of, score
from app.coordination.swarm_policy import CONFLICT_M, SwarmPolicy
from app.sim.engine import SimEngine
from app.sim.prediction import PREDICT_THRESHOLD_M
from app.sim.scenarios import get_scenario


def _state(rid, x, y, path, v=1.0):
    return AMRState(
        robot_id=rid, timestamp=0.0, position=Position(x=x, y=y), velocity=v,
        heading=0.0, status=RobotStatus.MOVING, battery=90.0,
        movement_intent=MovementIntent(
            target=Position(x=path[-1][0], y=path[-1][1]),
            path=[Position(x=px, y=py) for px, py in path],
            intent_id="I1", path_version=1,
        ),
    )


def test_threshold_matches_the_ladder_conflict_band():
    assert PREDICT_THRESHOLD_M == CONFLICT_M


def test_trajectory_advances_at_speed_along_the_path():
    s = _state("R001", 0.0, 0.0, [(10.0, 0.0)], v=1.0)
    pts = trajectory(s, 10)
    assert abs(pts[-1][0] - 1.0) < 1e-9       # 10 ticks x 0.1 s x 1 m/s


def test_head_on_is_predicted_with_the_expected_lead():
    a = _state("R001", 0.0, 0.5, [(10.0, 0.5)], v=1.0)
    b = _state("R002", 4.0, 0.5, [(-10.0, 0.5)], v=1.0)
    pc = predict_pair(a, b, horizon=30, threshold_m=CONFLICT_M)
    assert pc is not None
    # gap closes at 2 m/s from 4.0 m; below 0.97 m after (4.0-0.97)/0.2 = 15.15 ticks
    assert pc.lead_ticks == 16
    assert pc.geometry == "head-on"


def test_parallel_convoy_is_not_a_conflict():
    a = _state("R001", 0.0, 0.5, [(20.0, 0.5)], v=1.0)
    b = _state("R002", 2.0, 0.5, [(22.0, 0.5)], v=1.0)
    assert predict_pair(a, b, horizon=15, threshold_m=CONFLICT_M) is None


def test_crossing_is_detected_as_crossing():
    a = _state("R001", 0.0, 2.0, [(4.0, 2.0)], v=1.0)
    b = _state("R002", 2.0, 0.0, [(2.0, 4.0)], v=1.0)
    pc = predict_pair(a, b, horizon=30, threshold_m=CONFLICT_M)
    assert pc is not None and pc.geometry == "crossing"


def test_already_inside_is_an_actual_conflict_not_a_prediction():
    a = _state("R001", 0.0, 0.5, [(10.0, 0.5)])
    b = _state("R002", 0.5, 0.5, [(-10.0, 0.5)])
    assert predict_pair(a, b, horizon=15, threshold_m=CONFLICT_M) is None


def test_risk_is_deterministic_banded_and_explainable():
    a = _state("R001", 0.0, 0.5, [(10.0, 0.5)], v=1.0)
    b = _state("R002", 3.0, 0.5, [(-10.0, 0.5)], v=1.0)
    pc = predict_pair(a, b, horizon=15, threshold_m=CONFLICT_M)
    r1 = score(pc, threshold_m=CONFLICT_M, in_corridor=True)
    r2 = score(pc, threshold_m=CONFLICT_M, in_corridor=True)
    assert r1 == r2
    assert set(r1.terms) == set(WEIGHTS)
    assert abs(r1.score - sum(WEIGHTS[k] * v for k, v in r1.terms.items())) < 1e-9
    open_floor = score(pc, threshold_m=CONFLICT_M, in_corridor=False)
    assert r1.score > open_floor.score
    assert band_of(0.85) == "CRITICAL" and band_of(0.1) == "LOW"


def test_observe_only_lookahead_does_not_change_the_run():
    scen = get_scenario("rush_50")
    scen = type(scen)(**{**scen.__dict__, "fleet_size": 12})
    off = SimEngine(scen, seed=11, policy=SwarmPolicy())
    on = SimEngine(scen, seed=11, policy=SwarmPolicy(lookahead_h=15))
    off.run(400)
    on.run(400)
    assert on.trace_hash == off.trace_hash
    summary = on.kpis()["lookahead"]
    assert summary["prediction_episodes"] > 0
    assert summary["actual_conflicts"] > 0
    assert summary["true_positives"] + summary["false_negatives"] == summary["actual_conflicts"]
