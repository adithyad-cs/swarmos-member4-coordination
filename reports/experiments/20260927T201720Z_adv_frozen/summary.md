# Experiment `adv_frozen`

- git: `a6e18041c8151077485fcdb63c6fc1769594cefa+uncommitted-changes`
- code identity (sha256): `ae7c9aee82176521325c59ab9f90358d69d6648c39aca51810bcc72d96a86ac5`
- created: 20260927T201720Z
- seeds: [1400001, 1400002, 1400003, 1400004, 1400005, 1400006, 1400007, 1400008, 1400009, 1400010, 1400011, 1400012, 1400013, 1400014, 1400015, 1400016, 1400017, 1400018, 1400019, 1400020, 1400021, 1400022, 1400023, 1400024, 1400025, 1400026, 1400027, 1400028, 1400029, 1400030, 1400031, 1400032, 1400033, 1400034, 1400035, 1400036, 1400037, 1400038, 1400039, 1400040]
- reference arm: `swarmos`
- command: `PYTHONPATH=. python3 tools/run_experiment.py --name adv_frozen --scenarios overlap_batch open_floor_batch --arms stop_and_wait+F1+F6 swarmos swarmos+EAI swarmos+EAI+PC swarmos+AU swarmos+EAI+PC+AU --reference swarmos --seeds 1400001 1400002 1400003 1400004 1400005 1400006 1400007 1400008 1400009 1400010 1400011 1400012 1400013 1400014 1400015 1400016 1400017 1400018 1400019 1400020 1400021 1400022 1400023 1400024 1400025 1400026 1400027 1400028 1400029 1400030 1400031 1400032 1400033 1400034 1400035 1400036 1400037 1400038 1400039 1400040 --workers 4 --target-pct 20 --expect-identity ae7c9aee82176521325c59ab9f90358d69d6648c39aca51810bcc72d96a86ac5`

Makespan for runs that did not finish is CENSORED at the scenario cap. That understates the failing arm's true time, so it flatters the arm that finishes less; a censored target is marked MET only when the treatment never failed a seed the reference finished.

## open_floor_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| stop_and_wait+F1+F6 | 26/40 | 33.7 | 2154.9875 | 0 | 0 | 0 | 527.875 | 501.775 | 35.75 | 3.15 | 3880.425 | 0.988 | 0.752 |
| swarmos | 4/40 | 35.67 | 831.6675 | 0 | 0 | 0 | 198.4 | 56.6 | 48.675 | 0.25 | 7931.4 | 1.002 | 0.75 |
| swarmos+AU | 2/40 | 35.9 | 773.765 | 0 | 0 | 0 | 250.35 | 51.425 | 7.8 | 0.325 | 3848.95 | 0.9941 | 0.7515 |
| swarmos+EAI | 4/40 | 35.67 | 831.6675 | 0 | 0 | 0 | 198.4 | 56.6 | 48.675 | 0.25 | 7931.4 | 1.002 | 0.75 |
| swarmos+EAI+PC | 0/40 | 36.0 | 588.205 | 0 | 0 | 0 | 114.625 | 30.65 | 8.05 | 0.05 | 2127.975 | 1.0012 | 0.752 |
| swarmos+EAI+PC+AU | 0/40 | 36.0 | 614.89 | 0 | 0 | 0 | 96.675 | 29.65 | 2.75 | 0.1 | 1862.9 | 1.0026 | 0.75 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| stop_and_wait+F1+F6 | 0.35 | 585.6786 / 587.9 | 980.215 | 1.7305 | 55121.225 | 0.0 | 1861.525 | 1609.0 | 340.625 | 1120.35 / 1118.75 | 0.0 | None | 0 |
| swarmos | 0.9 | 590.7417 / 580.75 | 569.67 | 3.4052 | 7973.6 | 14312.95 | 3881.75 | 1102.2 | 462.425 | 110.75 / 107.5 | 340.1 | 0.0 | 0 |
| swarmos+AU | 0.95 | 656.5947 / 582.15 | 549.1775 | 3.3578 | 3062.15 | 11866.85 | 1857.75 | 1614.475 | 452.975 | 154.65 / 151.775 | 354.15 | 0.0 | 0 |
| swarmos+EAI | 0.9 | 590.7417 / 580.75 | 569.67 | 3.4052 | 7973.6 | 14312.95 | 3881.75 | 1102.2 | 462.425 | 110.75 / 107.5 | 340.1 | 0.0 | 0 |
| swarmos+EAI+PC | 1.0 | 588.205 / 571.55 | 495.485 | 3.7753 | 1772.85 | 5832.4 | 1006.6 | 495.025 | 196.8 | 69.6 / 66.875 | 166.8 | 0.0 | 0 |
| swarmos+EAI+PC+AU | 1.0 | 614.89 / 612.75 | 491.86 | 3.5595 | 1175.6 | 6125.875 | 869.55 | 459.95 | 231.7 | 64.7 / 61.95 | 183.325 | 0.0 | 0 |

| arm | floor entries (total) | floor pair-ticks (mean) | frozen pairs (total) | runs with a frozen pair | recovery actions (mean: stall releases + REROUTE) |
|---|---|---|---|---|---|
| stop_and_wait+F1+F6 | 0 | 0.0 | 0 | 0 | 1897.275 |
| swarmos | 0 | 0.0 | 0 | 0 | 3930.425 |
| swarmos+AU | 0 | 0.0 | 0 | 0 | 1865.55 |
| swarmos+EAI | 0 | 0.0 | 0 | 0 | 3930.425 |
| swarmos+EAI+PC | 0 | 0.0 | 0 | 0 | 1014.65 |
| swarmos+EAI+PC+AU | 0 | 0.0 | 0 | 0 | 872.3 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.319, recall 0.9747, mean lead 16.0622 ticks (TP 4318, FP 9217, FN 112)
- `swarmos+AU`: precision 0.4223, recall 0.9526, mean lead 16.325 ticks (TP 5893, FP 8062, FN 293)
- `swarmos+EAI`: precision 0.319, recall 0.9747, mean lead 16.0622 ticks (TP 4318, FP 9217, FN 112)
- `swarmos+EAI+PC`: precision 0.4077, recall 0.9677, mean lead 19.8012 ticks (TP 2694, FP 3914, FN 90)
- `swarmos+EAI+PC+AU`: precision 0.3409, recall 0.9571, mean lead 20.8237 ticks (TP 2477, FP 4790, FN 111)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| stop_and_wait+F1+F6 vs swarmos | makespan_censored_s | 40 | -230.68 | [-297.67, -163.69] | 5/40 | not met |
| stop_and_wait+F1+F6 vs swarmos | makespan_s (both finished) | 13 | -4.86 | [-14.15, 4.44] | 4/13 | not met |
| stop_and_wait+F1+F6 vs swarmos | t90_censored_s | 40 | -90.8 | [-151.79, -29.81] | 11/40 | not met |
| stop_and_wait+F1+F6 vs swarmos | tasks_complete | 40 | -5.55 | [-8.75, -2.35] | 2/40 | not met |
| swarmos+AU vs swarmos | makespan_censored_s | 40 | -19.73 | [-51.42, 11.97] | 21/40 | not met |
| swarmos+AU vs swarmos | makespan_s (both finished) | 34 | -6.45 | [-13.89, 0.99] | 17/34 | not met |
| swarmos+AU vs swarmos | t90_censored_s | 40 | -4.36 | [-14.13, 5.41] | 21/40 | not met |
| swarmos+AU vs swarmos | tasks_complete | 40 | 0.77 | [-0.64, 2.18] | 4/40 | not met |
| swarmos+EAI vs swarmos | makespan_censored_s | 40 | 0.0 | [0.0, 0.0] | 0/40 | not met |
| swarmos+EAI vs swarmos | makespan_s (both finished) | 36 | 0.0 | [0.0, 0.0] | 0/36 | not met |
| swarmos+EAI vs swarmos | t90_censored_s | 40 | 0.0 | [0.0, 0.0] | 0/40 | not met |
| swarmos+EAI vs swarmos | tasks_complete | 40 | 0.0 | [0.0, 0.0] | 0/40 | not met |
| swarmos+EAI+PC vs swarmos | makespan_censored_s | 40 | 6.83 | [-3.88, 17.54] | 23/40 | not met |
| swarmos+EAI+PC vs swarmos | makespan_s (both finished) | 36 | -1.5 | [-9.2, 6.21] | 19/36 | not met |
| swarmos+EAI+PC vs swarmos | t90_censored_s | 40 | 2.54 | [-6.1, 11.18] | 22/40 | not met |
| swarmos+EAI+PC vs swarmos | tasks_complete | 40 | 1.05 | [-0.28, 2.38] | 4/40 | not met |
| swarmos+EAI+PC+AU vs swarmos | makespan_censored_s | 40 | 3.43 | [-5.96, 12.83] | 20/40 | not met |
| swarmos+EAI+PC+AU vs swarmos | makespan_s (both finished) | 36 | -4.98 | [-9.97, 0.0] | 16/36 | not met |
| swarmos+EAI+PC+AU vs swarmos | t90_censored_s | 40 | 3.45 | [-2.5, 9.4] | 24/40 | not met |
| swarmos+EAI+PC+AU vs swarmos | tasks_complete | 40 | 1.05 | [-0.28, 2.38] | 4/40 | not met |

- `stop_and_wait+F1+F6 vs swarmos`: treatment-only DNF seeds [1400003, 1400004, 1400006, 1400009, 1400012, 1400013, 1400015, 1400018, 1400019, 1400021, 1400022, 1400023, 1400024, 1400025, 1400026, 1400027, 1400031, 1400032, 1400033, 1400034, 1400035, 1400038, 1400040]; reference-only DNF seeds [1400014]

- `swarmos+AU vs swarmos`: treatment-only DNF seeds [1400009, 1400020]; reference-only DNF seeds [1400005, 1400008, 1400014, 1400017]

- `swarmos+EAI vs swarmos`: treatment-only DNF seeds none; reference-only DNF seeds none

- `swarmos+EAI+PC vs swarmos`: treatment-only DNF seeds none; reference-only DNF seeds [1400005, 1400008, 1400014, 1400017]

- `swarmos+EAI+PC+AU vs swarmos`: treatment-only DNF seeds none; reference-only DNF seeds [1400005, 1400008, 1400014, 1400017]

## overlap_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| stop_and_wait+F1+F6 | 16/40 | 22.77 | 1853.585 | 0 | 0 | 0 | 88.375 | 83.7 | 1.325 | 5.15 | 445.1 | 0.5401 | 0.752 |
| swarmos | 0/40 | 24.0 | 487.4125 | 0 | 0 | 0 | 29.625 | 3.075 | 1.375 | 1.175 | 740.9 | 0.8249 | 0.7505 |
| swarmos+AU | 0/40 | 24.0 | 479.7075 | 0 | 0 | 0 | 26.125 | 3.1 | 0.875 | 1.025 | 608.6 | 0.8328 | 0.754 |
| swarmos+EAI | 0/40 | 24.0 | 487.4125 | 0 | 0 | 0 | 29.625 | 3.075 | 1.375 | 1.175 | 740.9 | 0.8249 | 0.7505 |
| swarmos+EAI+PC | 0/40 | 24.0 | 477.65 | 0 | 0 | 0 | 32.725 | 4.25 | 0.95 | 0.85 | 677.2 | 0.8413 | 0.7535 |
| swarmos+EAI+PC+AU | 0/40 | 24.0 | 496.9425 | 0 | 0 | 0 | 41.725 | 11.1 | 1.0 | 1.35 | 807.95 | 0.849 | 0.752 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| stop_and_wait+F1+F6 | 0.6 | 1089.3083 / 590.35 | 879.0925 | 1.476 | 5809.275 | 0.0 | 188.925 | 294.525 | 90.725 | 213.35 / 213.125 | 0.0 | None | 0 |
| swarmos | 1.0 | 487.4125 / 486.1 | 412.215 | 3.0152 | 278.775 | 2862.925 | 335.725 | 190.75 | 41.025 | 41.125 / 39.675 | 81.025 | 0.0 | 0 |
| swarmos+AU | 1.0 | 479.7075 / 476.35 | 402.56 | 3.0568 | 233.375 | 2288.075 | 264.25 | 156.75 | 46.975 | 34.825 / 33.4 | 68.4 | 0.0 | 0 |
| swarmos+EAI | 1.0 | 487.4125 / 486.1 | 412.215 | 3.0152 | 278.775 | 2862.925 | 335.725 | 190.75 | 41.025 | 41.125 / 39.675 | 81.025 | 0.0 | 0 |
| swarmos+EAI+PC | 1.0 | 477.65 / 472.25 | 396.78 | 3.0995 | 267.075 | 2802.0 | 304.075 | 195.4 | 52.0 | 35.375 / 33.775 | 82.15 | 0.0 | 0 |
| swarmos+EAI+PC+AU | 1.0 | 496.9425 / 492.25 | 410.365 | 2.9458 | 425.525 | 2819.45 | 363.9 | 184.1 | 90.425 | 33.775 / 32.15 | 76.475 | 0.0 | 0 |

| arm | floor entries (total) | floor pair-ticks (mean) | frozen pairs (total) | runs with a frozen pair | recovery actions (mean: stall releases + REROUTE) |
|---|---|---|---|---|---|
| stop_and_wait+F1+F6 | 0 | 0.0 | 0 | 0 | 190.25 |
| swarmos | 0 | 0.0 | 0 | 0 | 337.1 |
| swarmos+AU | 0 | 0.0 | 0 | 0 | 265.125 |
| swarmos+EAI | 0 | 0.0 | 0 | 0 | 337.1 |
| swarmos+EAI+PC | 0 | 0.0 | 0 | 0 | 305.025 |
| swarmos+EAI+PC+AU | 0 | 0.0 | 0 | 0 | 364.9 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.4963, recall 0.9708, mean lead 15.5352 ticks (TP 1597, FP 1621, FN 48)
- `swarmos+AU`: precision 0.4987, recall 0.9742, mean lead 16.3973 ticks (TP 1357, FP 1364, FN 36)
- `swarmos+EAI`: precision 0.4963, recall 0.9708, mean lead 15.5352 ticks (TP 1597, FP 1621, FN 48)
- `swarmos+EAI+PC`: precision 0.4224, recall 0.9731, mean lead 19.3133 ticks (TP 1377, FP 1883, FN 38)
- `swarmos+EAI+PC+AU`: precision 0.4331, recall 0.9726, mean lead 19.6888 ticks (TP 1314, FP 1720, FN 37)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| stop_and_wait+F1+F6 vs swarmos | makespan_censored_s | 40 | -276.79 | [-354.47, -199.11] | 4/40 | not met |
| stop_and_wait+F1+F6 vs swarmos | makespan_s (both finished) | 24 | -114.18 | [-182.49, -45.86] | 4/24 | not met |
| stop_and_wait+F1+F6 vs swarmos | t90_censored_s | 40 | -118.54 | [-190.02, -47.06] | 8/40 | not met |
| stop_and_wait+F1+F6 vs swarmos | tasks_complete | 40 | -5.1 | [-8.38, -1.83] | 0/40 | not met |
| swarmos+AU vs swarmos | makespan_censored_s | 40 | 0.03 | [-5.69, 5.75] | 23/40 | not met |
| swarmos+AU vs swarmos | makespan_s (both finished) | 40 | 0.03 | [-5.69, 5.75] | 23/40 | not met |
| swarmos+AU vs swarmos | t90_censored_s | 40 | 0.49 | [-5.03, 6.01] | 23/40 | not met |
| swarmos+AU vs swarmos | tasks_complete | 40 | 0.0 | [0.0, 0.0] | 0/40 | not met |
| swarmos+EAI vs swarmos | makespan_censored_s | 40 | 0.0 | [0.0, 0.0] | 0/40 | not met |
| swarmos+EAI vs swarmos | makespan_s (both finished) | 40 | 0.0 | [0.0, 0.0] | 0/40 | not met |
| swarmos+EAI vs swarmos | t90_censored_s | 40 | 0.0 | [0.0, 0.0] | 0/40 | not met |
| swarmos+EAI vs swarmos | tasks_complete | 40 | 0.0 | [0.0, 0.0] | 0/40 | not met |
| swarmos+EAI+PC vs swarmos | makespan_censored_s | 40 | 0.21 | [-6.88, 7.3] | 24/40 | not met |
| swarmos+EAI+PC vs swarmos | makespan_s (both finished) | 40 | 0.21 | [-6.88, 7.3] | 24/40 | not met |
| swarmos+EAI+PC vs swarmos | t90_censored_s | 40 | 2.57 | [-2.01, 7.15] | 23/40 | not met |
| swarmos+EAI+PC vs swarmos | tasks_complete | 40 | 0.0 | [0.0, 0.0] | 0/40 | not met |
| swarmos+EAI+PC+AU vs swarmos | makespan_censored_s | 40 | -3.43 | [-8.79, 1.93] | 18/40 | not met |
| swarmos+EAI+PC+AU vs swarmos | makespan_s (both finished) | 40 | -3.43 | [-8.79, 1.93] | 18/40 | not met |
| swarmos+EAI+PC+AU vs swarmos | t90_censored_s | 40 | -1.19 | [-7.17, 4.79] | 23/40 | not met |
| swarmos+EAI+PC+AU vs swarmos | tasks_complete | 40 | 0.0 | [0.0, 0.0] | 0/40 | not met |

- `stop_and_wait+F1+F6 vs swarmos`: treatment-only DNF seeds [1400002, 1400006, 1400012, 1400013, 1400014, 1400015, 1400016, 1400017, 1400021, 1400022, 1400025, 1400028, 1400029, 1400030, 1400033, 1400036]; reference-only DNF seeds none

- `swarmos+AU vs swarmos`: treatment-only DNF seeds none; reference-only DNF seeds none

- `swarmos+EAI vs swarmos`: treatment-only DNF seeds none; reference-only DNF seeds none

- `swarmos+EAI+PC vs swarmos`: treatment-only DNF seeds none; reference-only DNF seeds none

- `swarmos+EAI+PC+AU vs swarmos`: treatment-only DNF seeds none; reference-only DNF seeds none
