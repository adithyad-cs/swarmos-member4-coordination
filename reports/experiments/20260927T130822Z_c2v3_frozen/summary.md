# Experiment `c2v3_frozen`

- git: `a6e18041c8151077485fcdb63c6fc1769594cefa+uncommitted-changes`
- code identity (sha256): `f3dabbf0d732bfc218a1ab31f906299ca1baee5c4b1de148534b16c0d023094f`
- created: 20260927T130822Z
- seeds: [600001, 600002, 600003, 600004, 600005, 600006, 600007, 600008, 600009, 600010, 600011, 600012, 600013, 600014, 600015, 600016, 600017, 600018, 600019, 600020, 600021, 600022, 600023, 600024, 600025, 600026, 600027, 600028, 600029, 600030, 600031, 600032, 600033, 600034, 600035, 600036, 600037, 600038, 600039, 600040]
- reference arm: `stop_and_wait+F1+F6`
- command: `PYTHONPATH=. python3 tools/run_experiment.py --name c2v3_frozen --scenarios overlap_batch open_floor_batch --arms stop_and_wait+F1+F6 baseline+F1+F6 swarmos --reference stop_and_wait+F1+F6 --seeds 600001 600002 600003 600004 600005 600006 600007 600008 600009 600010 600011 600012 600013 600014 600015 600016 600017 600018 600019 600020 600021 600022 600023 600024 600025 600026 600027 600028 600029 600030 600031 600032 600033 600034 600035 600036 600037 600038 600039 600040 --workers 4 --target-pct 20 --expect-identity f3dabbf0d732bfc218a1ab31f906299ca1baee5c4b1de148534b16c0d023094f`

Makespan for runs that did not finish is CENSORED at the scenario cap. That understates the failing arm's true time, so it flatters the arm that finishes less; a censored target is marked MET only when the treatment never failed a seed the reference finished.

## open_floor_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline+F1+F6 | 25/40 | 34.48 | 2098.81 | 0 | 1 | 0 | 865.675 | 16.275 | 41.05 | 3.0 | 8056.95 | 0.951 | 0.748 |
| stop_and_wait+F1+F6 | 25/40 | 33.7 | 2093.7025 | 0 | 0 | 0 | 497.75 | 479.0 | 25.45 | 3.0 | 3568.5 | 0.9881 | 0.752 |
| swarmos | 0/40 | 36.0 | 671.8125 | 0 | 0 | 0 | 144.65 | 20.475 | 6.425 | 0.225 | 2563.775 | 0.9982 | 0.75 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline+F1+F6 | 0.375 | 596.8267 / 543.8 | 887.7525 | 1.856 | 28093.4 | 0.0 | 3949.9 | 2268.7 | 779.85 | 1544.375 / 1543.375 | 0.0 | None | 0 |
| stop_and_wait+F1+F6 | 0.375 | 583.2067 / 577.8 | 904.645 | 1.8175 | 50685.475 | 0.0 | 1714.775 | 1394.1 | 363.25 | 939.375 / 937.7 | 0.0 | None | 0 |
| swarmos | 1.0 | 671.8125 / 588.8 | 518.425 | 3.558 | 2077.75 | 7735.425 | 1224.375 | 960.85 | 183.15 | 118.75 / 116.3 | 300.825 | 0.0 | 0 |

| arm | floor entries (total) | floor pair-ticks (mean) | frozen pairs (total) | runs with a frozen pair | recovery actions (mean: stall releases + REROUTE) |
|---|---|---|---|---|---|
| baseline+F1+F6 | 1 | 0.025 | 0 | 0 | 3990.95 |
| stop_and_wait+F1+F6 | 0 | 0.0 | 0 | 0 | 1740.225 |
| swarmos | 0 | 0.0 | 0 | 0 | 1230.8 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.3705, recall 0.9259, mean lead 16.2855 ticks (TP 4398, FP 7473, FN 352)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| baseline+F1+F6 vs stop_and_wait+F1+F6 | makespan_censored_s | 40 | -80.1 | [-145.23, -14.96] | 14/40 | not met |
| baseline+F1+F6 vs stop_and_wait+F1+F6 | makespan_s (both finished) | 6 | 7.97 | [0.12, 15.82] | 5/6 | not met |
| baseline+F1+F6 vs stop_and_wait+F1+F6 | t90_censored_s | 40 | -47.91 | [-102.27, 6.45] | 22/40 | not met |
| baseline+F1+F6 vs stop_and_wait+F1+F6 | tasks_complete | 40 | 18.99 | [-19.34, 57.31] | 13/40 | not met |
| swarmos vs stop_and_wait+F1+F6 | makespan_censored_s | 40 | 33.65 | [4.47, 62.84] | 29/40 | not met |
| swarmos vs stop_and_wait+F1+F6 | makespan_s (both finished) | 15 | -44.35 | [-105.82, 17.11] | 4/15 | not met |
| swarmos vs stop_and_wait+F1+F6 | t90_censored_s | 40 | 11.26 | [-8.9, 31.42] | 29/40 | not met |
| swarmos vs stop_and_wait+F1+F6 | tasks_complete | 40 | 24.53 | [-16.1, 65.16] | 25/40 | not met |

- `baseline+F1+F6 vs stop_and_wait+F1+F6`: treatment-only DNF seeds [600001, 600005, 600007, 600008, 600013, 600014, 600032, 600036, 600038]; reference-only DNF seeds [600004, 600010, 600015, 600016, 600025, 600026, 600027, 600033, 600040]

- `swarmos vs stop_and_wait+F1+F6`: treatment-only DNF seeds none; reference-only DNF seeds [600002, 600003, 600004, 600009, 600010, 600011, 600015, 600016, 600017, 600018, 600019, 600021, 600024, 600025, 600026, 600027, 600028, 600029, 600030, 600031, 600033, 600034, 600037, 600039, 600040]

## overlap_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline+F1+F6 | 16/40 | 22.15 | 1708.005 | 0 | 0 | 0 | 85.825 | 0.6 | 1.125 | 4.85 | 1100.15 | 0.5542 | 0.7588 |
| stop_and_wait+F1+F6 | 19/40 | 21.38 | 1848.2625 | 0 | 0 | 0 | 108.3 | 96.95 | 1.475 | 4.625 | 763.675 | 0.6175 | 0.752 |
| swarmos | 0/40 | 24.0 | 481.4375 | 0 | 0 | 0 | 29.325 | 3.5 | 0.925 | 1.1 | 634.85 | 0.8122 | 0.754 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline+F1+F6 | 0.6 | 846.675 / 510.8 | 979.235 | 1.6937 | 3796.075 | 0.0 | 517.05 | 342.25 | 96.775 | 261.95 / 261.75 | 0.0 | None | 0 |
| stop_and_wait+F1+F6 | 0.525 | 806.2143 / 514.3 | 1085.04 | 1.5127 | 10612.95 | 0.0 | 349.975 | 364.325 | 154.775 | 276.5 / 276.025 | 0.0 | None | 0 |
| swarmos | 1.0 | 481.4375 / 466.1 | 411.07 | 3.0555 | 255.075 | 2426.375 | 282.8 | 166.125 | 45.575 | 36.925 / 35.55 | 74.55 | 0.0 | 0 |

| arm | floor entries (total) | floor pair-ticks (mean) | frozen pairs (total) | runs with a frozen pair | recovery actions (mean: stall releases + REROUTE) |
|---|---|---|---|---|---|
| baseline+F1+F6 | 0 | 0.0 | 0 | 0 | 518.175 |
| stop_and_wait+F1+F6 | 0 | 0.0 | 0 | 0 | 351.45 |
| swarmos | 0 | 0.0 | 0 | 0 | 283.725 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.4861, recall 0.9722, mean lead 16.1015 ticks (TP 1436, FP 1518, FN 41)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| baseline+F1+F6 vs stop_and_wait+F1+F6 | makespan_censored_s | 40 | -88.3 | [-164.2, -12.4] | 21/40 | not met |
| baseline+F1+F6 vs stop_and_wait+F1+F6 | makespan_s (both finished) | 10 | -11.03 | [-55.07, 33.01] | 7/10 | not met |
| baseline+F1+F6 vs stop_and_wait+F1+F6 | t90_censored_s | 40 | -59.35 | [-125.03, 6.32] | 19/40 | not met |
| baseline+F1+F6 vs stop_and_wait+F1+F6 | tasks_complete | 40 | 15.68 | [-1.74, 33.1] | 16/40 | not met |
| swarmos vs stop_and_wait+F1+F6 | makespan_censored_s | 40 | 48.89 | [35.33, 62.45] | 33/40 | MET |
| swarmos vs stop_and_wait+F1+F6 | makespan_s (both finished) | 21 | 17.48 | [1.36, 33.6] | 14/21 | not met |
| swarmos vs stop_and_wait+F1+F6 | t90_censored_s | 40 | 29.01 | [16.82, 41.21] | 30/40 | not met |
| swarmos vs stop_and_wait+F1+F6 | tasks_complete | 40 | 44.84 | [-12.27, 101.96] | 19/40 | not met |

- `baseline+F1+F6 vs stop_and_wait+F1+F6`: treatment-only DNF seeds [600003, 600010, 600011, 600016, 600017, 600022, 600029, 600033, 600034, 600036, 600037]; reference-only DNF seeds [600001, 600002, 600005, 600009, 600012, 600014, 600015, 600019, 600023, 600024, 600025, 600027, 600028, 600031]

- `swarmos vs stop_and_wait+F1+F6`: treatment-only DNF seeds none; reference-only DNF seeds [600001, 600002, 600005, 600008, 600009, 600012, 600014, 600015, 600019, 600021, 600023, 600024, 600025, 600027, 600028, 600031, 600032, 600039, 600040]
