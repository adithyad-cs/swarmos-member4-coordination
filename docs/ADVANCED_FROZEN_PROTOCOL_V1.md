# Advanced-intelligence frozen evaluation protocol, version 1

Frozen 2026-09-27, BEFORE the first evaluation run on the seeds below.

Once the first evaluation run starts, nothing listed here changes: code, model
artifact, flags, thresholds, reference settings, safety floor, timeout,
workload, seeds, worker configuration or this document. Any change invalidates
the evaluation and requires a new protocol with new, never-used seeds. There
is no post-hoc tuning: whatever the result is, it is reported.

## Question

Does each advanced-intelligence feature, and all three together, change the
SWARMOS product's time to complete a fixed batch, its finish rate and its
safety - measured on seeds that no development step ever saw?

The features (docs/ADVANCED_INTELLIGENCE_V1.md):

| Flag | Feature |
|---|---|
| `EDGE_AI_PREDICTOR` (EAI) | Per-robot learned conflict predictor, advisory only |
| `PREDICTIVE_COORDINATION` (PC) | Pre-hold on a confident Edge-AI prediction, before the conflict is imminent |
| `LIVE_DISTRIBUTED_AUCTION` (AU) | Robot bids exchanged over the peer radio, consensus matching, WMS task leases |

The product default keeps all three OFF (`app/product.PRODUCT_ADVANCED`).

## Frozen identity and environment

| Item | Value |
|---|---|
| `code_identity.sha256` | `ae7c9aee82176521325c59ab9f90358d69d6648c39aca51810bcc72d96a86ac5` |
| Files covered | 178 `.py`/`.toml` under `app/`, `tools/`, `pyproject.toml`, tracked or untracked |
| Model artifact | `app/ml/models/edge_conflict_v1.json`; file sha256 `5de8afcd716b4aebd28f0ab76dd2a33e19e77df93c92a748be11920dabb12628`; content sha256 `829ae8fe2e2ab134e41cb48340ce86df93163870f5118200d57f69133941ef0c` |
| Model | `edge-conflict-v1`, random forest (40 trees, depth 8), 20 features, horizon 25 ticks, threshold 0.5 |
| Model check | Read back into `config.json` `arm_configs[*].edge_model` and re-checked by the replay's arm-config match |
| Git | base `a6e18041c8151077485fcdb63c6fc1769594cefa` + uncommitted working tree (nothing committed) |
| Python / platform | CPython 3.11.15, Linux x86_64, 4 CPUs |
| Workers | `--workers 4` (wall time only; every run is deterministic and independent) |

Frozen thresholds:

| Constant | Value |
|---|---|
| Proactive | `CONF_MIN` 0.6, `OFF_RATIO` 0.6, `MIN_HOLD_TICKS` 5, `MAX_HOLD_TICKS` 25, `COOLDOWN_TICKS` 40, `STALE_TICKS` 2, `CLOSING_COS` 0.05 |
| Auction | `BID_WINDOW_TICKS` 5; bid weights `W_CONGESTION_S` 3.0 (`CONG_RADIUS_M` 4), `W_RISK_S` 4.0, `W_BATTERY_S` 5.0 |
| Auction admission | `AUCTION_ADMISSION` "greedy" (identical to the greedy dispatcher's WIP rule) |
| Leases | `LEASE_TTL_TICKS` 50, `MAX_ROUNDS` 3 |
| Safety | kernel floor 0.75 m (`SAFE_SEPARATION_M == HARD_STOP_M`), F2(a)/F2(b) OFF |

### Pre-freeze gate

Logs are in `reports/advanced_v1/prefreeze_*`.

| Check | Result |
|---|---|
| pytest | 725 passed, 0 failed |
| UI verifier | 39 pass / 1 known warn / 0 FAIL |
| Backend audit | 82 pass / 0 FAIL |
| Browser audit (real Chromium) | 28 pass / 0 FAIL, including the Lab advanced run with live Edge-AI, pre-hold and auction evidence |
| Seed guards | `tests/test_advanced_protocol.py` pass |
| Pipeline smoke (seeds 101-102, all six arms) | 24/24 replayed with identity and arm-config match |
| End-to-end trace | `reports/advanced_v1/e2e_trace.json`: task, bids, consensus winner, lease, execution, prediction, PRE-HOLD, kernel approval, clear, RESUME, completion; replay identical |

## Scenarios, workload, fleet, termination

These are unchanged from C2 protocols v1 to v3.

| | Primary: `overlap_batch` | Secondary: `open_floor_batch` |
|---|---|---|
| Fleet | 8 robots | 12 robots |
| Workload | fixed batch of 24 tasks | fixed batch of 36 tasks |
| Termination | all tasks done, or cap 3000 s (DNF) | same |
| Conditions | healthy radio, no faults | same |

## Arms

| Label | Arm string | Definition |
|---|---|---|
| A (reference) | `stop_and_wait+F1+F6` | The frozen C2 v3 reference arm |
| V0 (product baseline) | `swarmos` | The shipped product, all advanced flags OFF |
| V1 | `swarmos+EAI` | + Edge AI, observe-only |
| V2 | `swarmos+EAI+PC` | + proactive coordination |
| V3A | `swarmos+AU` | + live distributed auction |
| V4 | `swarmos+EAI+PC+AU` | all three |

## Seeds

`ADV_EVAL_SEEDS` = **1400001, 1400002, ..., 1400040** (40 consecutive
integers, in this order), in `tools/run_experiment.py`.

- They were fixed by rule before any run.
- They were never used in development, training, validation, testing or any
  earlier evaluation (checked by
  `tests/test_advanced_protocol.py::test_advanced_evaluation_seeds_are_fresh_and_frozen`).
- They are disjoint from:
  - the dev ablation seeds 1000001-1000040;
  - dataset train 1100001-1100030, validation 1200001-1200010 and test 1300001-1300010;
  - C2 v1 to v3 evaluation seeds;
  - smoke seeds 101-102.
- No seed will be chosen, dropped, replaced or reordered.

## Exclusions

**None.** Every run is analysed; a run that hits the cap is a DNF.

## Endpoints

- **Primary:** each advanced arm vs V0 on `overlap_batch`, paired censored
  makespan (DNF = 3000 s), Student-t 95 % CI on the per-seed percentage
  reduction.
- **Co-primary:** finish status per seed on both scenarios (treatment-only
  and reference-only DNF lists).
- **Secondary:**
  - `open_floor_batch`;
  - finished-only and common-finish makespan;
  - t90;
  - decision oscillations and stop events;
  - held-work ticks and replans;
  - margin breaches;
  - each arm vs reference A.
- **Runtime activity (must hold for the feature to count as active):**
  - EAI arms: Edge-AI status `ok` and inference calls > 0 in every run;
  - PC arms: pre-holds > 0 on each scenario (aggregate);
  - AU arms: leases granted > 0 in every run and ownership violations = 0 in
    every run.
- **Inertness:** V1's `trace_hash` equals V0's on every (scenario, seed).
- **Safety:** 0 collisions and 0 invariant failures, all arms, both scenarios.

## Decision rule (promotion to the product default)

A feature set is promoted ONLY if ALL of the following hold for its arm vs V0:

1. The primary 95 % CI lower bound is **> 0 %** (a real improvement).
2. It has **no** treatment-only DNF seed on either scenario.
3. Safety is clean (0 collisions, 0 invariant failures).
4. Runtime activity holds.
5. `tools/replay_check.py --all --require-identity` reproduces **every**
   run, with identity AND arm-config (model hash included) match.

Otherwise the product default stays V0, and the feature remains an opt-in flag,
reported with its measured effect. A favourable mean alone never promotes.

## Exact commands

```
PYTHONPATH=. python3 tools/run_experiment.py --name adv_frozen \
    --scenarios overlap_batch open_floor_batch \
    --arms "stop_and_wait+F1+F6" "swarmos" "swarmos+EAI" "swarmos+EAI+PC" \
           "swarmos+AU" "swarmos+EAI+PC+AU" \
    --reference "swarmos" \
    --seeds $(seq 1400001 1400040) \
    --workers 4 --target-pct 20 \
    --expect-identity ae7c9aee82176521325c59ab9f90358d69d6648c39aca51810bcc72d96a86ac5

PYTHONPATH=. python3 tools/replay_check.py reports/experiments/<UTC>_adv_frozen \
    --all --require-identity --workers 4
```

The comparisons against reference A come from the same `runs.jsonl`, using the
same paired statistics (`app/db/stats.py`). Results are interpreted only after
BOTH commands complete.
