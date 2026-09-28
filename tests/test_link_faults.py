"""LINK_IMPAIR and ZONE_PARTITION must change what the radio delivers.

Before this fix both faults only wrote a dict that nothing read: the radio
stayed at LINK_PERFECT, the trace hash of an "impaired" run was identical to a
clean one, and the Lab offered a button that did nothing. These tests fail on
that code and pass on the wired version.
"""

from __future__ import annotations

from app.api.runner import _make_policy
from app.coordination.radio import LINK_PERFECT
from app.sim.engine import SimEngine
from app.sim.scenarios import get_scenario

TICKS = 200


def _engine(fleet: int = 16, seed: int = 11) -> SimEngine:
    scen = get_scenario("rush_50")
    scen = type(scen)(**{**scen.__dict__, "fleet_size": fleet})
    return SimEngine(scen, seed=seed, policy=_make_policy("swarmos", seed),
                     label="swarmos")


def _delivery_ratio(eng: SimEngine) -> float:
    s = eng.policy.radio.stats
    attempted = s.delivered + s.dropped
    return s.delivered / attempted if attempted else 1.0


def test_link_impair_reaches_the_radio_and_changes_the_run():
    clean = _engine()
    clean.run(TICKS)

    lossy = _engine()
    detail = lossy.inject("LINK_IMPAIR", drop_pct=50.0, latency_ms=0.0)
    assert detail["applied"] is True
    assert lossy.policy.radio.profile.loss_pct == 50.0
    lossy.run(TICKS)

    assert lossy.policy.radio.stats.dropped > 0
    assert _delivery_ratio(lossy) < 0.7 < _delivery_ratio(clean)
    assert lossy.trace_hash != clean.trace_hash


def test_latency_is_quantised_to_whole_ticks_and_jitter_is_declared():
    eng = _engine()
    detail = eng.inject("LINK_IMPAIR", drop_pct=0.0, latency_ms=500.0)
    assert detail["latency_ticks"] == 5
    assert eng.policy.radio.profile.latency_ticks == 5
    assert detail["jitter_modelled"] is False


def test_timed_link_impairment_restores_itself():
    eng = _engine()
    eng.inject("LINK_IMPAIR", drop_pct=100.0, latency_ms=0.0, ticks=30)
    eng.run(10)
    assert eng.policy.radio.profile.loss_pct == 100.0
    eng.run(30)
    assert eng.policy.radio.profile == LINK_PERFECT
    assert "drop_pct" not in eng.impairment


def test_zone_partition_drops_only_hops_that_cross_the_boundary():
    eng = _engine()
    detail = eng.inject("ZONE_PARTITION", zone="EAST", ticks=100)
    assert detail["applied"] is True
    radio = eng.policy.radio
    assert radio.partition is not None
    before = radio.stats.dropped
    eng.run(50)
    assert radio.stats.dropped > before
    eng.run(60)
    assert radio.partition is None


def test_unknown_partition_zone_is_refused_not_faked():
    eng = _engine()
    detail = eng.inject("ZONE_PARTITION", zone="NOWHERE")
    assert detail["applied"] is False
    assert "EAST" in detail["zones"]


def test_baseline_has_no_radio_and_says_so():
    scen = get_scenario("rush_50")
    eng = SimEngine(scen, seed=11, policy=_make_policy("baseline", 11))
    detail = eng.inject("LINK_IMPAIR", drop_pct=30.0)
    assert detail["applied"] is False
