# Experiment `dev1_F1`

- git: `unknown`
- code identity (sha256): `3d7ee3b77ecdf6263c48c4df0422cdae2edc77f1c007d40aab3b56967715be02`
- created: 20260927T082855Z
- seeds: [700001, 700002, 700003, 700004, 700005, 700006, 700007, 700008, 700009, 700010, 700011, 700012, 700013, 700014, 700015, 700016, 700017, 700018, 700019, 700020]
- reference arm: `stop_and_wait+F1`
- command: `PYTHONPATH=. python3 tools/run_experiment.py --name dev1_F1 --scenarios overlap_batch open_floor_batch --arms stop_and_wait+F1 baseline+F1 swarmos+F1 --reference stop_and_wait+F1 --seeds 700001 700002 700003 700004 700005 700006 700007 700008 700009 700010 700011 700012 700013 700014 700015 700016 700017 700018 700019 700020 --workers 2 --out /tmp/claude-0/-home-user-swarmos-member4-coordination/a091c13b-17d3-58fe-ae28-470e6e7f7619/scratchpad/work/reports/experiments`

Makespan for runs that did not finish is CENSORED at the scenario cap. That understates the failing arm's true time, so it flatters the arm that finishes less; a censored target is marked MET only when the treatment never failed a seed the reference finished.

## open_floor_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline+F1 | 10/20 | 34.55 | 1891.57 | 0 | 1 | 0 | 904.75 | 3.75 | 140.85 | 3.3 | 10015.45 | 0.9448 | 0.7491 |
| stop_and_wait+F1 | 10/20 | 33.95 | 1782.815 | 0 | 0 | 0 | 514.75 | 467.0 | 33.9 | 2.9 | 3156.35 | 0.9924 | 0.752 |
| swarmos+F1 | 12/20 | 32.7 | 2097.74 | 0 | 0 | 0 | 2034.95 | 460.55 | 449.05 | 4.9 | 32178.45 | 0.9942 | 0.75 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline+F1 | 0.5 | 783.14 / 522.4 | 855.18 | 2.208 | 34552.15 | 0.0 | 4887.5 | 1265.0 | 771.25 | 716.45 / 715.35 | 0.0 | None | 0 |
| stop_and_wait+F1 | 0.5 | 565.63 / 540.2 | 1119.11 | 2.281 | 45014.4 | 0.0 | 1511.45 | 1506.95 | 345.1 | 1055.15 / 1053.6 | 0.0 | None | 0 |
| swarmos+F1 | 0.4 | 744.35 / 752.85 | 1801.47 | 1.535 | 38778.1 | 57899.7 | 15839.4 | 1462.7 | 2123.3 | 554.65 / 549.2 | 1674.85 | 0.0 | 0 |

| arm | floor entries (total) | floor pair-ticks (mean) | frozen pairs (total) | runs with a frozen pair | recovery actions (mean: stall releases + REROUTE) |
|---|---|---|---|---|---|
| baseline+F1 | 1 | 0.05 | 0 | 0 | 5028.35 |
| stop_and_wait+F1 | 0 | 0.0 | 0 | 0 | 1545.35 |
| swarmos+F1 | 0 | 0.0 | 0 | 0 | 16288.45 |

Lookahead (observe-only scoring):

- `swarmos+F1`: precision 0.3209, recall 0.9617, mean lead 16.192 ticks (TP 10668, FP 22577, FN 425)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| baseline+F1 vs stop_and_wait+F1 | makespan_censored_s | 20 | -74.81 | [-167.4, 17.78] | 9/20 | not met |
| baseline+F1 vs stop_and_wait+F1 | makespan_s (both finished) | 6 | 8.15 | [-4.6, 20.89] | 5/6 | not met |
| baseline+F1 vs stop_and_wait+F1 | t90_censored_s | 20 | -9.12 | [-59.15, 40.9] | 12/20 | not met |
| baseline+F1 vs stop_and_wait+F1 | tasks_complete | 20 | 2.42 | [-1.9, 6.74] | 6/20 | not met |
| swarmos+F1 vs stop_and_wait+F1 | makespan_censored_s | 20 | -122.86 | [-224.95, -20.77] | 4/20 | not met |
| swarmos+F1 vs stop_and_wait+F1 | makespan_s (both finished) | 4 | -39.56 | [-89.64, 10.52] | 0/4 | not met |
| swarmos+F1 vs stop_and_wait+F1 | t90_censored_s | 20 | -181.67 | [-300.41, -62.94] | 3/20 | not met |
| swarmos+F1 vs stop_and_wait+F1 | tasks_complete | 20 | -2.59 | [-10.48, 5.3] | 4/20 | not met |

- `baseline+F1 vs stop_and_wait+F1`: treatment-only DNF seeds [700003, 700016, 700017, 700020]; reference-only DNF seeds [700001, 700010, 700011, 700019]

- `swarmos+F1 vs stop_and_wait+F1`: treatment-only DNF seeds [700002, 700005, 700012, 700014, 700016, 700017]; reference-only DNF seeds [700001, 700009, 700011, 700015]

## overlap_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline+F1 | 7/20 | 21.65 | 1535.975 | 0 | 0 | 0 | 92.0 | 0.75 | 1.3 | 6.4 | 516.7 | 0.5499 | 0.7531 |
| stop_and_wait+F1 | 11/20 | 21.6 | 2061.485 | 0 | 0 | 0 | 103.15 | 97.25 | 27.7 | 5.0 | 1427.9 | 0.5278 | 0.752 |
| swarmos+F1 | 3/20 | 23.65 | 1010.295 | 0 | 0 | 0 | 228.8 | 85.35 | 55.6 | 3.6 | 4973.0 | 0.6668 | 0.7514 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline+F1 | 0.65 | 747.6538 / 554.4 | 1068.975 | 1.706 | 1784.4 | 0.0 | 225.45 | 342.05 | 106.35 | 253.1 / 253.0 | 0.0 | None | 0 |
| stop_and_wait+F1 | 0.45 | 914.4111 / 611.6 | 1129.695 | 1.261 | 20001.75 | 0.0 | 668.8 | 533.8 | 302.25 | 480.1 / 479.05 | 0.0 | None | 0 |
| swarmos+F1 | 0.85 | 659.1706 / 623.8 | 661.83 | 2.072 | 4715.9 | 12278.65 | 2427.85 | 204.15 | 541.1 | 58.4 / 56.5 | 177.25 | 0.0 | 0 |

| arm | floor entries (total) | floor pair-ticks (mean) | frozen pairs (total) | runs with a frozen pair | recovery actions (mean: stall releases + REROUTE) |
|---|---|---|---|---|---|
| baseline+F1 | 0 | 0.0 | 0 | 0 | 226.75 |
| stop_and_wait+F1 | 0 | 0.0 | 0 | 0 | 696.5 |
| swarmos+F1 | 0 | 0.0 | 0 | 0 | 2483.45 |

Lookahead (observe-only scoring):

- `swarmos+F1`: precision 0.3084, recall 0.9255, mean lead 16.4915 ticks (TP 1081, FP 2424, FN 87)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| baseline+F1 vs stop_and_wait+F1 | makespan_censored_s | 20 | -22.91 | [-99.75, 53.93] | 11/20 | not met |
| baseline+F1 vs stop_and_wait+F1 | makespan_s (both finished) | 6 | 13.6 | [-31.7, 58.89] | 4/6 | not met |
| baseline+F1 vs stop_and_wait+F1 | t90_censored_s | 20 | -43.62 | [-123.85, 36.62] | 10/20 | not met |
| baseline+F1 vs stop_and_wait+F1 | tasks_complete | 20 | 20.73 | [-32.92, 74.38] | 8/20 | not met |
| swarmos+F1 vs stop_and_wait+F1 | makespan_censored_s | 20 | 8.51 | [-62.01, 79.04] | 14/20 | not met |
| swarmos+F1 vs stop_and_wait+F1 | makespan_s (both finished) | 7 | -1.29 | [-18.43, 15.85] | 4/7 | not met |
| swarmos+F1 vs stop_and_wait+F1 | t90_censored_s | 20 | -1.09 | [-43.15, 40.97] | 10/20 | not met |
| swarmos+F1 vs stop_and_wait+F1 | tasks_complete | 20 | 31.26 | [-20.98, 83.51] | 10/20 | not met |

- `baseline+F1 vs stop_and_wait+F1`: treatment-only DNF seeds [700006, 700015, 700019]; reference-only DNF seeds [700001, 700002, 700004, 700009, 700013, 700014, 700018]

- `swarmos+F1 vs stop_and_wait+F1`: treatment-only DNF seeds [700012, 700017]; reference-only DNF seeds [700001, 700002, 700004, 700005, 700009, 700010, 700011, 700013, 700014, 700020]
