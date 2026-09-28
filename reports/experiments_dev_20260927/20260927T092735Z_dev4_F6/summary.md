# Experiment `dev4_F6`

- git: `unknown`
- code identity (sha256): `3d7ee3b77ecdf6263c48c4df0422cdae2edc77f1c007d40aab3b56967715be02`
- created: 20260927T092735Z
- seeds: [700001, 700002, 700003, 700004, 700005, 700006, 700007, 700008, 700009, 700010, 700011, 700012, 700013, 700014, 700015, 700016, 700017, 700018, 700019, 700020]
- reference arm: `stop_and_wait+F1+F6`
- command: `PYTHONPATH=. python3 tools/run_experiment.py --name dev4_F6 --scenarios overlap_batch open_floor_batch --arms stop_and_wait+F1+F6 baseline+F1+F6 swarmos+F1+F3+F5+F6 swarmos+F1+F5+F6 --reference stop_and_wait+F1+F6 --seeds 700001 700002 700003 700004 700005 700006 700007 700008 700009 700010 700011 700012 700013 700014 700015 700016 700017 700018 700019 700020 --workers 3 --out /tmp/claude-0/-home-user-swarmos-member4-coordination/a091c13b-17d3-58fe-ae28-470e6e7f7619/scratchpad/work/reports/experiments`

Makespan for runs that did not finish is CENSORED at the scenario cap. That understates the failing arm's true time, so it flatters the arm that finishes less; a censored target is marked MET only when the treatment never failed a seed the reference finished.

## open_floor_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline+F1+F6 | 7/20 | 35.2 | 1528.945 | 0 | 0 | 0 | 609.4 | 6.45 | 55.35 | 2.5 | 7049.4 | 0.9468 | 0.752 |
| stop_and_wait+F1+F6 | 7/20 | 34.4 | 1411.64 | 0 | 0 | 0 | 409.4 | 358.15 | 5.65 | 2.35 | 2452.75 | 0.9937 | 0.752 |
| swarmos+F1+F3+F5+F6 | 0/20 | 36.0 | 648.815 | 0 | 0 | 0 | 119.1 | 32.4 | 5.85 | 0.5 | 2280.7 | 0.999 | 0.7505 |
| swarmos+F1+F5+F6 | 4/20 | 35.5 | 1122.88 | 0 | 0 | 0 | 754.85 | 68.2 | 23.35 | 0.95 | 7918.05 | 0.9793 | 0.75 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline+F1+F6 | 0.65 | 736.8385 / 570.7 | 627.995 | 2.663 | 24382.85 | 0.0 | 3436.3 | 1101.2 | 484.1 | 641.05 / 640.1 | 0.0 | None | 0 |
| stop_and_wait+F1+F6 | 0.65 | 556.3692 / 563.6 | 997.595 | 2.785 | 35371.3 | 0.0 | 1172.7 | 1345.4 | 131.8 | 969.9 / 968.65 | 0.0 | None | 0 |
| swarmos+F1+F3+F5+F6 | 1.0 | 648.815 / 627.05 | 498.59 | 3.389 | 1717.7 | 6761.6 | 1083.3 | 673.75 | 209.65 | 92.55 / 90.05 | 210.75 | 0.0 | 0 |
| swarmos+F1+F5+F6 | 0.8 | 653.6 / 636.05 | 633.895 | 2.826 | 7174.7 | 20281.75 | 3889.45 | 1198.75 | 498.7 | 399.1 / 396.3 | 684.95 | 0.0 | 0 |

| arm | floor entries (total) | floor pair-ticks (mean) | frozen pairs (total) | runs with a frozen pair | recovery actions (mean: stall releases + REROUTE) |
|---|---|---|---|---|---|
| baseline+F1+F6 | 0 | 0.0 | 0 | 0 | 3491.65 |
| stop_and_wait+F1+F6 | 0 | 0.0 | 0 | 0 | 1178.35 |
| swarmos+F1+F3+F5+F6 | 0 | 0.0 | 0 | 0 | 1089.15 |
| swarmos+F1+F5+F6 | 0 | 0.0 | 0 | 0 | 3912.8 |

Lookahead (observe-only scoring):

- `swarmos+F1+F3+F5+F6`: precision 0.4213, recall 0.9519, mean lead 16.4885 ticks (TP 1762, FP 2420, FN 89)
- `swarmos+F1+F5+F6`: precision 0.533, recall 0.8582, mean lead 14.9175 ticks (TP 6850, FP 6002, FN 1132)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| baseline+F1+F6 vs stop_and_wait+F1+F6 | makespan_censored_s | 20 | -76.94 | [-169.15, 15.27] | 9/20 | not met |
| baseline+F1+F6 vs stop_and_wait+F1+F6 | makespan_s (both finished) | 10 | -50.56 | [-171.11, 69.99] | 6/10 | not met |
| baseline+F1+F6 vs stop_and_wait+F1+F6 | t90_censored_s | 20 | 11.31 | [-5.88, 28.51] | 14/20 | not met |
| baseline+F1+F6 vs stop_and_wait+F1+F6 | tasks_complete | 20 | 3.23 | [-2.31, 8.78] | 5/20 | not met |
| swarmos+F1+F3+F5+F6 vs stop_and_wait+F1+F6 | makespan_censored_s | 20 | 13.84 | [-10.58, 38.25] | 9/20 | not met |
| swarmos+F1+F3+F5+F6 vs stop_and_wait+F1+F6 | makespan_s (both finished) | 13 | -21.54 | [-34.1, -8.99] | 2/13 | not met |
| swarmos+F1+F3+F5+F6 vs stop_and_wait+F1+F6 | t90_censored_s | 20 | 13.61 | [-5.83, 33.06] | 12/20 | not met |
| swarmos+F1+F3+F5+F6 vs stop_and_wait+F1+F6 | tasks_complete | 20 | 5.63 | [0.07, 11.19] | 7/20 | not met |
| swarmos+F1+F5+F6 vs stop_and_wait+F1+F6 | makespan_censored_s | 20 | -59.9 | [-149.57, 29.77] | 8/20 | not met |
| swarmos+F1+F5+F6 vs stop_and_wait+F1+F6 | makespan_s (both finished) | 10 | -21.65 | [-34.31, -8.98] | 2/10 | not met |
| swarmos+F1+F5+F6 vs stop_and_wait+F1+F6 | t90_censored_s | 20 | -13.13 | [-63.41, 37.15] | 9/20 | not met |
| swarmos+F1+F5+F6 vs stop_and_wait+F1+F6 | tasks_complete | 20 | 4.23 | [-1.75, 10.2] | 6/20 | not met |

- `baseline+F1+F6 vs stop_and_wait+F1+F6`: treatment-only DNF seeds [700004, 700011, 700020]; reference-only DNF seeds [700010, 700015, 700017]

- `swarmos+F1+F3+F5+F6 vs stop_and_wait+F1+F6`: treatment-only DNF seeds none; reference-only DNF seeds [700007, 700009, 700010, 700013, 700015, 700017, 700019]

- `swarmos+F1+F5+F6 vs stop_and_wait+F1+F6`: treatment-only DNF seeds [700012, 700014, 700018]; reference-only DNF seeds [700007, 700009, 700013, 700015, 700017, 700019]

## overlap_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline+F1+F6 | 6/20 | 21.65 | 1402.225 | 0 | 0 | 0 | 91.9 | 0.65 | 1.15 | 6.05 | 506.7 | 0.544 | 0.7531 |
| stop_and_wait+F1+F6 | 13/20 | 21.4 | 2250.095 | 0 | 0 | 0 | 141.55 | 137.55 | 2.45 | 4.9 | 1533.1 | 0.5473 | 0.752 |
| swarmos+F1+F3+F5+F6 | 0/20 | 24.0 | 485.16 | 0 | 0 | 0 | 29.8 | 4.25 | 1.5 | 1.35 | 684.15 | 0.8041 | 0.75 |
| swarmos+F1+F5+F6 | 0/20 | 24.0 | 599.095 | 0 | 0 | 0 | 57.05 | 2.95 | 1.0 | 3.1 | 857.05 | 0.6728 | 0.7514 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline+F1+F6 | 0.7 | 717.4643 / 511.25 | 1066.085 | 1.869 | 1756.6 | 0.0 | 220.85 | 345.8 | 101.95 | 256.8 / 256.7 | 0.0 | None | 0 |
| stop_and_wait+F1+F6 | 0.35 | 857.4143 / 564.5 | 1130.485 | 1.159 | 21767.8 | 0.0 | 733.6 | 576.7 | 306.65 | 488.2 / 487.25 | 0.0 | None | 0 |
| swarmos+F1+F3+F5+F6 | 1.0 | 485.16 / 468.05 | 420.36 | 3.015 | 268.85 | 2601.7 | 307.0 | 169.7 | 46.6 | 39.75 / 38.2 | 79.0 | 0.0 | 0 |
| swarmos+F1+F5+F6 | 1.0 | 599.095 / 604.35 | 512.475 | 2.4865 | 352.95 | 3435.0 | 393.75 | 180.5 | 57.4 | 52.05 / 50.45 | 77.6 | 0.0 | 0 |

| arm | floor entries (total) | floor pair-ticks (mean) | frozen pairs (total) | runs with a frozen pair | recovery actions (mean: stall releases + REROUTE) |
|---|---|---|---|---|---|
| baseline+F1+F6 | 0 | 0.0 | 0 | 0 | 222.0 |
| stop_and_wait+F1+F6 | 0 | 0.0 | 0 | 0 | 736.05 |
| swarmos+F1+F3+F5+F6 | 0 | 0.0 | 0 | 0 | 308.5 |
| swarmos+F1+F5+F6 | 0 | 0.0 | 0 | 0 | 394.75 |

Lookahead (observe-only scoring):

- `swarmos+F1+F3+F5+F6`: precision 0.4952, recall 0.9761, mean lead 16.199 ticks (TP 776, FP 791, FN 19)
- `swarmos+F1+F5+F6`: precision 0.6183, recall 0.9135, mean lead 16.506 ticks (TP 951, FP 587, FN 90)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| baseline+F1+F6 vs stop_and_wait+F1+F6 | makespan_censored_s | 20 | 1.5 | [-68.61, 71.61] | 12/20 | not met |
| baseline+F1+F6 vs stop_and_wait+F1+F6 | makespan_s (both finished) | 6 | 11.78 | [-32.8, 56.36] | 4/6 | not met |
| baseline+F1+F6 vs stop_and_wait+F1+F6 | t90_censored_s | 20 | -30.7 | [-105.28, 43.88] | 11/20 | not met |
| baseline+F1+F6 vs stop_and_wait+F1+F6 | tasks_complete | 20 | 21.36 | [-32.21, 74.92] | 9/20 | not met |
| swarmos+F1+F3+F5+F6 vs stop_and_wait+F1+F6 | makespan_censored_s | 20 | 60.56 | [43.38, 77.73] | 19/20 | MET |
| swarmos+F1+F3+F5+F6 vs stop_and_wait+F1+F6 | makespan_s (both finished) | 7 | 17.55 | [-10.82, 45.92] | 6/7 | not met |
| swarmos+F1+F3+F5+F6 vs stop_and_wait+F1+F6 | t90_censored_s | 20 | 33.56 | [17.31, 49.81] | 19/20 | not met |
| swarmos+F1+F3+F5+F6 vs stop_and_wait+F1+F6 | tasks_complete | 20 | 33.67 | [-18.23, 85.56] | 13/20 | not met |
| swarmos+F1+F5+F6 vs stop_and_wait+F1+F6 | makespan_censored_s | 20 | 52.07 | [31.01, 73.13] | 16/20 | MET |
| swarmos+F1+F5+F6 vs stop_and_wait+F1+F6 | makespan_s (both finished) | 7 | 0.97 | [-37.25, 39.19] | 3/7 | not met |
| swarmos+F1+F5+F6 vs stop_and_wait+F1+F6 | t90_censored_s | 20 | 20.24 | [0.0, 40.48] | 12/20 | not met |
| swarmos+F1+F5+F6 vs stop_and_wait+F1+F6 | tasks_complete | 20 | 33.67 | [-18.23, 85.56] | 13/20 | not met |

- `baseline+F1+F6 vs stop_and_wait+F1+F6`: treatment-only DNF seeds [700015]; reference-only DNF seeds [700001, 700002, 700009, 700011, 700013, 700014, 700018, 700019]

- `swarmos+F1+F3+F5+F6 vs stop_and_wait+F1+F6`: treatment-only DNF seeds none; reference-only DNF seeds [700001, 700002, 700004, 700005, 700006, 700009, 700010, 700011, 700013, 700014, 700018, 700019, 700020]

- `swarmos+F1+F5+F6 vs stop_and_wait+F1+F6`: treatment-only DNF seeds none; reference-only DNF seeds [700001, 700002, 700004, 700005, 700006, 700009, 700010, 700011, 700013, 700014, 700018, 700019, 700020]
