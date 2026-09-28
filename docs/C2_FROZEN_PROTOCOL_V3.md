# C2 frozen evaluation protocol, version 3: PRODUCT-DEFAULT validation (SIH26123)

Frozen 2026-09-27, BEFORE the first evaluation run on the seeds below.

Once the first evaluation run starts, nothing listed here changes: code,
thresholds, flags, baseline settings, safety floor, timeout, workload, seeds,
worker configuration or this document. Any change invalidates the benchmark
and requires a new protocol with new, never-used seeds.

## Why version 3

Version 2 (`docs/C2_FROZEN_PROTOCOL_V2.md`, result `docs/C2_V2_RESULT.md`)
met the primary C2 rule for the EVALUATED ARM `swarmos+F1+F3+F5+F6`. At that
point the product defaults did not carry those fixes, so v2 is not a product
result.

Version 3 switches F1 + F3 + F5 + F6 on in the product default
(`app/api/runner._make_policy("swarmos")`). That changes the code identity,
so the product configuration is validated here on fresh seeds. No algorithm,
parameter, workload, timeout, fleet or scenario setting changed.

Pre-freeze equivalence check: the product arm `swarmos` produced bit-identical
traces to the v2 arm `swarmos+F1+F3+F5+F6` on dev seeds 700001-700003, and
their read-back configurations are equal (pinned by
`tests/test_c2_protocol.py::test_product_default_is_the_evaluated_configuration`).

## Frozen identity and environment

| Item | Value |
|---|---|
| `code_identity.sha256` (PRODUCT code) | `f3dabbf0d732bfc218a1ab31f906299ca1baee5c4b1de148534b16c0d023094f` |
| Files covered | 167 `.py`/`.toml` under `app/`, `tools/`, `pyproject.toml`, tracked or untracked |
| Git | base `a6e18041c8151077485fcdb63c6fc1769594cefa` + uncommitted working tree (nothing committed) |
| Python / platform | CPython 3.11.15, Linux-6.18.44-fc-v37-x86_64-with-glibc2.39, 4 CPUs |
| Workers | `--workers 4` (wall time only; every run is deterministic and independent) |

### Pre-freeze gate

Logs are in `reports/c2v3/prefreeze_*`.

| Check | Result |
|---|---|
| pytest | 672 passed, 0 failed |
| UI verifier | 39 pass / 1 known warn / 0 FAIL |
| Backend audit | 82 pass / 0 FAIL |
| Browser audit (real Chromium) | 26 pass / 0 FAIL |
| Seed-freshness and protocol guards | pass |
| Pipeline smoke (seeds 101-102) | 6/6 replayed with identity and arm-config match |

## Scenarios, workload, fleet, termination

Unchanged from versions 1 and 2.

| | Primary: `overlap_batch` | Secondary: `open_floor_batch` |
|---|---|---|
| Floor | 40 x 28, single-file aisles | 60 x 40, two-way aisles + cross aisles |
| Fleet | 8 robots | 12 robots |
| Workload | fixed batch of 24 tasks | fixed batch of 36 tasks |
| Termination | all tasks done, or cap 3000 s (DNF) | same |
| Idle parking | on, all arms | on, all arms |
| Conditions | healthy radio, no faults | same |

The same workload generator is used for every arm; the batch and fleet
depend on the seed only.

## Arms

| Label | Arm string | Definition |
|---|---|---|
| A (**reference**) | `stop_and_wait+F1+F6` | Textbook stop-and-wait (STUCK_TICKS 30) + shared F1 + F6 |
| B | `baseline+F1+F6` | Tuned stop-and-wait (STUCK_TICKS 8) + shared F1 + F6 |
| C (**PRODUCT**) | `swarmos` | `_make_policy("swarmos")` as shipped: ladder + Simplex kernel + perception fallback + observe-only lookahead H 15 + F1 + F3 + F5, with the policy carrying F6 (`release_cooldown_ticks` 300, applied by the engine) |

Arm C uses NO experiment-side switches; it is exactly what the API, the
dashboard and the co-simulation build.

Scope of each fix:

| Fix | Scope |
|---|---|
| F1 | **Shared, all arms** |
| F6 | **Shared, all arms** |
| F3 | SWARMOS only (ladder) |
| F5 | SWARMOS only (recovery; grants no motion) |

Safety:

- **F2(a) and F2(b) are disabled.** The separating exemption, mutual-hold
  break and traffic rules are OFF.
- The safety kernel and its 0.75 m floor are unchanged
  (`SAFE_SEPARATION_M == HARD_STOP_M == 0.75`, pinned).
- The engine's invariant monitor is the same for every arm.
- The remaining asymmetries favour the reference: the stop-and-wait arms keep
  their built-in rule for separating inside the margin, and they have a global
  view.

Every flag and threshold is read back from the constructed arms into
`config.json` (`arm_configs`), and the replay re-checks it.

## Seeds

`C2V3_EVAL_SEEDS` = **600001, 600002, ..., 600040** (40 consecutive integers,
in this order), in `tools/run_experiment.py`.

- They were fixed by rule before any run.
- They were never used in development, testing or any earlier evaluation
  (checked by `tests/test_c2_protocol.py::test_v3_evaluation_seeds_are_fresh_and_frozen`).
- Not reused, and disjoint from:
  - 800001-800040 (v2);
  - 900001-900040 (v1);
  - 700001-700020 (development);
  - 101-103 (smoke);
  - earlier small development seeds.
- No seed will be chosen, dropped, replaced or reordered.

## Exclusions

**None.** Every run of every arm on every seed is in the analysis. A run that
hits the 3000 s cap is a DNF and is reported as such.

## Endpoints

- **Primary:** `overlap_batch` paired time to completion, C vs A (censored
  makespan: DNF = 3000 s).
- **Co-primary:** per-seed finish status on `overlap_batch` (finish rates;
  treatment-only and reference-only DNF lists).
- **Secondary:**
  - `open_floor_batch`;
  - t90;
  - tasks completed, throughput;
  - persistent deadlocks, frozen pairs;
  - replans, backtracks, WAIT/YIELD/REROUTE counts;
  - margin breaches, stall releases.

Each is reported as all-seed (capped), finished-only, paired common-finish,
and failed-seed lists.

## Statistics

Paired by seed. Student-t 95 % CI on the per-seed percentage reduction
(`app/db/stats.py`), reference A.

## Decision rule

**C2 is MET for the product default only if ALL hold for C vs A on
`overlap_batch`:**

1. 95 % CI lower bound of the primary paired time reduction **>= +20 %**.
2. C fails **no** seed that A finished (the runner marks a violation
   `not_admissible`).
3. C has **0 collisions and 0 safety-invariant failures** (checked on both
   scenarios).
4. `tools/replay_check.py --all --require-identity` reproduces **every** run,
   with code-identity AND arm-config match.
5. No protocol violation, and no seed or configuration substitution.

Otherwise C2 is **NOT MET for the product default**, reported with the
measured numbers. A favourable mean alone never makes it met.

## Exact commands

```
PYTHONPATH=. python3 tools/run_experiment.py --name c2v3_frozen \
    --scenarios overlap_batch open_floor_batch \
    --arms "stop_and_wait+F1+F6" "baseline+F1+F6" "swarmos" \
    --reference "stop_and_wait+F1+F6" \
    --seeds $(seq 600001 600040) \
    --workers 4 --target-pct 20 \
    --expect-identity f3dabbf0d732bfc218a1ab31f906299ca1baee5c4b1de148534b16c0d023094f

PYTHONPATH=. python3 tools/replay_check.py reports/experiments/<UTC>_c2v3_frozen \
    --all --require-identity --workers 4
```

Results are interpreted only after BOTH complete.
