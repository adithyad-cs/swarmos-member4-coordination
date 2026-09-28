# Experiment `c2_frozen`

- git: `a6e18041c8151077485fcdb63c6fc1769594cefa+uncommitted-changes`
- code identity (sha256): `ba4086a693013487342c7832c6e9ff23bad8c7a8247fffb2e878091664179656`
- created: 20260927T045112Z
- seeds: [900001, 900002, 900003, 900004, 900005, 900006, 900007, 900008, 900009, 900010, 900011, 900012, 900013, 900014, 900015, 900016, 900017, 900018, 900019, 900020, 900021, 900022, 900023, 900024, 900025, 900026, 900027, 900028, 900029, 900030, 900031, 900032, 900033, 900034, 900035, 900036, 900037, 900038, 900039, 900040]
- reference arm: `stop_and_wait`
- command: `PYTHONPATH=. python3 tools/run_experiment.py --name c2_frozen --scenarios overlap_batch open_floor_batch --arms stop_and_wait baseline swarmos swarmos_mhb --reference stop_and_wait --seeds 900001 900002 900003 900004 900005 900006 900007 900008 900009 900010 900011 900012 900013 900014 900015 900016 900017 900018 900019 900020 900021 900022 900023 900024 900025 900026 900027 900028 900029 900030 900031 900032 900033 900034 900035 900036 900037 900038 900039 900040 --workers 4 --target-pct 20 --expect-identity ba4086a693013487342c7832c6e9ff23bad8c7a8247fffb2e878091664179656`

Makespan for runs that did not finish is CENSORED at the scenario cap. That understates the failing arm's true time, so it flatters the arm that finishes less; a censored target is marked MET only when the treatment never failed a seed the reference finished.

## open_floor_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 23/40 | 33.6 | 1964.0225 | 0 | 2 | 0 | 908.3 | 35.9 | 204.75 | 4.7 | 12889.8 | 0.9261 | 0.7447 |
| stop_and_wait | 31/40 | 31.4 | 2465.02 | 0 | 2 | 0 | 670.95 | 649.125 | 202.45 | 5.05 | 6140.825 | 0.987 | 0.7402 |
| swarmos | 38/40 | 29.88 | 2887.645 | 0 | 98 | 0 | 1852.375 | 501.5 | 927.25 | 10.175 | 59377.75 | 0.9928 | 0.715 |
| swarmos_mhb | 32/40 | 31.05 | 2534.065 | 0 | 70 | 0 | 1291.2 | 251.3 | 704.9 | 6.575 | 65352.625 | 1.0038 | 0.7221 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.425 | 562.4059 / 532.9 | 1192.99 | 2.0428 | 44619.6 | 0.0 | 6294.95 | 2037.925 | 1301.225 | 1511.375 / 1509.8 | 0.0 | None | 0 |
| stop_and_wait | 0.225 | 622.3111 / 585.6 | 1586.445 | 1.298 | 85877.075 | 0.0 | 2922.225 | 1757.725 | 642.675 | 1205.1 / 1202.625 | 0.0 | None | 0 |
| swarmos | 0.05 | 752.9 / 752.9 | 2246.295 | 0.7055 | 76538.15 | 106191.275 | 29228.3 | 1198.45 | 5263.875 | 495.5 / 489.975 | 1100.175 | 0.0 | 0 |
| swarmos_mhb | 0.2 | 670.325 / 650.55 | 1694.1125 | 1.1275 | 89285.9 | 41032.1 | 32360.025 | 898.825 | 6246.275 | 519.35 / 514.55 | 1150.025 | 0.0 | 0 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.4173, recall 0.9008, mean lead 17.3502 ticks (TP 17854, FP 24929, FN 1966)
- `swarmos_mhb`: precision 0.4133, recall 0.8824, mean lead 15.7483 ticks (TP 18331, FP 26017, FN 2443)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| baseline vs stop_and_wait | makespan_censored_s | 40 | -33.06 | [-92.5, 26.39] | 16/40 | not met |
| baseline vs stop_and_wait | makespan_s (both finished) | 4 | 16.41 | [-15.34, 48.15] | 3/4 | not met |
| baseline vs stop_and_wait | t90_censored_s | 40 | -48.74 | [-113.02, 15.54] | 22/40 | not met |
| baseline vs stop_and_wait | tasks_complete | 40 | 13.35 | [2.12, 24.59] | 22/40 | not met |
| swarmos vs stop_and_wait | makespan_censored_s | 40 | -89.3 | [-150.22, -28.38] | 2/40 | not met |
| swarmos vs stop_and_wait | t90_censored_s | 40 | -175.25 | [-255.44, -95.06] | 7/40 | not met |
| swarmos vs stop_and_wait | tasks_complete | 40 | 2.37 | [-10.74, 15.48] | 12/40 | not met |
| swarmos_mhb vs stop_and_wait | makespan_censored_s | 40 | -56.58 | [-108.37, -4.79] | 6/40 | not met |
| swarmos_mhb vs stop_and_wait | makespan_s (both finished) | 2 | -39.17 | [-458.8, 380.46] | 0/2 | not met |
| swarmos_mhb vs stop_and_wait | t90_censored_s | 40 | -117.25 | [-193.45, -41.06] | 14/40 | not met |
| swarmos_mhb vs stop_and_wait | tasks_complete | 40 | 7.02 | [-8.52, 22.55] | 18/40 | not met |

- `baseline vs stop_and_wait`: treatment-only DNF seeds [900001, 900011, 900021, 900027, 900030]; reference-only DNF seeds [900002, 900004, 900006, 900010, 900020, 900022, 900024, 900025, 900028, 900037, 900038, 900039, 900040]

- `swarmos vs stop_and_wait`: treatment-only DNF seeds [900001, 900007, 900008, 900011, 900012, 900014, 900021, 900027, 900030]; reference-only DNF seeds [900015, 900024]

- `swarmos_mhb vs stop_and_wait`: treatment-only DNF seeds [900008, 900011, 900012, 900014, 900021, 900027, 900030]; reference-only DNF seeds [900013, 900015, 900017, 900022, 900024, 900039]

## overlap_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 20/40 | 20.95 | 1814.2475 | 0 | 0 | 0 | 98.875 | 0.7 | 6.525 | 4.85 | 1158.35 | 0.5848 | 0.7573 |
| stop_and_wait | 19/40 | 22.1 | 1843.705 | 0 | 0 | 0 | 126.85 | 123.0 | 22.15 | 5.8 | 1300.375 | 0.551 | 0.7527 |
| swarmos | 20/40 | 23.02 | 1789.8375 | 0 | 32 | 0 | 312.275 | 47.85 | 157.55 | 3.625 | 16202.55 | 0.688 | 0.72 |
| swarmos_mhb | 18/40 | 22.85 | 1652.3575 | 0 | 21 | 0 | 412.125 | 12.75 | 176.0 | 3.925 | 20544.975 | 0.6924 | 0.7221 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.5 | 628.495 / 514.25 | 1096.31 | 1.5413 | 3970.275 | 0.0 | 545.45 | 342.85 | 380.5 | 246.75 / 246.45 | 0.0 | None | 0 |
| stop_and_wait | 0.525 | 797.5333 / 606.9 | 1344.575 | 1.45 | 18068.325 | 0.0 | 607.275 | 473.8 | 273.2 | 384.275 / 383.575 | 0.0 | None | 0 |
| swarmos | 0.5 | 579.675 / 590.7 | 752.24 | 1.4872 | 18471.5 | 32586.55 | 7999.325 | 260.3 | 2331.75 | 142.7 / 140.175 | 226.9 | 0.0 | 0 |
| swarmos_mhb | 0.55 | 549.7409 / 538.45 | 903.82 | 1.6835 | 27181.0 | 14394.725 | 10361.725 | 229.075 | 3177.75 | 113.925 / 111.5 | 186.525 | 0.0 | 0 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.5818, recall 0.8973, mean lead 18.6135 ticks (TP 5122, FP 3682, FN 586)
- `swarmos_mhb`: precision 0.5469, recall 0.7944, mean lead 16.1852 ticks (TP 3620, FP 2999, FN 937)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| baseline vs stop_and_wait | makespan_censored_s | 40 | -73.44 | [-132.99, -13.88] | 13/40 | not met |
| baseline vs stop_and_wait | makespan_s (both finished) | 9 | -2.19 | [-25.78, 21.4] | 2/9 | not met |
| baseline vs stop_and_wait | t90_censored_s | 40 | -72.86 | [-143.6, -2.12] | 21/40 | not met |
| baseline vs stop_and_wait | tasks_complete | 40 | 6.77 | [-20.67, 34.22] | 14/40 | not met |
| swarmos vs stop_and_wait | makespan_censored_s | 40 | -85.34 | [-155.26, -15.41] | 15/40 | not met |
| swarmos vs stop_and_wait | makespan_s (both finished) | 11 | 4.62 | [-28.87, 38.11] | 6/11 | not met |
| swarmos vs stop_and_wait | t90_censored_s | 40 | -9.22 | [-50.26, 31.82] | 22/40 | not met |
| swarmos vs stop_and_wait | tasks_complete | 40 | 15.28 | [-10.35, 40.91] | 15/40 | not met |
| swarmos_mhb vs stop_and_wait | makespan_censored_s | 40 | -69.89 | [-140.28, 0.51] | 16/40 | not met |
| swarmos_mhb vs stop_and_wait | makespan_s (both finished) | 13 | 7.87 | [-22.47, 38.22] | 7/13 | not met |
| swarmos_mhb vs stop_and_wait | t90_censored_s | 40 | -27.57 | [-76.73, 21.59] | 20/40 | not met |
| swarmos_mhb vs stop_and_wait | tasks_complete | 40 | 13.24 | [-8.86, 35.34] | 12/40 | not met |

- `baseline vs stop_and_wait`: treatment-only DNF seeds [900001, 900003, 900007, 900008, 900014, 900019, 900021, 900022, 900028, 900035, 900039, 900040]; reference-only DNF seeds [900006, 900013, 900015, 900016, 900026, 900029, 900030, 900031, 900036, 900037, 900038]

- `swarmos vs stop_and_wait`: treatment-only DNF seeds [900003, 900007, 900010, 900014, 900018, 900019, 900032, 900034, 900035, 900039]; reference-only DNF seeds [900004, 900005, 900013, 900016, 900023, 900026, 900030, 900031, 900038]

- `swarmos_mhb vs stop_and_wait`: treatment-only DNF seeds [900001, 900003, 900010, 900017, 900024, 900025, 900032, 900034]; reference-only DNF seeds [900004, 900012, 900013, 900015, 900016, 900020, 900026, 900036, 900038]
