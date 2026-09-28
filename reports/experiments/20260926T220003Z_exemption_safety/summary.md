# Experiment `exemption_safety`

- git: `a6e18041c8151077485fcdb63c6fc1769594cefa+uncommitted-changes`
- created: 20260926T220003Z
- seeds: [11, 13, 17, 19, 23, 29, 31, 37, 41]
- reference arm: `swarmos_mhb_sep`
- command: `PYTHONPATH=. python3 tools/run_experiment.py --name exemption_safety --scenarios rush_50 narrow_aisle_deadlock blocked_aisle corridor_demo --arms swarmos_mhb_sep --ticks 3000 --workers 4`

Makespan for runs that did not finish is CENSORED at the scenario cap (understates the failing arm's true time; never inflates an improvement).

## blocked_aisle/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos_mhb_sep | 0/9 | 10.56 | None | 0 | 31 | 0 | 494.6667 | 41.4444 | 67.4444 | 5449.6667 | 0.9654 | 0.727 |

Lookahead (observe-only scoring):

- `swarmos_mhb_sep`: precision 0.4431, recall 0.8704, mean lead 16.5333 ticks (TP 1626, FP 2044, FN 242)

## corridor_demo/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos_mhb_sep | 0/9 | 12.0 | 157.9444 | 0 | 2 | 0 | 23.2222 | 3.3333 | 2.0 | 383.3333 | 0.8027 | 0.732 |

Lookahead (observe-only scoring):

- `swarmos_mhb_sep`: precision 0.612, recall 0.9387, mean lead 15.5911 ticks (TP 153, FP 97, FN 10)

## narrow_aisle_deadlock/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos_mhb_sep | 0/9 | 6.22 | None | 0 | 4 | 0 | 237.7778 | 18.3333 | 23.6667 | 2048.8889 | 0.6657 | 0.74 |

Lookahead (observe-only scoring):

- `swarmos_mhb_sep`: precision 0.4647, recall 0.7977, mean lead 15.5167 ticks (TP 824, FP 949, FN 209)

## rush_50/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos_mhb_sep | 0/9 | 23.67 | None | 0 | 102 | 0 | 1667.8889 | 181.8889 | 309.5556 | 23538.6667 | 0.9442 | 0.722 |

Lookahead (observe-only scoring):

- `swarmos_mhb_sep`: precision 0.3422, recall 0.8654, mean lead 15.5867 ticks (TP 4791, FP 9210, FN 745)
