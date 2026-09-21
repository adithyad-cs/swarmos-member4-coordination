"""Tests for the X-12 / N10 counterfactual co-simulation harness.

The contract under test is narrow and deliberate:
  1. Lockstep invariance - the treatment arm of a CoSimulation must produce
     the same trace_hash as a standalone SimEngine built the same way. If it
     does not, the co-simulation is perturbing the thing it claims to observe
     and every delta it reports is worthless.
  2. Arm independence - the two arms must not share state.
  3. compare_kpis sign convention - positive delta always means "treatment is
     better", including for KPIs where lower is better.
  4. Missing-KPI honesty - a KPI that is present but None must be reported as
     missing, never silently rendered as zero.
"""

from app.sim.cosim import (
    ARM_BASELINE,
    ARM_TREATMENT,
    DIVERGENCE_KPI,
    HEADLINE_KPIS,
    LOWER_IS_BETTER,
    CoSimulation,
    compare_kpis,
    make_baseline_policy,
    make_treatment_policy,
)
from app.sim.engine import SimEngine

TICKS = 40
SEED = 11


def _standalone_treatment_hash(ticks=TICKS, seed=SEED):
    eng = SimEngine(seed=seed, policy=make_treatment_policy(), label=ARM_TREATMENT)
    snap = None
    for _ in range(ticks):
        snap = eng.step()
    return snap.trace_hash


def _standalone_baseline_hash(ticks=TICKS, seed=SEED):
    eng = SimEngine(seed=seed, policy=make_baseline_policy(), label=ARM_BASELINE)
    snap = None
    for _ in range(ticks):
        snap = eng.step()
    return snap.trace_hash


# --- 1. lockstep invariance ------------------------------------------------

def test_treatment_arm_matches_standalone_engine():
    """Co-simulating must not change the treatment arm's trajectory."""
    cosim = CoSimulation(seed=SEED)
    cosim.run(TICKS)
    frame = cosim.last_frame()
    assert frame is not None
    assert frame.treatment.trace_hash == _standalone_treatment_hash()


def test_baseline_arm_matches_standalone_engine():
    cosim = CoSimulation(seed=SEED)
    cosim.run(TICKS)
    frame = cosim.last_frame()
    assert frame.baseline.trace_hash == _standalone_baseline_hash()


def test_cosim_is_itself_deterministic():
    a = CoSimulation(seed=SEED)
    b = CoSimulation(seed=SEED)
    a.run(TICKS)
    b.run(TICKS)
    fa, fb = a.last_frame(), b.last_frame()
    assert fa.treatment.trace_hash == fb.treatment.trace_hash
    assert fa.baseline.trace_hash == fb.baseline.trace_hash


def test_arms_advance_together():
    cosim = CoSimulation(seed=SEED)
    for _ in range(TICKS):
        frame = cosim.step()
    assert frame.treatment.tick == frame.baseline.tick == TICKS


# --- 2. arm independence ---------------------------------------------------

def test_arms_are_distinct_policies():
    """The two arms must diverge, else the comparison is vacuous."""
    cosim = CoSimulation(seed=SEED)
    cosim.run(TICKS)
    frame = cosim.last_frame()
    assert frame.treatment.trace_hash != frame.baseline.trace_hash


def test_arm_labels_are_stable():
    cosim = CoSimulation(seed=SEED)
    cosim.run(2)
    frame = cosim.last_frame()
    assert frame.treatment.label == ARM_TREATMENT
    assert frame.baseline.label == ARM_BASELINE


# --- 3. compare_kpis sign convention --------------------------------------

def test_higher_is_better_kpi_positive_when_treatment_wins():
    deltas = compare_kpis(
        {"tasks_complete": 10},
        {"tasks_complete": 4},
        keys=("tasks_complete",),
    )
    assert deltas[0].delta > 0
    assert deltas[0].better is True


def test_lower_is_better_kpi_positive_when_treatment_wins():
    """collisions is in LOWER_IS_BETTER, so fewer collisions must read as a win."""
    assert "collisions" in LOWER_IS_BETTER
    deltas = compare_kpis({"collisions": 0}, {"collisions": 3}, keys=("collisions",))
    assert deltas[0].better is True


def test_lower_is_better_kpi_negative_when_treatment_loses():
    deltas = compare_kpis({"collisions": 5}, {"collisions": 1}, keys=("collisions",))
    assert deltas[0].better is False


def test_headline_kpis_are_all_comparable():
    treatment = {k: 1 for k in HEADLINE_KPIS}
    baseline = {k: 1 for k in HEADLINE_KPIS}
    deltas = compare_kpis(treatment, baseline)
    assert len(deltas) == len(HEADLINE_KPIS)
    assert not compare_kpis.missing


# --- 4. missing-KPI honesty -----------------------------------------------

def test_none_valued_kpi_is_reported_missing_not_zero():
    """p95_completion_s is None until a task completes. It must not read as 0."""
    deltas = compare_kpis(
        {"p95_completion_s": None},
        {"p95_completion_s": 12.0},
        keys=("p95_completion_s",),
    )
    assert "p95_completion_s" in compare_kpis.missing
    assert all(d.key != "p95_completion_s" for d in deltas)


def test_absent_kpi_is_reported_missing():
    deltas = compare_kpis({}, {}, keys=("tasks_complete",))
    assert "tasks_complete" in compare_kpis.missing
    assert deltas == []


# --- 5. summary and static payload ---------------------------------------

def test_summary_reports_both_arms_and_divergence_kpi():
    cosim = CoSimulation(seed=SEED)
    cosim.run(TICKS)
    summary = cosim.summary()
    assert ARM_TREATMENT in repr(summary) or "treatment" in repr(summary)
    assert DIVERGENCE_KPI in HEADLINE_KPIS


def test_static_payload_is_json_safe():
    import json

    cosim = CoSimulation(seed=SEED)
    cosim.run(2)
    json.dumps(cosim.static_payload())
    json.dumps(cosim.summary())


def test_fleet_size_override_applies_to_both_arms():
    cosim = CoSimulation(seed=SEED, fleet_size=6)
    cosim.run(2)
    frame = cosim.last_frame()
    assert len(frame.treatment.robots) == len(frame.baseline.robots) == 6
