# Experiment `c2_smoke`

- git: `a6e18041c8151077485fcdb63c6fc1769594cefa+uncommitted-changes`
- code identity (sha256): `e9724d49657739d0da9aaae49bd262088207faf1a28ad4af4682365f30b5a9ea`
- created: 20260927T001148Z
- seeds: [101, 102, 103]
- reference arm: `stop_and_wait`
- command: `PYTHONPATH=. python3 tools/run_experiment.py --name c2_smoke --scenarios overlap_batch open_floor_batch --arms stop_and_wait baseline swarmos swarmos_mhb --reference stop_and_wait --seeds 101 102 103 --workers 4`

Makespan for runs that did not finish is CENSORED at the scenario cap. That understates the failing arm's true time, so it flatters the arm that finishes less; a censored target is marked MET only when the treatment never failed a seed the reference finished.

## open_floor_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 2/3 | 31.0 | 2205.4333 | 0 | 0 | 0 | 1666.0 | 1.6667 | 2.6667 | 4.3333 | 10740.0 | 0.9698 | 0.7643 |
| stop_and_wait | 2/3 | 34.67 | 2150.3 | 0 | 0 | 0 | 248.3333 | 247.0 | 128.6667 | 2.6667 | 6498.3333 | 0.9776 | 0.7607 |
| swarmos | 3/3 | 27.33 | 3000.0 | 0 | 11 | 0 | 4461.6667 | 935.6667 | 1116.6667 | 15.0 | 69731.0 | 1.0003 | 0.7251 |
| swarmos_mhb | 2/3 | 33.0 | 2207.3 | 0 | 4 | 0 | 720.6667 | 262.3333 | 485.6667 | 3.3333 | 55177.6667 | 1.0017 | 0.746 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.3333 | 616.3 / 616.3 | 1344.6667 | 1.5467 | 38302.6667 | 0.0 | 5320.0 | 6133.3333 | 246.0 | 4069.3333 / 4068.3333 | 0.0 | None | 0 |
| stop_and_wait | 0.3333 | 450.9 / 450.9 | 513.1667 | 2.05 | 91360.0 | 0.0 | 3134.6667 | 580.6667 | 1062.0 | 333.6667 / 329.6667 | 0.0 | None | 0 |
| swarmos | 0.0 | None / None | 3000.0 | 0.5467 | 89570.3333 | 125124.6667 | 34324.0 | 3401.3333 | 4005.6667 | 1808.3333 / 1801.0 | 4805.0 | 0.0 | 0 |
| swarmos_mhb | 0.3333 | 621.9 / 621.9 | 1347.7333 | 1.5767 | 74066.3333 | 31962.6667 | 27342.6667 | 536.3333 | 8192.3333 | 622.6667 / 618.0 | 892.6667 | 0.0 | 0 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.3437, recall 0.9054, mean lead 15.6533 ticks (TP 4912, FP 9380, FN 513)
- `swarmos_mhb`: precision 0.5029, recall 0.6574, mean lead 14.0133 ticks (TP 1228, FP 1214, FN 640)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| baseline vs stop_and_wait | makespan_censored_s | 3 | -161.96 | [-1035.42, 711.5] | 1/3 | not met |
| baseline vs stop_and_wait | t90_censored_s | 3 | -155.03 | [-782.21, 472.15] | 1/3 | not met |
| baseline vs stop_and_wait | tasks_complete | 3 | -10.68 | [-59.43, 38.08] | 1/3 | not met |
| swarmos vs stop_and_wait | makespan_censored_s | 3 | -188.45 | [-999.33, 622.43] | 0/3 | not met |
| swarmos vs stop_and_wait | t90_censored_s | 3 | -499.93 | [-807.16, -192.7] | 0/3 | not met |
| swarmos vs stop_and_wait | tasks_complete | 3 | -21.35 | [-43.38, 0.68] | 0/3 | not met |
| swarmos_mhb vs stop_and_wait | makespan_censored_s | 3 | -162.02 | [-1035.32, 711.28] | 1/3 | not met |
| swarmos_mhb vs stop_and_wait | t90_censored_s | 3 | -154.77 | [-780.46, 470.93] | 1/3 | not met |
| swarmos_mhb vs stop_and_wait | tasks_complete | 3 | -4.85 | [-34.41, 24.72] | 1/3 | not met |

- `baseline vs stop_and_wait`: treatment-only DNF seeds [103]; reference-only DNF seeds [102]

- `swarmos vs stop_and_wait`: treatment-only DNF seeds [103]; reference-only DNF seeds none

- `swarmos_mhb vs stop_and_wait`: treatment-only DNF seeds [103]; reference-only DNF seeds [102]

## overlap_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 2/3 | 19.0 | 2121.6 | 0 | 0 | 0 | 109.6667 | 0.0 | 0.0 | 4.0 | 512.6667 | 0.5265 | 0.772 |
| stop_and_wait | 2/3 | 18.67 | 2176.1333 | 0 | 0 | 0 | 120.6667 | 108.3333 | 0.6667 | 5.0 | 509.0 | 0.4619 | 0.7864 |
| swarmos | 0/3 | 24.0 | 780.8 | 0 | 1 | 0 | 61.0 | 2.0 | 1.0 | 4.0 | 1675.0 | 0.6332 | 0.7444 |
| swarmos_mhb | 1/3 | 23.33 | 1428.5 | 0 | 0 | 0 | 76.6667 | 3.0 | 3.3333 | 4.0 | 2902.3333 | 0.6649 | 0.755 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.3333 | 364.8 / 364.8 | 1279.5667 | 1.5367 | 1737.3333 | 0.0 | 227.6667 | 315.6667 | 104.6667 | 210.3333 / 210.3333 | 0.0 | None | 0 |
| stop_and_wait | 0.3333 | 528.4 / 528.4 | 1411.4333 | 1.12 | 7454.6667 | 0.0 | 225.6667 | 581.6667 | 124.0 | 479.6667 / 479.3333 | 0.0 | None | 0 |
| swarmos | 1.0 | 780.8 / 743.5 | 508.2 | 2.0133 | 590.6667 | 7013.0 | 803.0 | 195.6667 | 42.6667 | 47.3333 / 45.6667 | 71.0 | 0.0 | 0 |
| swarmos_mhb | 0.6667 | 642.75 / 642.75 | 552.7 | 1.7133 | 778.3333 | 11800.0 | 1414.3333 | 263.0 | 110.6667 | 65.3333 / 63.6667 | 83.6667 | 0.0 | 0 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.6381, recall 0.9437, mean lead 17.14 ticks (TP 134, FP 76, FN 8)
- `swarmos_mhb`: precision 0.7331, recall 0.9388, mean lead 16.4133 ticks (TP 184, FP 67, FN 12)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| baseline vs stop_and_wait | makespan_censored_s | 3 | -126.64 | [-868.61, 615.34] | 1/3 | not met |
| baseline vs stop_and_wait | t90_censored_s | 3 | 17.24 | [-61.24, 95.72] | 1/3 | not met |
| baseline vs stop_and_wait | tasks_complete | 3 | 1.64 | [-15.2, 18.48] | 1/3 | not met |
| swarmos vs stop_and_wait | makespan_censored_s | 3 | 17.97 | [-244.47, 280.41] | 2/3 | not met |
| swarmos vs stop_and_wait | t90_censored_s | 3 | 36.54 | [-67.95, 141.04] | 3/3 | not met |
| swarmos vs stop_and_wait | tasks_complete | 3 | 49.7 | [-144.92, 244.31] | 2/3 | not met |
| swarmos_mhb vs stop_and_wait | makespan_censored_s | 3 | 11.74 | [-153.22, 176.69] | 1/3 | not met |
| swarmos_mhb vs stop_and_wait | t90_censored_s | 3 | 23.24 | [-138.55, 185.04] | 2/3 | not met |
| swarmos_mhb vs stop_and_wait | tasks_complete | 3 | 46.67 | [-154.14, 247.47] | 1/3 | not met |

- `baseline vs stop_and_wait`: treatment-only DNF seeds [101]; reference-only DNF seeds [102]

- `swarmos vs stop_and_wait`: treatment-only DNF seeds none; reference-only DNF seeds [102, 103]

- `swarmos_mhb vs stop_and_wait`: treatment-only DNF seeds none; reference-only DNF seeds [103]
