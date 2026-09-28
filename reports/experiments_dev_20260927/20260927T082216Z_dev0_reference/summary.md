# Experiment `dev0_reference`

- git: `unknown`
- code identity (sha256): `fe0411531a831eb40bb1d93790790b7da61021536567043bb0969ce9f66f742e`
- created: 20260927T082216Z
- seeds: [700001, 700002, 700003, 700004, 700005, 700006, 700007, 700008, 700009, 700010, 700011, 700012, 700013, 700014, 700015, 700016, 700017, 700018, 700019, 700020]
- reference arm: `stop_and_wait`
- command: `PYTHONPATH=. python3 tools/run_experiment.py --name dev0_reference --scenarios overlap_batch open_floor_batch --arms stop_and_wait baseline swarmos --reference stop_and_wait --seeds 700001 700002 700003 700004 700005 700006 700007 700008 700009 700010 700011 700012 700013 700014 700015 700016 700017 700018 700019 700020 --workers 3 --out /tmp/claude-0/-home-user-swarmos-member4-coordination/a091c13b-17d3-58fe-ae28-470e6e7f7619/scratchpad/dev/reports/experiments`

Makespan for runs that did not finish is CENSORED at the scenario cap. That understates the failing arm's true time, so it flatters the arm that finishes less; a censored target is marked MET only when the treatment never failed a seed the reference finished.

## open_floor_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 10/20 | 34.4 | 1892.36 | 0 | 1 | 0 | 810.6 | 12.2 | 153.95 | 3.4 | 10424.65 | 0.9449 | 0.7491 |
| stop_and_wait | 10/20 | 33.8 | 1782.395 | 0 | 1 | 0 | 514.2 | 468.25 | 51.0 | 3.1 | 3657.2 | 0.9908 | 0.748 |
| swarmos | 20/20 | 29.8 | 3000.0 | 0 | 49 | 0 | 1916.8 | 418.3 | 925.75 | 8.6 | 61094.45 | 0.9899 | 0.72 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.5 | 784.72 / 523.0 | 985.18 | 2.199 | 35984.4 | 0.0 | 5079.5 | 1400.75 | 914.55 | 780.5 / 779.3 | 0.0 | None | 0 |
| stop_and_wait | 0.5 | 564.79 / 540.2 | 1238.065 | 2.28 | 52186.5 | 0.0 | 1753.5 | 1497.95 | 355.5 | 1041.0 / 1039.15 | 0.0 | None | 0 |
| swarmos | 0.0 | None / None | 2314.78 | 0.596 | 78955.85 | 103408.65 | 30092.35 | 863.6 | 5585.9 | 298.75 / 293.45 | 995.7 | 0.0 | 0 |

| arm | floor entries (total) | floor pair-ticks (mean) | frozen pairs (total) | runs with a frozen pair | recovery actions (mean: stall releases + REROUTE) |
|---|---|---|---|---|---|
| baseline | 1 | 0.05 | 0 | 0 | 5233.45 |
| stop_and_wait | 1 | 0.1 | 0 | 0 | 1804.5 |
| swarmos | 49 | 62341.1 | 48 | 18 | 31018.1 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.281, recall 0.9265, mean lead 21.4715 ticks (TP 5536, FP 14163, FN 439)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| baseline vs stop_and_wait | makespan_censored_s | 20 | -60.69 | [-147.49, 26.12] | 9/20 | not met |
| baseline vs stop_and_wait | makespan_s (both finished) | 7 | 9.18 | [-1.75, 20.1] | 6/7 | not met |
| baseline vs stop_and_wait | t90_censored_s | 20 | 7.52 | [-6.23, 21.27] | 11/20 | not met |
| baseline vs stop_and_wait | tasks_complete | 20 | 2.48 | [-2.02, 6.99] | 5/20 | not met |
| swarmos vs stop_and_wait | makespan_censored_s | 20 | -222.83 | [-333.96, -111.7] | 0/20 | not met |
| swarmos vs stop_and_wait | t90_censored_s | 20 | -271.25 | [-402.73, -139.77] | 2/20 | not met |
| swarmos vs stop_and_wait | tasks_complete | 20 | -10.4 | [-19.51, -1.29] | 3/20 | not met |

- `baseline vs stop_and_wait`: treatment-only DNF seeds [700003, 700017, 700020]; reference-only DNF seeds [700001, 700010, 700011]

- `swarmos vs stop_and_wait`: treatment-only DNF seeds [700002, 700003, 700005, 700006, 700008, 700009, 700012, 700014, 700017, 700020]; reference-only DNF seeds none

## overlap_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 8/20 | 21.8 | 1664.01 | 0 | 0 | 0 | 93.05 | 0.75 | 1.3 | 6.45 | 522.6 | 0.5162 | 0.7531 |
| stop_and_wait | 11/20 | 21.5 | 2061.485 | 0 | 0 | 0 | 104.65 | 98.9 | 44.3 | 5.15 | 1527.7 | 0.5223 | 0.752 |
| swarmos | 9/20 | 22.05 | 1667.35 | 0 | 10 | 0 | 304.3 | 133.75 | 166.45 | 5.05 | 13062.7 | 0.6561 | 0.726 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.6 | 773.35 / 570.5 | 1052.59 | 1.569 | 1803.35 | 0.0 | 228.2 | 344.4 | 109.6 | 254.5 / 254.45 | 0.0 | None | 0 |
| stop_and_wait | 0.45 | 914.4111 / 611.6 | 1246.07 | 1.259 | 21208.8 | 0.0 | 710.8 | 554.75 | 401.95 | 458.75 / 457.85 | 0.0 | None | 0 |
| swarmos | 0.55 | 577.0 / 580.1 | 838.765 | 1.6075 | 14569.0 | 30715.45 | 6424.2 | 274.85 | 1727.1 | 74.45 / 71.85 | 150.3 | 0.0 | 0 |

| arm | floor entries (total) | floor pair-ticks (mean) | frozen pairs (total) | runs with a frozen pair | recovery actions (mean: stall releases + REROUTE) |
|---|---|---|---|---|---|
| baseline | 0 | 0.0 | 0 | 0 | 229.5 |
| stop_and_wait | 0 | 0.0 | 0 | 0 | 755.1 |
| swarmos | 10 | 12752.05 | 10 | 8 | 6590.65 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.4673, recall 0.9349, mean lead 16.7315 ticks (TP 1392, FP 1587, FN 97)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| baseline vs stop_and_wait | makespan_censored_s | 20 | -54.52 | [-154.87, 45.83] | 11/20 | not met |
| baseline vs stop_and_wait | makespan_s (both finished) | 5 | 18.01 | [-39.99, 76.0] | 4/5 | not met |
| baseline vs stop_and_wait | t90_censored_s | 20 | -27.33 | [-98.97, 44.32] | 11/20 | not met |
| baseline vs stop_and_wait | tasks_complete | 20 | 21.85 | [-31.67, 75.38] | 8/20 | not met |
| swarmos vs stop_and_wait | makespan_censored_s | 20 | -59.46 | [-156.79, 37.86] | 10/20 | not met |
| swarmos vs stop_and_wait | makespan_s (both finished) | 4 | 11.78 | [-55.09, 78.65] | 3/4 | not met |
| swarmos vs stop_and_wait | t90_censored_s | 20 | -30.0 | [-101.15, 41.15] | 10/20 | not met |
| swarmos vs stop_and_wait | tasks_complete | 20 | 24.86 | [-28.78, 78.49] | 9/20 | not met |

- `baseline vs stop_and_wait`: treatment-only DNF seeds [700006, 700008, 700015, 700019]; reference-only DNF seeds [700001, 700002, 700004, 700009, 700013, 700014, 700018]

- `swarmos vs stop_and_wait`: treatment-only DNF seeds [700003, 700007, 700012, 700016, 700017]; reference-only DNF seeds [700002, 700005, 700009, 700010, 700013, 700014, 700018]
