# C2 v3 result: PRODUCT-DEFAULT validation (`docs/C2_FROZEN_PROTOCOL_V3.md`)

Interpreted only after the benchmark AND the full replay had both finished.

- v2 (`docs/C2_V2_RESULT.md`) showed the result for the evaluated arm
  configuration `swarmos+F1+F3+F5+F6`.
- **v3 is the product result.** Arm C is `swarmos` exactly as
  `app/api/runner._make_policy` ships it, with no experiment-side switches.

## Integrity record

| Item | Evidence |
|---|---|
| Protocol frozen before the first run | `reports/c2v3/protocol_freeze_record.txt`: 2026-09-27T13:08:22Z, sha256 `21a6c7d8...ef99`, byte-identical after the run |
| Product code identity | `f3dabbf0d732bfc218a1ab31f906299ca1baee5c4b1de148534b16c0d023094f`, checked at launch (`--expect-identity`) and unchanged after |
| Pre-freeze gate | pytest 672 passed; UI verifier 39/1 warn/0 FAIL; backend audit 82/0; browser audit 26/0; seed and protocol guards pass (`reports/c2v3/prefreeze_*`) |
| Benchmark | `reports/experiments/20260927T130822Z_c2v3_frozen/`: 240 runs (3 arms x 2 scenarios x 40 seeds), complete. Command verbatim in `config.json`. |
| Seeds | 600001-600040, in order. None chosen, dropped, replaced or reordered. Never used before. |
| Exclusions | none |
| Mid-run changes | none |
| Replay | `--all --require-identity --workers 4`: **240/240 reproduced exactly**, code identity MATCH, arm configs MATCH, 0 mismatches (`reports/c2v3/replay_all.log`) |

## A. Primary C2 verdict (overlap_batch, C = product `swarmos` vs A = `stop_and_wait+F1+F6`)

| # | Condition | Measured | Pass |
|---|---|---|---|
| 1 | 95% CI lower bound >= +20% | **+48.9%, 95% CI [+35.3, +62.5]**, n = 40, 33/40 wins | Yes |
| 2 | C fails no seed that A finished | C 40/40 finished; treatment-only DNF seeds: **none** | Yes |
| 3 | 0 collisions, 0 invariant failures | 0 / 0 on both scenarios | Yes |
| 4 | Full replay, identity and config | 240/240 | Yes |
| 5 | No violation or substitution | none | Yes |

**C2 is MET for the product-default configuration** under the frozen v3 rule.

## B. Open-floor secondary result (does not change the verdict)

| C vs A | n | Mean | 95% CI |
|---|---|---|---|
| Capped, all seeds | 40 | +33.7% | [+4.5, +62.8] |
| Common finish | 15 | **-44.4%** | [-105.8, +17.1] (C faster on only 4 of 15) |
| t90, capped | 40 | +11.3% | [-8.9, +31.4] |

- Finish: C 40/40, A 15/40, B 15/40.
- C failed no seed that A finished.
- **On seeds both finish, SWARMOS is slower on average.** The interval is wide
  and includes 0, and only 4 of 15 favour SWARMOS. SWARMOS's open-floor
  advantage comes entirely from finishing every batch.

## C-G. Time results by view (95% CI, paired by seed, reference A)

| Scenario | View | A textbook +F1+F6 | B tuned +F1+F6 | C SWARMOS product | C vs A |
|---|---|---|---|---|---|
| overlap | **C. All-seed capped mean (s)** | 1848 | 1708 | **481** | **+48.9% [+35.3, +62.5]** |
| overlap | **D. Finished-only mean / median (s)** | 806 / 514 | 847 / 511 | 481 / 466 | (unpaired) |
| overlap | **E. Common-finish** | n = 21 | | | **+17.5% [+1.4, +33.6]**, 14/21 wins |
| overlap | **F. Finish rate** | 21/40 | 24/40 | **40/40** | |
| overlap | t90 capped (s) | 1085 | 979 | 411 | +29.0% [+16.8, +41.2] |
| overlap | Tasks done (of 24) | 21.4 | 22.1 | 24.0 | +44.8% [-12.3, +102.0] |
| open floor | C. All-seed capped (s) | 2094 | 2099 | 672 | +33.7% [+4.5, +62.8] |
| open floor | D. Finished-only mean / median (s) | 583 / 578 | 597 / 544 | 672 / 589 | (unpaired) |
| open floor | E. Common-finish | n = 15 | | | -44.4% [-105.8, +17.1] |
| open floor | F. Finish rate | 15/40 | 15/40 | 40/40 | |

Failed-seed lists:

- **overlap, A failed and C finished (19):** 600001, 600002, 600005, 600008,
  600009, 600012, 600014, 600015, 600019, 600021, 600023, 600024, 600025,
  600027, 600028, 600031, 600032, 600039, 600040.
- **overlap, C failed and A finished:** none.
- **open floor, A failed and C finished (25):** 600002, 600003, 600004,
  600009, 600010, 600011, 600015, 600016, 600017, 600018, 600019, 600021,
  600024, 600025, 600026, 600027, 600028, 600029, 600030, 600031, 600033,
  600034, 600037, 600039, 600040.
- **open floor, C failed:** none.
- For B vs A, see `summary.md`.

## H-M. Safety and coordination (all 40 seeds per cell)

| Scenario | Arm | H. Collisions | I. Invariant failures | J. Margin breaches | K. Frozen pairs | L. Persistent deadlocks (mean) | M. Replans (mean) | Min separation (m) |
|---|---|---|---|---|---|---|---|---|
| overlap | A | 0 | 0 | 0 | 0 | 97.0 | 764 | 0.752 |
| overlap | B | 0 | 0 | 0 | 0 | 0.6 | 1100 | 0.759 |
| overlap | **C** | **0** | **0** | **0** | **0** | 3.5 | 635 | 0.754 |
| open floor | A | 0 | 0 | 0 | 0 | 479 | 3569 | 0.752 |
| open floor | B | 0 | 0 | **1** | 0 | 16.3 | 8057 | 0.748 |
| open floor | **C** | **0** | **0** | **0** | **0** | 20.5 | 2564 | 0.750 |

The one margin breach is in the tuned REFERENCE arm, not in SWARMOS. The
tuned baseline also has fewer persistent deadlocks than SWARMOS on both
floors (0.6 vs 3.5; 16.3 vs 20.5), but it fails far more batches.

## N. Replay

240/240 reproduced exactly, code identity MATCH, arm configs MATCH, 0
mismatches.

## O. Exact product code identity

`f3dabbf0d732bfc218a1ab31f906299ca1baee5c4b1de148534b16c0d023094f`
(167 files, base `a6e1804` + uncommitted tree, CPython 3.11.15).

## Limits (stated, not hidden)

- Most of the primary gain is **reliability**: SWARMOS finishes every batch;
  textbook stop-and-wait fails 19 of 40. On the common-finish subset the gain
  is +17.5% with a CI lower bound of +1.4%. That is below the 20% bar as a
  pure speed claim.
- On the open floor, SWARMOS is slower when both finish (point estimate
  -44%, not significant).
- The remaining arm asymmetries favour the reference: its built-in rule for
  separating inside the margin, and its global view.
- This is a simulation result on two synthetic floors. It is not a physical
  certification.
