# Experiment `c2v2_frozen`

- git: `a6e18041c8151077485fcdb63c6fc1769594cefa+uncommitted-changes`
- code identity (sha256): `d7d8aacd477552a19dcb56a7731cc9611f8ea65c961af1e82a7559c76e841a90`
- created: 20260927T103242Z
- seeds: [800001, 800002, 800003, 800004, 800005, 800006, 800007, 800008, 800009, 800010, 800011, 800012, 800013, 800014, 800015, 800016, 800017, 800018, 800019, 800020, 800021, 800022, 800023, 800024, 800025, 800026, 800027, 800028, 800029, 800030, 800031, 800032, 800033, 800034, 800035, 800036, 800037, 800038, 800039, 800040]
- reference arm: `stop_and_wait+F1+F6`
- command: `PYTHONPATH=. python3 tools/run_experiment.py --name c2v2_frozen --scenarios overlap_batch open_floor_batch --arms stop_and_wait+F1+F6 baseline+F1+F6 swarmos+F1+F3+F5+F6 --reference stop_and_wait+F1+F6 --seeds 800001 800002 800003 800004 800005 800006 800007 800008 800009 800010 800011 800012 800013 800014 800015 800016 800017 800018 800019 800020 800021 800022 800023 800024 800025 800026 800027 800028 800029 800030 800031 800032 800033 800034 800035 800036 800037 800038 800039 800040 --workers 4 --target-pct 20 --expect-identity d7d8aacd477552a19dcb56a7731cc9611f8ea65c961af1e82a7559c76e841a90`

Makespan for runs that did not finish is CENSORED at the scenario cap. That understates the failing arm's true time, so it flatters the arm that finishes less; a censored target is marked MET only when the treatment never failed a seed the reference finished.

## open_floor_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline+F1+F6 | 20/40 | 34.88 | 1774.2775 | 0 | 0 | 0 | 719.2 | 5.6 | 46.575 | 1.975 | 7498.0 | 0.9539 | 0.752 |
| stop_and_wait+F1+F6 | 23/40 | 33.55 | 1968.0775 | 0 | 0 | 0 | 465.05 | 439.925 | 54.45 | 3.325 | 3557.0 | 0.9814 | 0.752 |
| swarmos+F1+F3+F5+F6 | 2/40 | 35.73 | 741.945 | 0 | 0 | 0 | 309.875 | 51.525 | 37.1 | 0.825 | 5150.575 | 0.996 | 0.7512 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline+F1+F6 | 0.5 | 548.555 / 530.3 | 798.825 | 2.3345 | 25981.175 | 0.0 | 3663.05 | 1547.925 | 523.525 | 980.325 / 979.325 | 0.0 | None | 0 |
| stop_and_wait+F1+F6 | 0.425 | 571.9471 / 563.7 | 844.75 | 1.9905 | 50136.825 | 0.0 | 1694.875 | 1434.8 | 294.825 | 1009.8 / 1008.025 | 0.0 | None | 0 |
| swarmos+F1+F3+F5+F6 | 0.95 | 623.1 / 588.05 | 649.1225 | 3.457 | 4914.7 | 11777.6 | 2496.875 | 1372.775 | 296.075 | 168.25 / 165.55 | 539.35 | 0.0 | 0 |

| arm | floor entries (total) | floor pair-ticks (mean) | frozen pairs (total) | runs with a frozen pair | recovery actions (mean: stall releases + REROUTE) |
|---|---|---|---|---|---|
| baseline+F1+F6 | 0 | 0.0 | 0 | 0 | 3709.625 |
| stop_and_wait+F1+F6 | 0 | 0.0 | 0 | 0 | 1749.325 |
| swarmos+F1+F3+F5+F6 | 0 | 0.0 | 0 | 0 | 2533.975 |

Lookahead (observe-only scoring):

- `swarmos+F1+F3+F5+F6`: precision 0.2943, recall 0.9361, mean lead 17.115 ticks (TP 6300, FP 15110, FN 430)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| baseline+F1+F6 vs stop_and_wait+F1+F6 | makespan_censored_s | 40 | -76.12 | [-140.89, -11.35] | 18/40 | not met |
| baseline+F1+F6 vs stop_and_wait+F1+F6 | makespan_s (both finished) | 7 | 2.42 | [-14.12, 18.97] | 5/7 | not met |
| baseline+F1+F6 vs stop_and_wait+F1+F6 | t90_censored_s | 40 | -31.01 | [-77.82, 15.81] | 23/40 | not met |
| baseline+F1+F6 vs stop_and_wait+F1+F6 | tasks_complete | 40 | 10.1 | [-4.66, 24.85] | 16/40 | not met |
| swarmos+F1+F3+F5+F6 vs stop_and_wait+F1+F6 | makespan_censored_s | 40 | 25.64 | [-5.74, 57.03] | 27/40 | not met |
| swarmos+F1+F3+F5+F6 vs stop_and_wait+F1+F6 | makespan_s (both finished) | 16 | -15.19 | [-28.14, -2.24] | 5/16 | not met |
| swarmos+F1+F3+F5+F6 vs stop_and_wait+F1+F6 | t90_censored_s | 40 | -13.64 | [-52.34, 25.07] | 24/40 | not met |
| swarmos+F1+F3+F5+F6 vs stop_and_wait+F1+F6 | tasks_complete | 40 | 12.99 | [-2.7, 28.68] | 22/40 | not met |

- `baseline+F1+F6 vs stop_and_wait+F1+F6`: treatment-only DNF seeds [800007, 800008, 800010, 800023, 800025, 800029, 800031, 800032, 800033, 800035]; reference-only DNF seeds [800001, 800003, 800005, 800006, 800011, 800013, 800014, 800020, 800024, 800027, 800028, 800034, 800040]

- `swarmos+F1+F3+F5+F6 vs stop_and_wait+F1+F6`: treatment-only DNF seeds [800019]; reference-only DNF seeds [800001, 800003, 800004, 800005, 800006, 800011, 800013, 800014, 800016, 800017, 800020, 800021, 800022, 800026, 800027, 800028, 800034, 800036, 800037, 800038, 800039, 800040]

## overlap_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline+F1+F6 | 14/40 | 23.25 | 1521.05 | 0 | 0 | 0 | 126.8 | 1.175 | 2.3 | 5.3 | 1150.175 | 0.5338 | 0.7573 |
| stop_and_wait+F1+F6 | 17/40 | 21.0 | 1636.755 | 0 | 0 | 0 | 101.375 | 88.35 | 1.65 | 4.375 | 717.875 | 0.6109 | 0.7565 |
| swarmos+F1+F3+F5+F6 | 0/40 | 24.0 | 492.025 | 0 | 0 | 0 | 33.125 | 7.55 | 1.0 | 1.1 | 753.2 | 0.823 | 0.7517 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline+F1+F6 | 0.65 | 724.6923 / 558.5 | 967.635 | 1.8 | 4186.575 | 0.0 | 539.85 | 434.4 | 292.675 | 322.075 / 321.65 | 0.0 | None | 0 |
| stop_and_wait+F1+F6 | 0.575 | 629.1391 / 488.6 | 1165.125 | 1.7685 | 9875.125 | 0.0 | 327.425 | 314.55 | 114.875 | 242.225 / 241.725 | 0.0 | None | 0 |
| swarmos+F1+F3+F5+F6 | 1.0 | 492.025 / 483.95 | 405.4375 | 2.9877 | 340.95 | 2722.275 | 342.05 | 170.3 | 63.95 | 37.875 / 36.175 | 71.65 | 0.0 | 0 |

| arm | floor entries (total) | floor pair-ticks (mean) | frozen pairs (total) | runs with a frozen pair | recovery actions (mean: stall releases + REROUTE) |
|---|---|---|---|---|---|
| baseline+F1+F6 | 0 | 0.0 | 0 | 0 | 542.15 |
| stop_and_wait+F1+F6 | 0 | 0.0 | 0 | 0 | 329.075 |
| swarmos+F1+F3+F5+F6 | 0 | 0.0 | 0 | 0 | 343.05 |

Lookahead (observe-only scoring):

- `swarmos+F1+F3+F5+F6`: precision 0.5206, recall 0.9769, mean lead 15.7615 ticks (TP 1480, FP 1363, FN 35)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| baseline+F1+F6 vs stop_and_wait+F1+F6 | makespan_censored_s | 40 | -74.86 | [-146.33, -3.38] | 18/40 | not met |
| baseline+F1+F6 vs stop_and_wait+F1+F6 | makespan_s (both finished) | 15 | -13.83 | [-44.02, 16.35] | 7/15 | not met |
| baseline+F1+F6 vs stop_and_wait+F1+F6 | t90_censored_s | 40 | -79.34 | [-156.65, -2.03] | 20/40 | not met |
| baseline+F1+F6 vs stop_and_wait+F1+F6 | tasks_complete | 40 | 33.33 | [2.07, 64.59] | 16/40 | not met |
| swarmos+F1+F3+F5+F6 vs stop_and_wait+F1+F6 | makespan_censored_s | 40 | 39.5 | [25.23, 53.78] | 29/40 | MET |
| swarmos+F1+F3+F5+F6 vs stop_and_wait+F1+F6 | makespan_s (both finished) | 23 | 7.45 | [-5.78, 20.68] | 12/23 | not met |
| swarmos+F1+F3+F5+F6 vs stop_and_wait+F1+F6 | t90_censored_s | 40 | 32.11 | [20.17, 44.06] | 29/40 | MET |
| swarmos+F1+F3+F5+F6 vs stop_and_wait+F1+F6 | tasks_complete | 40 | 38.12 | [5.08, 71.15] | 17/40 | not met |

- `baseline+F1+F6 vs stop_and_wait+F1+F6`: treatment-only DNF seeds [800007, 800016, 800020, 800031, 800032, 800035, 800037, 800038]; reference-only DNF seeds [800005, 800006, 800011, 800012, 800014, 800015, 800025, 800026, 800027, 800033, 800039]

- `swarmos+F1+F3+F5+F6 vs stop_and_wait+F1+F6`: treatment-only DNF seeds none; reference-only DNF seeds [800003, 800005, 800006, 800009, 800011, 800012, 800014, 800015, 800019, 800021, 800022, 800025, 800026, 800027, 800030, 800033, 800039]
