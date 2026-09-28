# Experiment `long_run_safety`

- git: `a6e18041c8151077485fcdb63c6fc1769594cefa+uncommitted-changes`
- created: 20260926T220544Z
- seeds: [11, 13, 17, 19, 23, 29, 31, 37, 41]
- reference arm: `swarmos`
- command: `PYTHONPATH=. python3 tools/run_experiment.py --name long_run_safety --scenarios rush_50 narrow_aisle_deadlock blocked_aisle --arms swarmos swarmos_mhb_sep --ticks 9000 --workers 4`

Makespan for runs that did not finish is CENSORED at the scenario cap (understates the failing arm's true time; never inflates an improvement).

## blocked_aisle/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos | 0/9 | 8.78 | None | 0 | 21 | 0 | 428.3333 | 66.1111 | 62.8889 | 4024.2222 | 0.9569 | 0.722 |
| swarmos_mhb_sep | 0/9 | 10.56 | None | 0 | 31 | 0 | 494.6667 | 41.4444 | 67.4444 | 5449.6667 | 0.9654 | 0.727 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.4079, recall 0.8753, mean lead 16.3767 ticks (TP 1629, FP 2365, FN 232)
- `swarmos_mhb_sep`: precision 0.4431, recall 0.8704, mean lead 16.5333 ticks (TP 1626, FP 2044, FN 242)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| swarmos_mhb_sep vs swarmos | tasks_complete | 9 | 31.3 | [-14.71, 77.3] | 5/9 | not met |

## narrow_aisle_deadlock/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos | 0/9 | 5.56 | None | 0 | 5 | 0 | 193.3333 | 28.6667 | 22.6667 | 1497.3333 | 0.6594 | 0.73 |
| swarmos_mhb_sep | 0/9 | 6.22 | None | 0 | 4 | 0 | 237.7778 | 18.3333 | 23.6667 | 2048.8889 | 0.6657 | 0.74 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.4111, recall 0.9178, mean lead 16.67 ticks (TP 782, FP 1120, FN 70)
- `swarmos_mhb_sep`: precision 0.4647, recall 0.7977, mean lead 15.5167 ticks (TP 824, FP 949, FN 209)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| swarmos_mhb_sep vs swarmos | tasks_complete | 9 | 72.22 | [-40.84, 185.29] | 5/9 | not met |

## rush_50/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos | 0/9 | 24.22 | None | 0 | 88 | 0 | 6147.3333 | 1553.3333 | 2040.4444 | 102526.8889 | 0.954 | 0.724 |
| swarmos_mhb_sep | 0/9 | 38.33 | None | 0 | 259 | 0 | 6625.7778 | 727.3333 | 1667.4444 | 120632.1111 | 0.947 | 0.722 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.1899, recall 0.8739, mean lead 20.1956 ticks (TP 9022, FP 38481, FN 1302)
- `swarmos_mhb_sep`: precision 0.2815, recall 0.8481, mean lead 15.1789 ticks (TP 18499, FP 47211, FN 3314)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| swarmos_mhb_sep vs swarmos | tasks_complete | 9 | 96.9 | [-14.07, 207.87] | 6/9 | not met |
