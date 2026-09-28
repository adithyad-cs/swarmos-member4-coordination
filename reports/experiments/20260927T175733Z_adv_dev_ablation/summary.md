# Experiment `adv_dev_ablation`

- git: `a6e18041c8151077485fcdb63c6fc1769594cefa+uncommitted-changes`
- code identity (sha256): `20ae813c15a9a2d2eeb312f9229de8f04b40452493a1db4bd04d2e849799ad07`
- created: 20260927T175733Z
- seeds: [1000001, 1000002, 1000003, 1000004, 1000005, 1000006, 1000007, 1000008, 1000009, 1000010, 1000011, 1000012, 1000013, 1000014, 1000015, 1000016, 1000017, 1000018, 1000019, 1000020]
- reference arm: `swarmos`
- command: `PYTHONPATH=. python3 tools/run_experiment.py --name adv_dev_ablation --scenarios overlap_batch open_floor_batch --arms stop_and_wait+F1+F6 swarmos swarmos+EAI swarmos+EAI+PC swarmos+AU swarmos+EAI+PC+AU --reference swarmos --seeds 1000001 1000002 1000003 1000004 1000005 1000006 1000007 1000008 1000009 1000010 1000011 1000012 1000013 1000014 1000015 1000016 1000017 1000018 1000019 1000020 --workers 4 --target-pct 20`

Makespan for runs that did not finish is CENSORED at the scenario cap. That understates the failing arm's true time, so it flatters the arm that finishes less; a censored target is marked MET only when the treatment never failed a seed the reference finished.

## open_floor_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| stop_and_wait+F1+F6 | 10/20 | 34.3 | 1788.835 | 0 | 0 | 0 | 488.75 | 486.6 | 59.9 | 3.2 | 4261.15 | 0.9843 | 0.7522 |
| swarmos | 2/20 | 35.9 | 814.975 | 0 | 0 | 0 | 117.95 | 45.5 | 5.75 | 0.1 | 4613.3 | 1.004 | 0.7508 |
| swarmos+AU | 0/20 | 36.0 | 655.085 | 0 | 0 | 0 | 88.95 | 35.15 | 6.95 | 0.0 | 2423.55 | 1.0077 | 0.75 |
| swarmos+EAI | 2/20 | 35.9 | 814.975 | 0 | 0 | 0 | 117.95 | 45.5 | 5.75 | 0.1 | 4613.3 | 1.004 | 0.7508 |
| swarmos+EAI+PC | 1/20 | 35.8 | 729.555 | 0 | 0 | 0 | 186.1 | 54.65 | 34.25 | 0.1 | 5707.4 | 1.0008 | 0.7521 |
| swarmos+EAI+PC+AU | 1/20 | 35.9 | 753.865 | 0 | 0 | 0 | 178.75 | 57.35 | 14.3 | 0.05 | 4339.35 | 1.0112 | 0.752 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| stop_and_wait+F1+F6 | 0.5 | 577.67 / 561.5 | 1148.03 | 2.225 | 59615.45 | 0.0 | 2025.65 | 1266.25 | 407.35 | 824.95 / 823.2 | 0.0 | None | 0 |
| swarmos | 0.9 | 572.1944 / 570.0 | 473.58 | 3.5055 | 3314.0 | 12659.25 | 2250.75 | 929.25 | 203.95 | 125.3 / 122.05 | 222.05 | 0.0 | 0 |
| swarmos+AU | 1.0 | 655.085 / 646.5 | 555.575 | 3.351 | 1640.55 | 6572.85 | 1146.4 | 329.55 | 235.5 | 55.15 / 52.1 | 119.9 | 0.0 | 0 |
| swarmos+EAI | 0.9 | 572.1944 / 570.0 | 473.58 | 3.5055 | 3314.0 | 12659.25 | 2250.75 | 929.25 | 203.95 | 125.3 / 122.05 | 222.05 | 0.0 | 0 |
| swarmos+EAI+PC | 0.95 | 610.0579 / 590.7 | 595.81 | 3.4665 | 5455.0 | 10503.15 | 2777.7 | 476.0 | 252.95 | 102.15 / 99.0 | 295.3 | 0.0 | 0 |
| swarmos+EAI+PC+AU | 0.95 | 635.6474 / 613.6 | 564.62 | 3.2905 | 3600.15 | 9507.15 | 2097.6 | 470.95 | 281.1 | 165.0 / 161.5 | 339.05 | 0.0 | 0 |

| arm | floor entries (total) | floor pair-ticks (mean) | frozen pairs (total) | runs with a frozen pair | recovery actions (mean: stall releases + REROUTE) |
|---|---|---|---|---|---|
| stop_and_wait+F1+F6 | 0 | 0.0 | 0 | 0 | 2085.55 |
| swarmos | 0 | 0.0 | 0 | 0 | 2256.5 |
| swarmos+AU | 0 | 0.0 | 0 | 0 | 1153.35 |
| swarmos+EAI | 0 | 0.0 | 0 | 0 | 2256.5 |
| swarmos+EAI+PC | 0 | 0.0 | 0 | 0 | 2811.95 |
| swarmos+EAI+PC+AU | 0 | 0.0 | 0 | 0 | 2111.9 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.5589, recall 0.9844, mean lead 16.7625 ticks (TP 2467, FP 1947, FN 39)
- `swarmos+AU`: precision 0.451, recall 0.9728, mean lead 16.705 ticks (TP 1073, FP 1306, FN 30)
- `swarmos+EAI`: precision 0.5589, recall 0.9844, mean lead 16.7625 ticks (TP 2467, FP 1947, FN 39)
- `swarmos+EAI+PC`: precision 0.3379, recall 0.9692, mean lead 19.5985 ticks (TP 1980, FP 3880, FN 63)
- `swarmos+EAI+PC+AU`: precision 0.4453, recall 0.8558, mean lead 20.0915 ticks (TP 2824, FP 3518, FN 476)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| stop_and_wait+F1+F6 vs swarmos | makespan_censored_s | 20 | -200.75 | [-305.0, -96.49] | 5/20 | not met |
| stop_and_wait+F1+F6 vs swarmos | makespan_s (both finished) | 8 | -5.61 | [-15.75, 4.52] | 3/8 | not met |
| stop_and_wait+F1+F6 vs swarmos | t90_censored_s | 20 | -141.38 | [-248.98, -33.77] | 4/20 | not met |
| stop_and_wait+F1+F6 vs swarmos | tasks_complete | 20 | -4.44 | [-7.41, -1.47] | 2/20 | not met |
| swarmos+AU vs swarmos | makespan_censored_s | 20 | -7.11 | [-23.3, 9.07] | 5/20 | not met |
| swarmos+AU vs swarmos | makespan_s (both finished) | 18 | -16.86 | [-25.9, -7.81] | 3/18 | not met |
| swarmos+AU vs swarmos | t90_censored_s | 20 | -17.96 | [-25.82, -10.1] | 1/20 | not met |
| swarmos+AU vs swarmos | tasks_complete | 20 | 0.29 | [-0.13, 0.7] | 2/20 | not met |
| swarmos+EAI vs swarmos | makespan_censored_s | 20 | 0.0 | [0.0, 0.0] | 0/20 | not met |
| swarmos+EAI vs swarmos | makespan_s (both finished) | 18 | 0.0 | [0.0, 0.0] | 0/18 | not met |
| swarmos+EAI vs swarmos | t90_censored_s | 20 | 0.0 | [0.0, 0.0] | 0/20 | not met |
| swarmos+EAI vs swarmos | tasks_complete | 20 | 0.0 | [0.0, 0.0] | 0/20 | not met |
| swarmos+EAI+PC vs swarmos | makespan_censored_s | 20 | -20.76 | [-68.36, 26.84] | 8/20 | not met |
| swarmos+EAI+PC vs swarmos | makespan_s (both finished) | 17 | -8.71 | [-17.58, 0.16] | 6/17 | not met |
| swarmos+EAI+PC vs swarmos | t90_censored_s | 20 | -26.25 | [-82.61, 30.11] | 12/20 | not met |
| swarmos+EAI+PC vs swarmos | tasks_complete | 20 | -0.27 | [-1.53, 0.99] | 2/20 | not met |
| swarmos+EAI+PC+AU vs swarmos | makespan_censored_s | 20 | -6.56 | [-17.71, 4.59] | 6/20 | not met |
| swarmos+EAI+PC+AU vs swarmos | makespan_s (both finished) | 18 | -11.59 | [-18.45, -4.72] | 5/18 | not met |
| swarmos+EAI+PC+AU vs swarmos | t90_censored_s | 20 | -20.26 | [-39.93, -0.59] | 2/20 | not met |
| swarmos+EAI+PC+AU vs swarmos | tasks_complete | 20 | 0.0 | [-0.43, 0.43] | 1/20 | not met |

- `stop_and_wait+F1+F6 vs swarmos`: treatment-only DNF seeds [1000003, 1000008, 1000009, 1000010, 1000011, 1000013, 1000014, 1000015, 1000016, 1000019]; reference-only DNF seeds [1000006, 1000012]

- `swarmos+AU vs swarmos`: treatment-only DNF seeds none; reference-only DNF seeds [1000006, 1000012]

- `swarmos+EAI vs swarmos`: treatment-only DNF seeds none; reference-only DNF seeds none

- `swarmos+EAI+PC vs swarmos`: treatment-only DNF seeds [1000013]; reference-only DNF seeds [1000006, 1000012]

- `swarmos+EAI+PC+AU vs swarmos`: treatment-only DNF seeds none; reference-only DNF seeds [1000012]

## overlap_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| stop_and_wait+F1+F6 | 14/20 | 21.2 | 2277.705 | 0 | 0 | 0 | 110.25 | 106.4 | 0.4 | 4.1 | 518.05 | 0.5645 | 0.752 |
| swarmos | 0/20 | 24.0 | 491.605 | 0 | 0 | 0 | 28.15 | 2.15 | 1.15 | 1.25 | 625.35 | 0.8141 | 0.7517 |
| swarmos+AU | 0/20 | 24.0 | 531.95 | 0 | 0 | 0 | 30.65 | 9.8 | 1.35 | 0.15 | 1084.95 | 0.9064 | 0.7517 |
| swarmos+EAI | 0/20 | 24.0 | 491.605 | 0 | 0 | 0 | 28.15 | 2.15 | 1.15 | 1.25 | 625.35 | 0.8141 | 0.7517 |
| swarmos+EAI+PC | 0/20 | 24.0 | 471.805 | 0 | 0 | 0 | 35.25 | 13.5 | 0.9 | 0.75 | 729.15 | 0.8481 | 0.7539 |
| swarmos+EAI+PC+AU | 0/20 | 24.0 | 531.775 | 0 | 0 | 0 | 44.05 | 25.15 | 1.95 | 0.2 | 1305.65 | 0.9396 | 0.754 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| stop_and_wait+F1+F6 | 0.3 | 592.35 / 497.05 | 908.34 | 1.0805 | 6873.75 | 0.0 | 227.75 | 303.1 | 105.8 | 202.05 / 201.75 | 0.0 | None | 0 |
| swarmos | 1.0 | 491.605 / 484.0 | 412.275 | 3.0155 | 236.15 | 2442.55 | 278.2 | 168.7 | 45.2 | 36.55 / 35.3 | 73.55 | 0.0 | 0 |
| swarmos+AU | 1.0 | 531.95 / 516.7 | 465.005 | 2.742 | 405.55 | 3729.65 | 502.4 | 100.85 | 87.55 | 23.3 / 21.2 | 51.0 | 0.0 | 0 |
| swarmos+EAI | 1.0 | 491.605 / 484.0 | 412.275 | 3.0155 | 236.15 | 2442.55 | 278.2 | 168.7 | 45.2 | 36.55 / 35.3 | 73.55 | 0.0 | 0 |
| swarmos+EAI+PC | 1.0 | 471.805 / 468.95 | 401.37 | 3.124 | 353.25 | 2674.6 | 330.1 | 174.6 | 84.6 | 34.0 / 32.05 | 74.9 | 0.0 | 0 |
| swarmos+EAI+PC+AU | 1.0 | 531.775 / 487.35 | 460.415 | 2.783 | 775.85 | 3812.15 | 612.4 | 155.3 | 185.4 | 21.4 / 19.5 | 58.45 | 0.0 | 0 |

| arm | floor entries (total) | floor pair-ticks (mean) | frozen pairs (total) | runs with a frozen pair | recovery actions (mean: stall releases + REROUTE) |
|---|---|---|---|---|---|
| stop_and_wait+F1+F6 | 0 | 0.0 | 0 | 0 | 228.15 |
| swarmos | 0 | 0.0 | 0 | 0 | 279.35 |
| swarmos+AU | 0 | 0.0 | 0 | 0 | 503.75 |
| swarmos+EAI | 0 | 0.0 | 0 | 0 | 279.35 |
| swarmos+EAI+PC | 0 | 0.0 | 0 | 0 | 331.0 |
| swarmos+EAI+PC+AU | 0 | 0.0 | 0 | 0 | 614.35 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.4874, recall 0.9767, mean lead 15.515 ticks (TP 714, FP 751, FN 17)
- `swarmos+AU`: precision 0.4552, recall 0.9914, mean lead 16.753 ticks (TP 462, FP 553, FN 4)
- `swarmos+EAI`: precision 0.4874, recall 0.9767, mean lead 15.515 ticks (TP 714, FP 751, FN 17)
- `swarmos+EAI+PC`: precision 0.4476, recall 0.9735, mean lead 19.7395 ticks (TP 662, FP 817, FN 18)
- `swarmos+EAI+PC+AU`: precision 0.3624, recall 0.9813, mean lead 20.9585 ticks (TP 420, FP 739, FN 8)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| stop_and_wait+F1+F6 vs swarmos | makespan_censored_s | 20 | -383.08 | [-506.29, -259.88] | 3/20 | not met |
| stop_and_wait+F1+F6 vs swarmos | makespan_s (both finished) | 6 | -14.59 | [-52.73, 23.55] | 3/6 | not met |
| stop_and_wait+F1+F6 vs swarmos | t90_censored_s | 20 | -123.21 | [-234.19, -12.23] | 6/20 | not met |
| stop_and_wait+F1+F6 vs swarmos | tasks_complete | 20 | -11.67 | [-20.26, -3.07] | 0/20 | not met |
| swarmos+AU vs swarmos | makespan_censored_s | 20 | -10.59 | [-19.12, -2.07] | 7/20 | not met |
| swarmos+AU vs swarmos | makespan_s (both finished) | 20 | -10.59 | [-19.12, -2.07] | 7/20 | not met |
| swarmos+AU vs swarmos | t90_censored_s | 20 | -13.8 | [-19.84, -7.75] | 4/20 | not met |
| swarmos+AU vs swarmos | tasks_complete | 20 | 0.0 | [0.0, 0.0] | 0/20 | not met |
| swarmos+EAI vs swarmos | makespan_censored_s | 20 | 0.0 | [0.0, 0.0] | 0/20 | not met |
| swarmos+EAI vs swarmos | makespan_s (both finished) | 20 | 0.0 | [0.0, 0.0] | 0/20 | not met |
| swarmos+EAI vs swarmos | t90_censored_s | 20 | 0.0 | [0.0, 0.0] | 0/20 | not met |
| swarmos+EAI vs swarmos | tasks_complete | 20 | 0.0 | [0.0, 0.0] | 0/20 | not met |
| swarmos+EAI+PC vs swarmos | makespan_censored_s | 20 | 1.85 | [-7.49, 11.19] | 12/20 | not met |
| swarmos+EAI+PC vs swarmos | makespan_s (both finished) | 20 | 1.85 | [-7.49, 11.19] | 12/20 | not met |
| swarmos+EAI+PC vs swarmos | t90_censored_s | 20 | 1.59 | [-5.76, 8.94] | 10/20 | not met |
| swarmos+EAI+PC vs swarmos | tasks_complete | 20 | 0.0 | [0.0, 0.0] | 0/20 | not met |
| swarmos+EAI+PC+AU vs swarmos | makespan_censored_s | 20 | -10.69 | [-21.72, 0.35] | 7/20 | not met |
| swarmos+EAI+PC+AU vs swarmos | makespan_s (both finished) | 20 | -10.69 | [-21.72, 0.35] | 7/20 | not met |
| swarmos+EAI+PC+AU vs swarmos | t90_censored_s | 20 | -13.06 | [-21.46, -4.67] | 6/20 | not met |
| swarmos+EAI+PC+AU vs swarmos | tasks_complete | 20 | 0.0 | [0.0, 0.0] | 0/20 | not met |

- `stop_and_wait+F1+F6 vs swarmos`: treatment-only DNF seeds [1000001, 1000003, 1000004, 1000005, 1000006, 1000007, 1000010, 1000011, 1000012, 1000014, 1000016, 1000018, 1000019, 1000020]; reference-only DNF seeds none

- `swarmos+AU vs swarmos`: treatment-only DNF seeds none; reference-only DNF seeds none

- `swarmos+EAI vs swarmos`: treatment-only DNF seeds none; reference-only DNF seeds none

- `swarmos+EAI+PC vs swarmos`: treatment-only DNF seeds none; reference-only DNF seeds none

- `swarmos+EAI+PC+AU vs swarmos`: treatment-only DNF seeds none; reference-only DNF seeds none
