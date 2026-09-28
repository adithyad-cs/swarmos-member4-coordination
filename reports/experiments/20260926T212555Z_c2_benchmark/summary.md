# Experiment `c2_benchmark`

- git: `a6e18041c8151077485fcdb63c6fc1769594cefa+uncommitted-changes`
- created: 20260926T212555Z
- seeds: [11, 13, 17, 19, 23, 29, 31, 37, 41]
- reference arm: `stop_and_wait`
- command: `PYTHONPATH=. python3 tools/run_experiment.py --name c2_benchmark --scenarios overlap_batch open_floor_batch --arms stop_and_wait baseline swarmos swarmos_lookahead swarmos_traffic noop --reference stop_and_wait --workers 4`

Makespan for runs that did not finish is CENSORED at the scenario cap (understates the failing arm's true time; never inflates an improvement).

## open_floor_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 3/9 | 35.33 | 1380.2778 | 0 | 0 | 0 | 432.3333 | 4.0 | 8.4444 | 2414.1111 | 0.9785 | 0.7529 |
| noop | 0/9 | 36.0 | 447.8889 | 639 | 707 | 9 | 0.0 | 0.0 | 0.0 | 102.4444 | 1.0268 | 0.0 |
| stop_and_wait | 3/9 | 35.44 | 1378.8111 | 0 | 0 | 0 | 201.0 | 199.7778 | 26.6667 | 1429.2222 | 0.9961 | 0.752 |
| swarmos | 8/9 | 33.22 | 2772.6889 | 0 | 16 | 0 | 347.6667 | 34.6667 | 489.8889 | 36588.1111 | 0.9934 | 0.722 |
| swarmos_lookahead | 8/9 | 33.22 | 2772.6889 | 0 | 16 | 0 | 347.6667 | 34.6667 | 489.8889 | 36588.1111 | 0.9934 | 0.722 |
| swarmos_traffic | 8/9 | 27.78 | 2745.5 | 0 | 19 | 0 | 2795.1111 | 1102.8889 | 944.1111 | 54286.5556 | 0.9712 | 0.731 |

Lookahead (observe-only scoring):

- `swarmos_lookahead`: precision 0.7103, recall 0.954, mean lead 16.4078 ticks (TP 1557, FP 635, FN 75)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| baseline vs stop_and_wait | makespan_censored_s | 9 | -81.58 | [-240.99, 77.84] | 3/9 | not met |
| baseline vs stop_and_wait | tasks_complete | 9 | -0.24 | [-3.44, 2.95] | 2/9 | not met |
| noop vs stop_and_wait | makespan_censored_s | 9 | 41.4 | [15.27, 67.53] | 9/9 | not met |
| noop vs stop_and_wait | tasks_complete | 9 | 1.62 | [-0.37, 3.61] | 3/9 | not met |
| swarmos vs stop_and_wait | makespan_censored_s | 9 | -245.12 | [-412.5, -77.74] | 0/9 | not met |
| swarmos vs stop_and_wait | tasks_complete | 9 | -6.27 | [-10.11, -2.43] | 0/9 | not met |
| swarmos_lookahead vs stop_and_wait | makespan_censored_s | 9 | -245.12 | [-412.5, -77.74] | 0/9 | not met |
| swarmos_lookahead vs stop_and_wait | tasks_complete | 9 | -6.27 | [-10.11, -2.43] | 0/9 | not met |
| swarmos_traffic vs stop_and_wait | makespan_censored_s | 9 | -242.4 | [-416.23, -68.56] | 0/9 | not met |
| swarmos_traffic vs stop_and_wait | tasks_complete | 9 | -21.55 | [-39.54, -3.56] | 0/9 | not met |

## overlap_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 0/9 | 24.0 | 569.2778 | 0 | 1 | 0 | 34.4444 | 3.4444 | 7.1111 | 539.4444 | 0.7251 | 0.7481 |
| noop | 0/9 | 24.0 | 311.4111 | 316 | 329 | 9 | 0.0 | 0.0 | 0.0 | 67.4444 | 1.0297 | 0.0 |
| stop_and_wait | 1/9 | 23.78 | 855.0667 | 0 | 0 | 0 | 34.0 | 31.6667 | 39.0 | 653.6667 | 0.6628 | 0.76 |
| swarmos | 4/9 | 22.67 | 1718.4778 | 0 | 6 | 0 | 510.5556 | 257.1111 | 238.2222 | 17028.1111 | 0.781 | 0.726 |
| swarmos_lookahead | 4/9 | 22.67 | 1718.4778 | 0 | 6 | 0 | 510.5556 | 257.1111 | 238.2222 | 17028.1111 | 0.781 | 0.726 |
| swarmos_traffic | 8/9 | 14.22 | 2721.5111 | 0 | 4 | 0 | 34.5556 | 4.1111 | 1146.3333 | 74327.4444 | 0.833 | 0.738 |

Lookahead (observe-only scoring):

- `swarmos_lookahead`: precision 0.176, recall 0.9002, mean lead 17.5756 ticks (TP 388, FP 1816, FN 43)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| baseline vs stop_and_wait | makespan_censored_s | 9 | 4.54 | [-29.58, 38.67] | 5/9 | not met |
| baseline vs stop_and_wait | tasks_complete | 9 | 1.01 | [-1.32, 3.34] | 1/9 | not met |
| noop vs stop_and_wait | makespan_censored_s | 9 | 49.84 | [34.61, 65.08] | 9/9 | MET |
| noop vs stop_and_wait | tasks_complete | 9 | 1.01 | [-1.32, 3.34] | 1/9 | not met |
| swarmos vs stop_and_wait | makespan_censored_s | 9 | -226.61 | [-449.63, -3.6] | 4/9 | not met |
| swarmos vs stop_and_wait | tasks_complete | 9 | -4.55 | [-11.15, 2.06] | 1/9 | not met |
| swarmos_lookahead vs stop_and_wait | makespan_censored_s | 9 | -226.61 | [-449.63, -3.6] | 4/9 | not met |
| swarmos_lookahead vs stop_and_wait | tasks_complete | 9 | -4.55 | [-11.15, 2.06] | 1/9 | not met |
| swarmos_traffic vs stop_and_wait | makespan_censored_s | 9 | -361.6 | [-544.77, -178.43] | 1/9 | not met |
| swarmos_traffic vs stop_and_wait | tasks_complete | 9 | -40.32 | [-57.29, -23.35] | 0/9 | not met |
