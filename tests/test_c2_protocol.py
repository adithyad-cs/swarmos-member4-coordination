"""Guards for the frozen C2 protocol (docs/C2_FROZEN_PROTOCOL.md).

These pin the conditions the headline comparison depends on, so a later edit
cannot silently change them: one safety rule for every arm, the headline
SWARMOS configuration, one workload for every arm, and evaluation seeds that
were never used in development.
"""

from __future__ import annotations

import glob
import json
import os
import re

from app.api.runner import BASELINE_STUCK_TICKS, _make_policy
from app.coordination.swarm_policy import HARD_STOP_M, SwarmPolicy
from app.sim.engine import SimEngine
from app.sim.policy import StopAndWaitPolicy, TextbookStopAndWaitPolicy
from app.sim.scenarios import get_scenario
from tools.run_experiment import C2_EVAL_SEEDS, DEFAULT_SEEDS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_every_arm_uses_the_same_safety_floor():
    assert StopAndWaitPolicy.SAFE_SEPARATION_M == HARD_STOP_M == 0.75
    assert TextbookStopAndWaitPolicy.SAFE_SEPARATION_M == HARD_STOP_M


def test_headline_arms_are_configured_as_the_protocol_states():
    sw = _make_policy("swarmos", 1)
    assert isinstance(sw, SwarmPolicy)
    assert sw.separating_exemption is False       # never in the headline
    assert sw.mutual_hold_break is False
    assert sw.traffic_rules_enabled is False
    assert sw.perception_fallback is True
    assert TextbookStopAndWaitPolicy.STUCK_TICKS == 30
    assert type(_make_policy("stop_and_wait", 1)) is TextbookStopAndWaitPolicy
    assert _make_policy("baseline", 1).STUCK_TICKS == BASELINE_STUCK_TICKS == 8


def test_workload_and_fleet_are_identical_across_arms():
    spec = get_scenario("overlap_batch")
    seen = []
    for arm in ("stop_and_wait", "baseline", "swarmos"):
        eng = SimEngine(spec, seed=501, policy=_make_policy(arm, 1))
        tasks = [(t.task_id, t.pick, t.drop, t.priority.value, t.payload_kg, t.created_s)
                 for t in eng.tasks.values()]
        fleet = [(r.robot_id, round(r.x, 6), round(r.y, 6)) for r in
                 sorted(eng.robots.values(), key=lambda r: r.robot_id)]
        seen.append((tasks, fleet))
    assert seen[0] == seen[1] == seen[2]
    assert len(seen[0][0]) == spec.initial_burst and len(seen[0][1]) == spec.fleet_size


def test_evaluation_seeds_are_fresh():
    assert len(C2_EVAL_SEEDS) >= 30 and len(set(C2_EVAL_SEEDS)) == len(C2_EVAL_SEEDS)
    assert not set(C2_EVAL_SEEDS) & set(DEFAULT_SEEDS)
    pattern = re.compile(r"\b(9000[0-4]\d)\b")
    for path in glob.glob(os.path.join(ROOT, "tests", "*.py")) + \
            glob.glob(os.path.join(ROOT, "tools", "*.py")):
        if path.endswith(os.path.join("tools", "run_experiment.py")):
            continue                    # where C2_EVAL_SEEDS is defined
        with open(path) as fh:
            hits = {int(x) for x in pattern.findall(fh.read())} & set(C2_EVAL_SEEDS)
        assert not hits, (path, hits)
    for runs in glob.glob(os.path.join(ROOT, "reports", "experiments", "*", "runs.jsonl")):
        with open(runs) as fh:
            used = {json.loads(line)["seed"] for line in fh if line.strip()}
        # the frozen benchmark's own output is the only place they may appear
        if "c2_frozen" in runs:
            continue
        assert not used & set(C2_EVAL_SEEDS), runs


def test_development_seeds_are_disjoint_from_the_evaluation_seeds():
    from tools.run_experiment import DEV_SEEDS

    assert len(DEV_SEEDS) >= 20
    assert not set(DEV_SEEDS) & set(C2_EVAL_SEEDS)
    assert not set(DEV_SEEDS) & set(DEFAULT_SEEDS)


# -- C2 v2 (docs/C2_FROZEN_PROTOCOL_V2.md) -------------------------------------

V2_ARMS = ("stop_and_wait+F1+F6", "baseline+F1+F6", "swarmos+F1+F3+F5+F6")


def test_v2_evaluation_seeds_are_fresh_and_frozen():
    from tools.run_experiment import C2V2_EVAL_SEEDS, DEV_SEEDS

    base = 8 * 10 ** 5                  # written arithmetically so this file never names a seed
    assert C2V2_EVAL_SEEDS == tuple(range(base + 1, base + 41))
    assert not set(C2V2_EVAL_SEEDS) & (set(C2_EVAL_SEEDS) | set(DEV_SEEDS) | set(DEFAULT_SEEDS))
    pattern = re.compile(r"\b(8000[0-4]\d)\b")
    for path in glob.glob(os.path.join(ROOT, "tests", "*.py")) + \
            glob.glob(os.path.join(ROOT, "tools", "*.py")):
        if path.endswith(os.path.join("tools", "run_experiment.py")):
            continue
        with open(path) as fh:
            hits = {int(x) for x in pattern.findall(fh.read())} & set(C2V2_EVAL_SEEDS)
        assert not hits, (path, hits)
    for runs in glob.glob(os.path.join(ROOT, "reports", "**", "runs.jsonl"), recursive=True):
        if "c2v2_frozen" in runs:
            continue                    # the frozen benchmark's own output
        with open(runs) as fh:
            used = {json.loads(line)["seed"] for line in fh if line.strip()}
        assert not used & set(C2V2_EVAL_SEEDS), runs


def test_v2_arms_share_the_safety_rule_and_swarmos_gets_no_relaxation():
    from tools.run_experiment import arm_config

    cfg = {a: arm_config(a) for a in V2_ARMS}
    for a in ("stop_and_wait+F1+F6", "baseline+F1+F6"):
        assert cfg[a]["POLYLINE_SWEEP"] is True                  # shared F1
        assert cfg[a]["engine_release_cooldown_ticks"] == 300    # shared F6
        assert cfg[a]["SAFE_SEPARATION_M"] == HARD_STOP_M
    assert cfg["stop_and_wait+F1+F6"]["STUCK_TICKS"] == 30
    assert cfg["baseline+F1+F6"]["STUCK_TICKS"] == 8
    sw = cfg["swarmos+F1+F3+F5+F6"]
    assert sw["polyline_sweep"] and sw["leader_rule"] and sw["standoff_breaker"]
    assert sw["engine_release_cooldown_ticks"] == 300
    assert sw["separating_exemption"] is False and sw["mutual_hold_break"] is False
    assert sw["traffic_rules_enabled"] is False
    assert sw["constants"]["HARD_STOP_M"] == HARD_STOP_M == 0.75


# -- C2 v3: product-default validation (docs/C2_FROZEN_PROTOCOL_V3.md) --------

V3_ARMS = ("stop_and_wait+F1+F6", "baseline+F1+F6", "swarmos")


def test_v3_evaluation_seeds_are_fresh_and_frozen():
    from tools.run_experiment import C2V2_EVAL_SEEDS, C2V3_EVAL_SEEDS, DEV_SEEDS

    base = 6 * 10 ** 5                  # arithmetic, so this file never names a seed
    assert C2V3_EVAL_SEEDS == tuple(range(base + 1, base + 41))
    earlier = set(C2_EVAL_SEEDS) | set(C2V2_EVAL_SEEDS) | set(DEV_SEEDS) | set(DEFAULT_SEEDS)
    assert not set(C2V3_EVAL_SEEDS) & earlier
    pattern = re.compile(r"\b(6000[0-4]\d)\b")
    for path in glob.glob(os.path.join(ROOT, "tests", "*.py")) + \
            glob.glob(os.path.join(ROOT, "tools", "*.py")):
        if path.endswith(os.path.join("tools", "run_experiment.py")):
            continue
        with open(path) as fh:
            hits = {int(x) for x in pattern.findall(fh.read())} & set(C2V3_EVAL_SEEDS)
        assert not hits, (path, hits)
    for runs in glob.glob(os.path.join(ROOT, "reports", "**", "runs.jsonl"), recursive=True):
        if "c2v3_frozen" in runs:
            continue                    # the frozen benchmark's own output
        with open(runs) as fh:
            used = {json.loads(line)["seed"] for line in fh if line.strip()}
        assert not used & set(C2V3_EVAL_SEEDS), runs


def test_product_default_is_the_evaluated_configuration():
    """The PRODUCT swarmos arm carries exactly F1+F3+F5+F6, F2 stays off,
    and the kernel floor is unchanged; references keep F1+F6."""
    from app.api.runner import PRODUCT_RELEASE_COOLDOWN_TICKS
    from tools.run_experiment import arm_config

    sw = arm_config("swarmos")
    assert sw["polyline_sweep"] and sw["leader_rule"] and sw["standoff_breaker"]
    assert sw["engine_release_cooldown_ticks"] == PRODUCT_RELEASE_COOLDOWN_TICKS == 300
    assert sw["separating_exemption"] is False and sw["mutual_hold_break"] is False
    assert sw["traffic_rules_enabled"] is False
    assert sw["constants"]["HARD_STOP_M"] == HARD_STOP_M == 0.75
    ev = arm_config("swarmos+F1+F3+F5+F6")
    keys = set(sw) - {"base", "fixes"}
    assert {k: sw[k] for k in keys} == {k: ev[k] for k in keys}
    for ref in ("stop_and_wait+F1+F6", "baseline+F1+F6"):
        c = arm_config(ref)
        assert c["POLYLINE_SWEEP"] is True and c["engine_release_cooldown_ticks"] == 300


def test_product_runtime_engines_apply_the_product_configuration():
    import asyncio

    from app.api.runner import RunConfig, RunManager

    async def check():
        mgr = RunManager()
        await mgr.start(RunConfig(scenario="overlap_batch", seed=1, policy="swarmos"))
        try:
            eng = mgr.engine
            assert eng.release_cooldown_ticks == 300
            assert eng.policy.polyline_sweep and eng.policy.leader_rule
            assert eng.policy.standoff_breaker
        finally:
            await mgr.stop()

    asyncio.run(check())
