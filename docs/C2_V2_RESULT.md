# C2 v2 result (frozen protocol `docs/C2_FROZEN_PROTOCOL_V2.md`)

Interpreted only after the benchmark AND the full replay had both finished.

## Integrity record

| Item | Evidence |
|---|---|
| Protocol frozen before the first run | `reports/c2v2/protocol_freeze_record.txt`: 2026-09-27T10:32:38Z, protocol sha256 `273b9f4d...0243`. The file is byte-identical after the run. |
| Code identity | `d7d8aacd477552a19dcb56a7731cc9611f8ea65c961af1e82a7559c76e841a90`. The runner checked it with `--expect-identity`, and it is unchanged after the run. |
| Benchmark | `reports/experiments/20260927T103242Z_c2v2_frozen/`: 240 runs (3 arms x 2 scenarios x 40 seeds), exit 0. stdout in `reports/c2v2/benchmark_stdout.log`. |
| Command | Exactly as written in the protocol. It is recorded verbatim in `config.json`. |
| Seeds | 800001-800040, in order. None chosen, dropped, replaced or reordered. |
| Exclusions | None. Every run is in the analysis. |
| Mid-run changes | None. No file under `app/`, `tools/` or the protocol was edited between freeze and the end of the replay. |
| Replay | `tools/replay_check.py --all --require-identity --workers 4`: **240/240 reproduced exactly**, code identity MATCH, arm configs MATCH, 0 mismatches (`reports/c2v2/replay_all.log`) |

## Decision rule (primary: overlap_batch, C = `swarmos+F1+F3+F5+F6` vs A = `stop_and_wait+F1+F6`)

| # | Condition | Measured | Pass |
|---|---|---|---|
| 1 | 95% CI lower bound of the paired time reduction >= +20% | **+39.5%, 95% CI [+25.2, +53.8]**, n = 40, 29 wins | Yes |
| 2 | C fails no seed that A finished | C: 0/40 DNF. Treatment-only DNF seeds: **none** | Yes |
| 3 | 0 collisions and 0 invariant failures | 0 and 0 on both scenarios (80 runs of C); min separation 0.7517 m | Yes |
| 4 | Full replay reproduces every run | 240/240, identity required | Yes |
| 5 | No protocol violation or substitution | none | Yes |

**Verdict under the frozen v2 rule: C2 MET** for the arm `swarmos+F1+F3+F5+F6`
against textbook stop-and-wait with the shared fixes, on `overlap_batch`.

## What the result does and does not say

### Primary scenario, overlap_batch (40 seeds)

| Arm | Finished | Mean (median) time, finished runs (s) | Mean time, capped (s) | t90, capped (s) | Tasks done (mean of 24) | Persistent deadlocks | Replans |
|---|---|---|---|---|---|---|---|
| A stop_and_wait+F1+F6 | 23/40 | 629 (489) | 1637 | 1165 | 21.0 | 88.4 | 718 |
| B baseline+F1+F6 | 26/40 | 725 (559) | 1521 | 968 | 23.3 | 1.2 | 1150 |
| **C swarmos+F1+F3+F5+F6** | **40/40** | 492 (484) | **492** | **405** | **24.0** | 7.6 | 753 |

| C vs A | n | Mean reduction | 95% CI |
|---|---|---|---|
| All seeds, capped (primary) | 40 | **+39.5%** | [+25.2, +53.8] |
| Seeds where both finished | 23 | +7.5% | **[-5.8, +20.7]**: not significant |
| t90, capped | 40 | +32.1% | [+20.2, +44.1] |
| Tasks completed | 40 | +38.1% | [+5.1, +71.2] |

- A failed 17 seeds that C finished: 800003, 800005, 800006, 800009, 800011,
  800012, 800014, 800015, 800019, 800021, 800022, 800025, 800026, 800027,
  800030, 800033, 800039.
- C failed none that A finished.

**Read it honestly.** Most of the primary gain is *reliability*. C finishes
every batch; textbook stop-and-wait fails 17 of 40. When both finish, C is
7.5% faster on average and that is not statistically significant.

### Secondary scenario, open_floor_batch (40 seeds)

It does not change the verdict.

| Arm | Finished | Mean time, finished (s) | Mean time, capped (s) |
|---|---|---|---|
| A | 17/40 | 572 | 1968 |
| B | 20/40 | 549 | 1774 |
| C | 38/40 | 623 | 742 |

| C vs A | n | Mean reduction | 95% CI |
|---|---|---|---|
| All seeds, capped | 40 | +25.6% | [-5.7, +57.0] |
| Seeds where both finished | 16 | **-15.2%** | **[-28.1, -2.2]**: C is SLOWER |
| t90, capped | 40 | -13.6% | [-52.3, +25.1] |

- C failed seed 800019, which A finished.
- A failed 22 seeds that C finished.

On the open floor, C is significantly slower than stop-and-wait whenever both
finish, and would fail condition 2 there. The frozen rule applies to
overlap_batch only, so this does not change the verdict, but it is a real
weakness.

### Safety (all 240 runs)

- 0 collisions, 0 invariant failures and 0 safety FAILs in every arm.
- 0 margin breaches, 0 floor entries and 0 frozen pairs.
- Minimum separation: C 0.7512 m, A 0.752 m.

### Fairness notes

- The shared fixes F1 and F6 were applied to the reference arms.
- SWARMOS received no safety relaxation.
- The remaining asymmetries favour the REFERENCE: its separating escape
  inside the margin, and its global view.
- The tuned baseline B did not beat A on the primary endpoint (capped: -74.9%).
  C is ahead of both.

### Scope

- The evaluated configuration is the arm string
  `swarmos+F1+F3+F5+F6`. **It is not yet the product default** in
  `app/api/runner.py`.
- A claim that "the SWARMOS product meets C2" requires switching those flags
  on in the product, which changes the code identity. That is a new
  configuration. It should be confirmed by at least the full test gate, and
  strictly by a new frozen run on new seeds.
- This is a simulation result on two synthetic floors. It is not a physical
  certification.
