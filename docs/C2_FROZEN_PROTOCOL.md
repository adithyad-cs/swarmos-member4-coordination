# C2 frozen evaluation protocol (SIH26123)

Written and frozen BEFORE any run on the evaluation seeds. Nothing in this
protocol may be changed after the first evaluation run; a change means a new
protocol with new, never-used seeds.

## Claim under test

SIH26123 C2: SWARMOS reduces total task-completion time by at least 20 %
versus traditional stop-and-wait on overlapping paths, with no loss of safety.

## Code and configuration identity

Nothing is committed (owner's instruction), so the code is identified by
content, not by a git revision:

- `code_identity.sha256` = sha256 over `(path, sha256(content))` of every
  `.py` / `.toml` file under `app/`, `tools/` and `pyproject.toml`, tracked
  or untracked (`tools/run_experiment.py: code_identity`).
- Frozen value: **see "Frozen identity" at the end of this file.**
- The benchmark is launched with `--expect-identity <frozen value>`; the runner
  refuses to run (exit 2, nothing written) if the code differs.
- `config.json` of the run stores the identity, git revision (+ an
  `uncommitted-changes` marker), Python version, full scenario specs, arms,
  seeds and the exact command line.

## Scenario, workload, fleet, termination

| | Primary: `overlap_batch` | Secondary: `open_floor_batch` |
|---|---|---|
| Floor | 40 x 28, single-file aisles, picks south, drops north (head-on by construction) | 60 x 40, two-way aisles + cross aisles |
| Fleet | 8 robots | 12 robots |
| Workload | fixed batch of 24 tasks, no arrivals | fixed batch of 36 tasks, no arrivals |
| Termination | all tasks complete, or cap 3000 s | same |
| Idle parking | on (all arms) | on (all arms) |

For a given seed the task batch and the fleet (ids, spawn poses, classes) are
identical across arms (`tests/test_c2_protocol.py::test_workload_and_fleet_are_identical_across_arms`).
No fault injection, healthy radio (`condition = normal`). Only the primary
scenario decides C2; the secondary is reported so a gain is not shown only on
corridors.

## Arms

| Label | Arm | Definition |
|---|---|---|
| A | `stop_and_wait` | Textbook stop-and-wait, `TextbookStopAndWaitPolicy`, STUCK_TICKS = 30. **Reference for C2.** |
| B | `baseline` | The same rule tuned (STUCK_TICKS = 8, from the baseline's own sweep). Honesty check. |
| C | `swarmos` | The product policy: `_make_policy("swarmos")` = graded ladder + Simplex kernel + perception fallback + observe-only lookahead (H = 15). `separating_exemption = False`, `mutual_hold_break = False`, `traffic_rules = False`. |
| C-mhb (variant) | `swarmos_mhb` | C + mutual-hold break (ladder only; kernel unchanged). Reported separately and labelled as a variant; never the headline. |

The separating-motion exemption is NOT run. The safety rule is identical for
every arm: one 0.75 m swept-segment floor (`StopAndWaitPolicy.SAFE_SEPARATION_M
== swarm_policy.HARD_STOP_M`, pinned by `tests/test_c2_protocol.py`), and the
engine's invariant monitor (INV-1 contact < 0.70 m, INV-2..4) is the same code
for every arm. Known asymmetry, in the baseline's favour: stop-and-wait sees
every robot's true position; SWARMOS sees only its 15 m radio inbox plus
onboard sensing.

## Seeds

`C2_EVAL_SEEDS` = 900001 ... 900040 (40 seeds), fixed by rule before any run.
None appears in any test, tool or stored experiment
(`tests/test_c2_protocol.py::test_evaluation_seeds_are_fresh`). Development
used 11, 13, 17, 19, 23, 29, 31, 37, 41 and small integers; the smoke test
used 101, 102, 103. Nothing will be tuned on the evaluation seeds. Every seed
is reported; none is excluded.

## Metrics (every run, every arm; `runs.jsonl`)

makespan and DNF status, finish rate, tasks completed, throughput (tasks/min),
time to 90 % completion (t90, censored at cap), persistent deadlocks (>= 1 s
wait-for cycles) and wait-cycles formed, livelock episodes (observe-only,
engine.LIVELOCK_WINDOW_TICKS), collisions, minimum separation, margin breaches
(< 0.75 m episodes), WAIT / YIELD / REROUTE counts, actual conflicts,
predicted conflicts, resolved conflicts, backtracks dropped, replans,
stop-and-wait events (working robot going from moving to zero granted motion),
held-with-work ticks, communication-induced holds (held by a robot known only
from sensing), stall releases, safety invariant failures, trace hash.

## Statistics and decision rule

- Paired by seed, Student-t 95 % CI on the per-seed percentage reduction
  (`app/db/stats.py`), reference A.
- Reported for each comparison: censored makespan (DNF = 3000 s), makespan on
  seeds where BOTH arms finished, t90 censored, tasks completed, plus
  finish rate and finished-only mean / median per arm, and the lists of
  treatment-only and reference-only DNF seeds.
- Censoring flatters the arm that does not finish. Therefore:

**C2 is MET only if ALL of the following hold for C vs A on `overlap_batch`:**

1. the 95 % CI lower bound of the censored-makespan reduction is >= 20 %;
2. C did not finish on zero seeds where A finished (else the runner marks the
   result `not_admissible`);
3. C has 0 collisions and 0 invariant failures over all 40 seeds;
4. `tools/replay_check.py <dir> --n 8 --require-identity` reproduces every
   replayed run exactly.

Otherwise C2 is reported as NOT MET, with the measured numbers. The same
statistics are reported for C vs B, for C-mhb, and for the secondary
scenario, without changing the verdict.

## Exact commands

```
PYTHONPATH=. python3 tools/run_experiment.py --name c2_frozen \
    --scenarios overlap_batch open_floor_batch \
    --arms stop_and_wait baseline swarmos swarmos_mhb \
    --reference stop_and_wait \
    --seeds $(seq 900001 900040) \
    --workers 4 --target-pct 20 \
    --expect-identity ba4086a693013487342c7832c6e9ff23bad8c7a8247fffb2e878091664179656

PYTHONPATH=. python3 tools/replay_check.py reports/experiments/<UTC>_c2_frozen \
    --n 8 --require-identity
```

## Frozen identity

- `code_identity.sha256` = `ba4086a693013487342c7832c6e9ff23bad8c7a8247fffb2e878091664179656`
  (166 files under `app/`, `tools/`, `pyproject.toml`)
- base commit `a6e18041c8151077485fcdb63c6fc1769594cefa` + uncommitted working tree
- Python 3.11, test gate 650 passed at freeze
