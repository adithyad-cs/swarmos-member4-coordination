# Experiment `deadlock_breakers`

- git: `a6e18041c8151077485fcdb63c6fc1769594cefa+uncommitted-changes`
- created: 20260926T214450Z
- seeds: [11, 13, 17, 19, 23, 29, 31, 37, 41]
- reference arm: `stop_and_wait`
- command: `PYTHONPATH=. python3 tools/run_experiment.py --name deadlock_breakers --scenarios overlap_batch open_floor_batch --arms stop_and_wait swarmos swarmos_mhb swarmos_mhb_sep --reference stop_and_wait --workers 4`

Makespan for runs that did not finish is CENSORED at the scenario cap (understates the failing arm's true time; never inflates an improvement).

## open_floor_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| stop_and_wait | 3/9 | 35.44 | 1378.8111 | 0 | 0 | 0 | 201.0 | 199.7778 | 26.6667 | 1429.2222 | 0.9961 | 0.752 |
| swarmos | 8/9 | 33.22 | 2772.6889 | 0 | 16 | 0 | 347.6667 | 34.6667 | 489.8889 | 36588.1111 | 0.9934 | 0.722 |
| swarmos_mhb | 9/9 | 30.33 | 3000.0 | 0 | 16 | 0 | 2559.6667 | 201.4444 | 852.7778 | 79575.2222 | 0.9996 | 0.724 |
| swarmos_mhb_sep | 4/9 | 32.78 | 1725.4444 | 0 | 24 | 0 | 1862.8889 | 101.2222 | 473.1111 | 44134.0 | 0.9974 | 0.724 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.7103, recall 0.954, mean lead 16.4078 ticks (TP 1557, FP 635, FN 75)
- `swarmos_mhb`: precision 0.2902, recall 0.8732, mean lead 17.3144 ticks (TP 4077, FP 9973, FN 592)
- `swarmos_mhb_sep`: precision 0.2596, recall 0.7495, mean lead 16.8522 ticks (TP 3166, FP 9030, FN 1058)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| swarmos vs stop_and_wait | makespan_censored_s | 9 | -245.12 | [-412.5, -77.74] | 0/9 | not met |
| swarmos vs stop_and_wait | tasks_complete | 9 | -6.27 | [-10.11, -2.43] | 0/9 | not met |
| swarmos_mhb vs stop_and_wait | makespan_censored_s | 9 | -286.56 | [-453.04, -120.08] | 0/9 | not met |
| swarmos_mhb vs stop_and_wait | tasks_complete | 9 | -14.21 | [-23.65, -4.76] | 0/9 | not met |
| swarmos_mhb_sep vs stop_and_wait | makespan_censored_s | 9 | -138.36 | [-315.55, 38.84] | 3/9 | not met |
| swarmos_mhb_sep vs stop_and_wait | tasks_complete | 9 | -7.43 | [-16.49, 1.62] | 2/9 | not met |

## overlap_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| stop_and_wait | 1/9 | 23.78 | 855.0667 | 0 | 0 | 0 | 34.0 | 31.6667 | 39.0 | 653.6667 | 0.6628 | 0.76 |
| swarmos | 4/9 | 22.67 | 1718.4778 | 0 | 6 | 0 | 510.5556 | 257.1111 | 238.2222 | 17028.1111 | 0.781 | 0.726 |
| swarmos_mhb | 4/9 | 23.22 | 1653.2667 | 0 | 6 | 0 | 97.0 | 14.8889 | 139.0 | 21200.2222 | 0.7354 | 0.722 |
| swarmos_mhb_sep | 0/9 | 24.0 | 619.3556 | 0 | 6 | 0 | 77.5556 | 8.1111 | 6.7778 | 1668.7778 | 0.7313 | 0.722 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.176, recall 0.9002, mean lead 17.5756 ticks (TP 388, FP 1816, FN 43)
- `swarmos_mhb`: precision 0.6207, recall 0.9231, mean lead 18.1644 ticks (TP 468, FP 286, FN 39)
- `swarmos_mhb_sep`: precision 0.6329, recall 0.9317, mean lead 16.7556 ticks (TP 450, FP 261, FN 33)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| swarmos vs stop_and_wait | makespan_censored_s | 9 | -226.61 | [-449.63, -3.6] | 4/9 | not met |
| swarmos vs stop_and_wait | tasks_complete | 9 | -4.55 | [-11.15, 2.06] | 1/9 | not met |
| swarmos_mhb vs stop_and_wait | makespan_censored_s | 9 | -197.11 | [-400.89, 6.66] | 3/9 | not met |
| swarmos_mhb vs stop_and_wait | tasks_complete | 9 | -2.23 | [-6.64, 2.18] | 1/9 | not met |
| swarmos_mhb_sep vs stop_and_wait | makespan_censored_s | 9 | -5.54 | [-42.31, 31.24] | 4/9 | not met |
| swarmos_mhb_sep vs stop_and_wait | tasks_complete | 9 | 1.01 | [-1.32, 3.34] | 1/9 | not met |
