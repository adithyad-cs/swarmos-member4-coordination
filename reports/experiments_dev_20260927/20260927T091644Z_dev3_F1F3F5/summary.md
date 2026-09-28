# Experiment `dev3_F1F3F5`

- git: `unknown`
- code identity (sha256): `3d7ee3b77ecdf6263c48c4df0422cdae2edc77f1c007d40aab3b56967715be02`
- created: 20260927T091644Z
- seeds: [700001, 700002, 700003, 700004, 700005, 700006, 700007, 700008, 700009, 700010, 700011, 700012, 700013, 700014, 700015, 700016, 700017, 700018, 700019, 700020]
- reference arm: `swarmos+F1+F3+F5`
- command: `PYTHONPATH=. python3 tools/run_experiment.py --name dev3_F1F3F5 --scenarios overlap_batch open_floor_batch --arms swarmos+F1+F3+F5 swarmos+F1+F5 --seeds 700001 700002 700003 700004 700005 700006 700007 700008 700009 700010 700011 700012 700013 700014 700015 700016 700017 700018 700019 700020 --workers 3 --out /tmp/claude-0/-home-user-swarmos-member4-coordination/a091c13b-17d3-58fe-ae28-470e6e7f7619/scratchpad/work/reports/experiments`

Makespan for runs that did not finish is CENSORED at the scenario cap. That understates the failing arm's true time, so it flatters the arm that finishes less; a censored target is marked MET only when the treatment never failed a seed the reference finished.

## open_floor_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos+F1+F3+F5 | 6/20 | 35.15 | 1321.335 | 0 | 0 | 0 | 180.0 | 17.25 | 120.6 | 0.85 | 11305.0 | 0.9986 | 0.7505 |
| swarmos+F1+F5 | 2/20 | 35.75 | 894.61 | 0 | 0 | 0 | 455.5 | 76.8 | 32.1 | 0.95 | 6770.25 | 0.9806 | 0.75 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos+F1+F3+F5 | 0.7 | 601.9071 / 595.95 | 613.33 | 2.7345 | 8967.35 | 27170.3 | 5544.5 | 1049.95 | 611.6 | 180.75 / 177.95 | 275.9 | 0.0 | 0 |
| swarmos+F1+F5 | 0.9 | 660.6778 / 636.85 | 555.185 | 3.0935 | 6315.65 | 15753.55 | 3317.8 | 729.65 | 348.85 | 326.1 / 322.9 | 638.8 | 0.0 | 0 |

| arm | floor entries (total) | floor pair-ticks (mean) | frozen pairs (total) | runs with a frozen pair | recovery actions (mean: stall releases + REROUTE) |
|---|---|---|---|---|---|
| swarmos+F1+F3+F5 | 0 | 0.0 | 0 | 0 | 5665.1 |
| swarmos+F1+F5 | 0 | 0.0 | 0 | 0 | 3349.9 |

Lookahead (observe-only scoring):

- `swarmos+F1+F3+F5`: precision 0.4544, recall 0.6913, mean lead 16.3565 ticks (TP 2499, FP 3000, FN 1116)
- `swarmos+F1+F5`: precision 0.4929, recall 0.9572, mean lead 15.818 ticks (TP 6243, FP 6423, FN 279)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| swarmos+F1+F5 vs swarmos+F1+F3+F5 | makespan_censored_s | 20 | -22.88 | [-90.48, 44.72] | 12/20 | not met |
| swarmos+F1+F5 vs swarmos+F1+F3+F5 | makespan_s (both finished) | 12 | -5.77 | [-22.03, 10.5] | 6/12 | not met |
| swarmos+F1+F5 vs swarmos+F1+F3+F5 | t90_censored_s | 20 | -10.16 | [-25.8, 5.49] | 6/20 | not met |
| swarmos+F1+F5 vs swarmos+F1+F3+F5 | tasks_complete | 20 | 1.9 | [-0.63, 4.44] | 6/20 | not met |

- `swarmos+F1+F5 vs swarmos+F1+F3+F5`: treatment-only DNF seeds [700004, 700018]; reference-only DNF seeds [700001, 700005, 700011, 700012, 700015, 700016]

## overlap_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos+F1+F3+F5 | 0/20 | 24.0 | 485.655 | 0 | 0 | 0 | 32.4 | 5.45 | 1.5 | 1.4 | 695.0 | 0.7978 | 0.75 |
| swarmos+F1+F5 | 1/20 | 23.95 | 720.71 | 0 | 0 | 0 | 133.05 | 62.15 | 0.95 | 3.25 | 1924.25 | 0.6622 | 0.7514 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos+F1+F3+F5 | 1.0 | 485.655 / 469.9 | 419.49 | 3.0105 | 308.25 | 2534.85 | 312.45 | 169.9 | 55.85 | 40.2 / 38.6 | 79.05 | 0.0 | 0 |
| swarmos+F1+F5 | 0.95 | 600.7474 / 606.3 | 521.06 | 2.384 | 1226.4 | 5755.35 | 927.55 | 216.65 | 348.3 | 57.05 / 55.1 | 102.6 | 0.0 | 0 |

| arm | floor entries (total) | floor pair-ticks (mean) | frozen pairs (total) | runs with a frozen pair | recovery actions (mean: stall releases + REROUTE) |
|---|---|---|---|---|---|
| swarmos+F1+F3+F5 | 0 | 0.0 | 0 | 0 | 313.95 |
| swarmos+F1+F5 | 0 | 0.0 | 0 | 0 | 928.5 |

Lookahead (observe-only scoring):

- `swarmos+F1+F3+F5`: precision 0.4987, recall 0.9726, mean lead 16.1595 ticks (TP 782, FP 786, FN 22)
- `swarmos+F1+F5`: precision 0.5172, recall 0.9238, mean lead 16.619 ticks (TP 1054, FP 984, FN 87)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| swarmos+F1+F5 vs swarmos+F1+F3+F5 | makespan_censored_s | 20 | -47.74 | [-96.65, 1.17] | 2/20 | not met |
| swarmos+F1+F5 vs swarmos+F1+F3+F5 | makespan_s (both finished) | 19 | -24.9 | [-35.82, -13.97] | 2/19 | not met |
| swarmos+F1+F5 vs swarmos+F1+F3+F5 | t90_censored_s | 20 | -24.8 | [-34.87, -14.72] | 2/20 | not met |
| swarmos+F1+F5 vs swarmos+F1+F3+F5 | tasks_complete | 20 | -0.21 | [-0.64, 0.23] | 0/20 | not met |

- `swarmos+F1+F5 vs swarmos+F1+F3+F5`: treatment-only DNF seeds [700017]; reference-only DNF seeds none
