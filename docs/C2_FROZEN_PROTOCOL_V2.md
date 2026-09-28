# C2 frozen evaluation protocol, version 2 (SIH26123)

Frozen 2026-09-27, BEFORE the first evaluation run on the seeds below.

Once the first evaluation run starts, nothing listed here changes: code,
thresholds, flags, baseline settings, safety floor, timeout, workload, seeds,
worker configuration or this document. Any change invalidates the benchmark
and requires a new protocol with new, never-used seeds.

Version 1 (`docs/C2_FROZEN_PROTOCOL.md`, seeds 900001-900040) was run and
reported C2 NOT MET. Its seeds are spent. Version 2 evaluates the fixes found
by the root-cause analysis (`docs/C2_ROOT_CAUSE_ANALYSIS.md`) and developed on
dev seeds 700001-700020 (`docs/IMPROVEMENT_CYCLE_20260927.md`).

## Claim under test

SIH26123 C2: SWARMOS reduces total task-completion time by at least 20 %
versus traditional stop-and-wait on overlapping paths, with no loss of safety.

## Frozen identity and environment

| Item | Value |
|---|---|
| `code_identity.sha256` | `d7d8aacd477552a19dcb56a7731cc9611f8ea65c961af1e82a7559c76e841a90` |
| Files covered | 167 `.py`/`.toml` files under `app/`, `tools/`, `pyproject.toml`, tracked or untracked |
| Git | base commit `a6e18041c8151077485fcdb63c6fc1769594cefa` + uncommitted working tree (nothing committed, owner's instruction) |
| Python | CPython 3.11.15 |
| Platform | Linux-6.18.44-fc-v37-x86_64-with-glibc2.39, 4 CPUs |
| Libraries | starlette 1.7.0, pydantic 2.13.5 (not used by the benchmark path) |
| Workers | `--workers 4`. Runs are deterministic and independent, so the worker count affects wall time only; the trace hash is per run. |
| Test gate at freeze | pytest 669 passed, 0 failed; UI verifier 39 pass / 1 known warn / 0 FAIL; backend audit 82/0; browser audit 26/0 |

The runner is launched with `--expect-identity` and refuses to run (exit 2,
nothing written) if the code differs. `config.json` records the identity,
Python, platform, workers, the full scenario specs, and `arm_configs`. That
last item is every flag and threshold READ BACK from the constructed policy
and engine settings, not restated by hand.

## Scenarios, workload, fleet, termination

Unchanged from version 1.

| | Primary: `overlap_batch` | Secondary: `open_floor_batch` |
|---|---|---|
| Floor | 40 x 28, single-file aisles, picks south, drops north | 60 x 40, two-way aisles + cross aisles |
| Fleet | 8 robots | 12 robots |
| Workload | fixed batch of 24 tasks, no arrivals | fixed batch of 36 tasks, no arrivals |
| Termination | all tasks complete, or cap 3000 s (DNF) | same |
| Idle parking | on, all arms | on, all arms |
| Conditions | healthy radio, no faults | same |

The workload generator is identical for every arm, and the batch and fleet
depend on the seed only
(`tests/test_c2_protocol.py::test_workload_and_fleet_are_identical_across_arms`).

## Arms

| Label | Arm string | Definition |
|---|---|---|
| A (**reference**) | `stop_and_wait+F1+F6` | Textbook stop-and-wait (`TextbookStopAndWaitPolicy`, STUCK_TICKS 30) + shared fixes F1, F6 |
| B | `baseline+F1+F6` | Tuned stop-and-wait (STUCK_TICKS 8) + shared fixes F1, F6 |
| C (**SWARMOS**) | `swarmos+F1+F3+F5+F6` | Product SWARMOS policy (ladder + Simplex kernel + perception fallback + observe-only lookahead H 15) + F1, F3, F5, F6 |

### Which fixes are shared and which are SWARMOS-specific

| Fix | Scope | What |
|---|---|---|
| F1 polyline sweep | **Shared: A, B, C** | The safety check tests the real path legs of a step as well as its chord. It can only veto more. |
| F6 release cooldown (300 ticks) | **Shared: A, B, C** (engine) | After a stall release the same robot cannot retake the same task for 30 s |
| F3 leader rule | SWARMOS only (ladder) | A robot not closing on its peer keeps right of way in the contest band |
| F5 standoff breaker (20 / 200 ticks, 3 m) | SWARMOS only (recovery) | After 2 s of mutual hold, a deterministic loser replans around the peer and its route. It grants no motion. |

### Safety rule

- Every arm uses the same 0.75 m floor with the same F1 swept-path geometry
  (`SAFE_SEPARATION_M == HARD_STOP_M == 0.75`, pinned by a test).
- The engine's invariant monitor (INV-1 contact < 0.70 m, INV-2..4) is the
  same code for every arm.
- **SWARMOS receives no safety relaxation:**
  - the separating-motion exemption, mutual-hold break and traffic rules are
    OFF (pinned by
    `tests/test_c2_protocol.py::test_v2_arms_share_the_safety_rule_and_swarmos_gets_no_relaxation`);
  - F2(a) was not implemented.
- The at-floor rule still differs, in the REFERENCE's favour. The
  stop-and-wait arms keep their built-in rule that lets a pair already
  inside the margin move apart; SWARMOS has no such rule.
- Stop-and-wait also sees every robot's true position, while SWARMOS sees its
  15 m radio inbox plus onboard sensing.

These configurations are NOT yet the product defaults (`app/api/runner.py`).
The claim, if any, is about the arm string above.

## Seeds

`C2V2_EVAL_SEEDS` = **800001, 800002, ..., 800040** (40 consecutive integers,
in this order), in `tools/run_experiment.py`.

- They were fixed by rule before any run.
- They appear in no test, tool or stored experiment (checked by
  `tests/test_c2_protocol.py::test_v2_evaluation_seeds_are_fresh_and_frozen`).
- Seeds used elsewhere, for reference:
  - development: 700001-700020;
  - v1 evaluation: 900001-900040;
  - smoke tests: 101-103;
  - earlier development: 11, 13, 17, 19, 23, 29, 31, 37, 41 and small integers.
- 40 seeds keep comparability with v1.
- No seed will be chosen, dropped, replaced or reordered.

## Exclusions

**None.** Every run of every arm on every seed is reported. A run that hits
the 3000 s cap is a DNF and stays in the analysis as described below. There
are no other exclusion rules.

## Endpoints

- **Primary:** `overlap_batch` paired time to completion, C vs A (censored
  makespan: DNF = 3000 s), paired by seed.
- **Co-primary robustness:** per-seed finish status on `overlap_batch`
  (finish rate per arm; treatment-only and reference-only DNF seed lists).
- **Secondary:**
  - `open_floor_batch`;
  - time to 90 % completion;
  - tasks completed, throughput;
  - persistent deadlocks, frozen pairs;
  - replans, backtracks, WAIT/YIELD/REROUTE counts;
  - margin breaches, floor pair-ticks;
  - stall releases, standoff breaks, communication holds.

Every endpoint is reported four ways: all seeds (censored), finished runs
only, the paired common-finish subset (seeds where both arms finished), and
the failed-seed lists. Capped averages are never shown without the DNF counts
beside them.

## Statistics

Paired by seed. Student-t 95 % CI on the per-seed percentage reduction
(`app/db/stats.py paired().interval_pct()`), reference A. C vs B and the
secondary scenario are reported with the same statistics and do not change
the verdict.

## Decision rule

**C2 is MET only if ALL of the following hold for C vs A on `overlap_batch`:**

1. The 95 % CI lower bound of the primary paired time reduction (censored
   makespan) is **>= +20 %**.
2. C did not fail **any** seed that A finished. The runner marks a violation
   `not_admissible` and never reports it as MET.
3. C has **0 collisions and 0 safety-invariant failures** over all 40 seeds.
   This is checked for both scenarios and reported for both.
4. `tools/replay_check.py` with **`--all --require-identity`** reproduces
   **every** recorded run exactly (identity match, arm-config match, trace hash
   and headline metrics).
5. No protocol violation and no seed or configuration substitution occurred.

Otherwise C2 is **NOT MET**, reported with the measured numbers. A favourable
mean alone never makes C2 met.

## Exact commands

Benchmark (run once):

```
PYTHONPATH=. python3 tools/run_experiment.py --name c2v2_frozen \
    --scenarios overlap_batch open_floor_batch \
    --arms "stop_and_wait+F1+F6" "baseline+F1+F6" "swarmos+F1+F3+F5+F6" \
    --reference "stop_and_wait+F1+F6" \
    --seeds $(seq 800001 800040) \
    --workers 4 --target-pct 20 \
    --expect-identity d7d8aacd477552a19dcb56a7731cc9611f8ea65c961af1e82a7559c76e841a90
```

Replay (every run, identity required):

```
PYTHONPATH=. python3 tools/replay_check.py reports/experiments/<UTC>_c2v2_frozen \
    --all --require-identity --workers 4
```

Results are interpreted only after BOTH complete.
