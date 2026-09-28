"""Guards for the frozen advanced-intelligence evaluation
(docs/ADVANCED_FROZEN_PROTOCOL_V1.md): fresh seeds, the product default
unchanged, observe-only Edge AI provably inert, independent flags."""

from __future__ import annotations

import glob
import json
import os
import re

from app.product import ADVANCED_FLAGS, PRODUCT_ADVANCED, describe_policy, make_swarmos_policy
from app.sim.engine import SimEngine
from app.sim.scenarios import get_scenario

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_advanced_evaluation_seeds_are_fresh_and_frozen():
    from tools.run_experiment import (ADV_DEV_SEEDS, ADV_EVAL_SEEDS, C2_EVAL_SEEDS,
                                      C2V2_EVAL_SEEDS, C2V3_EVAL_SEEDS, DEV_SEEDS)

    base = 14 * 10 ** 5                  # arithmetic, so this file never names a seed
    assert ADV_EVAL_SEEDS == tuple(range(base + 1, base + 41))
    earlier = (set(C2_EVAL_SEEDS) | set(C2V2_EVAL_SEEDS) | set(C2V3_EVAL_SEEDS)
               | set(DEV_SEEDS) | set(ADV_DEV_SEEDS))
    with open(os.path.join(ROOT, "reports", "advanced_v1", "dataset", "manifest.json")) as fh:
        for split in json.load(fh)["seeds"].values():
            earlier |= set(split)
    assert not set(ADV_EVAL_SEEDS) & earlier
    pattern = re.compile(r"\b(14000[0-4]\d)\b")
    for path in glob.glob(os.path.join(ROOT, "tests", "*.py")) + \
            glob.glob(os.path.join(ROOT, "tools", "*.py")):
        if path.endswith(os.path.join("tools", "run_experiment.py")):
            continue
        with open(path) as fh:
            hits = {int(x) for x in pattern.findall(fh.read())} & set(ADV_EVAL_SEEDS)
        assert not hits, (path, hits)
    for runs in glob.glob(os.path.join(ROOT, "reports", "**", "runs.jsonl"), recursive=True):
        if "adv_frozen" in runs:
            continue                    # the frozen evaluation's own output
        with open(runs) as fh:
            used = {json.loads(line)["seed"] for line in fh if line.strip()}
        assert not used & set(ADV_EVAL_SEEDS), runs


def test_product_default_keeps_every_advanced_feature_off():
    assert PRODUCT_ADVANCED == {k: False for k in ADVANCED_FLAGS}
    d = describe_policy(make_swarmos_policy())
    assert d["advanced"] == [] and d["edge_model"] is None
    assert d["fixes"] == ["F1", "F3", "F5", "F6"]


def test_flags_are_independent():
    for flag in ADVANCED_FLAGS:
        d = describe_policy(make_swarmos_policy(advanced={flag: True}))
        assert d["advanced"] == [flag]


def test_observe_only_edge_ai_leaves_the_trace_bit_identical():
    """V1 (EDGE_AI_PREDICTOR alone) runs the model every tick but acts on
    nothing: the motion trace must equal V0's."""
    scen = get_scenario("overlap_batch")
    v0 = SimEngine(scen, seed=77, policy=make_swarmos_policy())
    v1 = SimEngine(scen, seed=77, policy=make_swarmos_policy(advanced={"EDGE_AI_PREDICTOR": True}))
    v0.run(600)
    v1.run(600)
    assert v1.kpis()["advanced"]["edge_ai"]["calls"] > 0
    assert v0.trace_hash == v1.trace_hash
