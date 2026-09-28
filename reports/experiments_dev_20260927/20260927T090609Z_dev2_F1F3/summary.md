# Experiment `dev2_F1F3`

- git: `unknown`
- code identity (sha256): `3d7ee3b77ecdf6263c48c4df0422cdae2edc77f1c007d40aab3b56967715be02`
- created: 20260927T090609Z
- seeds: [700001, 700002, 700003, 700004, 700005, 700006, 700007, 700008, 700009, 700010, 700011, 700012, 700013, 700014, 700015, 700016, 700017, 700018, 700019, 700020]
- reference arm: `swarmos+F1+F3`
- command: `PYTHONPATH=. python3 tools/run_experiment.py --name dev2_F1F3 --scenarios overlap_batch open_floor_batch --arms swarmos+F1+F3 --seeds 700001 700002 700003 700004 700005 700006 700007 700008 700009 700010 700011 700012 700013 700014 700015 700016 700017 700018 700019 700020 --workers 3 --out /tmp/claude-0/-home-user-swarmos-member4-coordination/a091c13b-17d3-58fe-ae28-470e6e7f7619/scratchpad/work/reports/experiments`

Makespan for runs that did not finish is CENSORED at the scenario cap. That understates the failing arm's true time, so it flatters the arm that finishes less; a censored target is marked MET only when the treatment never failed a seed the reference finished.

## open_floor_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos+F1+F3 | 8/20 | 34.45 | 1583.035 | 0 | 0 | 0 | 710.05 | 337.55 | 249.8 | 2.1 | 21199.85 | 1.0094 | 0.7505 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos+F1+F3 | 0.6 | 638.3917 / 626.95 | 1160.085 | 2.3555 | 24658.9 | 34295.3 | 10432.9 | 936.0 | 1163.65 | 152.95 / 149.15 | 423.65 | 0.0 | 0 |

| arm | floor entries (total) | floor pair-ticks (mean) | frozen pairs (total) | runs with a frozen pair | recovery actions (mean: stall releases + REROUTE) |
|---|---|---|---|---|---|
| swarmos+F1+F3 | 0 | 0.0 | 0 | 0 | 10682.7 |

Lookahead (observe-only scoring):

- `swarmos+F1+F3`: precision 0.3428, recall 0.9441, mean lead 17.099 ticks (TP 2888, FP 5537, FN 171)

## overlap_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos+F1+F3 | 5/20 | 23.55 | 1111.195 | 0 | 0 | 0 | 117.75 | 62.1 | 75.8 | 1.85 | 10196.85 | 0.8074 | 0.7527 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos+F1+F3 | 0.75 | 481.5933 / 474.5 | 684.375 | 2.375 | 11633.6 | 19194.15 | 5030.8 | 656.25 | 1586.3 | 69.3 / 66.75 | 139.5 | 0.0 | 0 |

| arm | floor entries (total) | floor pair-ticks (mean) | frozen pairs (total) | runs with a frozen pair | recovery actions (mean: stall releases + REROUTE) |
|---|---|---|---|---|---|
| swarmos+F1+F3 | 0 | 0.0 | 0 | 0 | 5106.6 |

Lookahead (observe-only scoring):

- `swarmos+F1+F3`: precision 0.4511, recall 0.8391, mean lead 16.074 ticks (TP 1163, FP 1415, FN 223)
