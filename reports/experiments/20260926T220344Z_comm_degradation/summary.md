# Experiment `comm_degradation`

- git: `a6e18041c8151077485fcdb63c6fc1769594cefa+uncommitted-changes`
- created: 20260926T220344Z
- seeds: [11, 13, 17, 19, 23]
- reference arm: `swarmos`
- command: `PYTHONPATH=. python3 tools/run_experiment.py --name comm_degradation --comm-sweep --scenarios rush_50 --fleet 16 --ticks 1200 --arms swarmos swarmos_nofb swarmos_mhb_sep --seeds 11 13 17 19 23 --workers 4`

Makespan for runs that did not finish is CENSORED at the scenario cap (understates the failing arm's true time; never inflates an improvement).

## rush_50/blackout_one

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos | 0/5 | 5.0 | None | 0 | 5 | 0 | 106.4 | 16.8 | 15.6 | 957.4 | 0.9887 | 0.72 |
| swarmos_mhb_sep | 0/5 | 5.6 | None | 0 | 5 | 0 | 96.6 | 12.0 | 13.8 | 1127.2 | 1.0103 | 0.722 |
| swarmos_nofb | 0/5 | 6.0 | None | 4 | 8 | 3 | 108.6 | 14.0 | 15.8 | 962.2 | 0.9749 | 0.045 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.6152, recall 0.875, mean lead 17.716 ticks (TP 203, FP 127, FN 29)
- `swarmos_mhb_sep`: precision 0.6286, recall 0.8871, mean lead 16.912 ticks (TP 220, FP 130, FN 28)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| swarmos_mhb_sep vs swarmos | tasks_complete | 5 | 18.33 | [-29.3, 65.97] | 2/5 | not met |
| swarmos_nofb vs swarmos | tasks_complete | 5 | 22.38 | [-4.84, 49.6] | 3/5 | not met |

## rush_50/latency100ms

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos | 0/5 | 5.8 | None | 0 | 0 | 0 | 80.8 | 15.8 | 15.2 | 1088.6 | 1.0022 | 0.7607 |
| swarmos_mhb_sep | 0/5 | 5.8 | None | 0 | 0 | 0 | 86.2 | 14.4 | 19.4 | 1642.4 | 1.0022 | 0.7614 |
| swarmos_nofb | 0/5 | 6.2 | None | 0 | 2 | 0 | 134.4 | 12.0 | 9.8 | 732.6 | 0.9817 | 0.7402 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.0327, recall 1.0, mean lead 17.734 ticks (TP 17, FP 503, FN 0)
- `swarmos_mhb_sep`: precision 0.0366, recall 0.9444, mean lead 16.968 ticks (TP 17, FP 447, FN 1)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| swarmos_mhb_sep vs swarmos | tasks_complete | 5 | 0.67 | [-41.27, 42.6] | 3/5 | not met |
| swarmos_nofb vs swarmos | tasks_complete | 5 | 9.33 | [-55.66, 74.33] | 3/5 | not met |

## rush_50/latency500ms

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos | 0/5 | 3.8 | None | 0 | 0 | 0 | 63.2 | 16.6 | 29.2 | 1730.2 | 1.0194 | 0.7607 |
| swarmos_mhb_sep | 0/5 | 4.0 | None | 0 | 0 | 0 | 82.8 | 26.8 | 28.4 | 2245.6 | 1.0036 | 0.7614 |
| swarmos_nofb | 0/5 | 6.4 | None | 3 | 10 | 3 | 98.8 | 23.2 | 13.4 | 973.2 | 1.0041 | 0.53 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.0619, recall 0.9615, mean lead 14.058 ticks (TP 25, FP 379, FN 1)
- `swarmos_mhb_sep`: precision 0.051, recall 1.0, mean lead 13.83 ticks (TP 24, FP 447, FN 0)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| swarmos_mhb_sep vs swarmos | tasks_complete | 5 | 11.67 | [-51.09, 74.43] | 2/5 | not met |
| swarmos_nofb vs swarmos | tasks_complete | 5 | 71.67 | [34.65, 108.68] | 5/5 | MET |

## rush_50/loss10

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos | 0/5 | 4.4 | None | 0 | 9 | 0 | 178.2 | 15.6 | 17.8 | 1000.8 | 1.0097 | 0.72 |
| swarmos_mhb_sep | 0/5 | 7.0 | None | 0 | 2 | 0 | 204.0 | 7.8 | 10.0 | 827.8 | 0.9857 | 0.722 |
| swarmos_nofb | 0/5 | 6.2 | None | 0 | 7 | 0 | 98.4 | 12.6 | 14.2 | 884.2 | 0.9998 | 0.7191 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.5748, recall 0.8918, mean lead 17.418 ticks (TP 173, FP 128, FN 21)
- `swarmos_mhb_sep`: precision 0.6374, recall 0.9393, mean lead 15.344 ticks (TP 232, FP 132, FN 15)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| swarmos_mhb_sep vs swarmos | tasks_complete | 5 | 149.17 | [-108.71, 407.04] | 4/5 | not met |
| swarmos_nofb vs swarmos | tasks_complete | 5 | 90.0 | [-63.17, 243.17] | 4/5 | not met |

## rush_50/loss30

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos | 0/5 | 5.4 | None | 0 | 4 | 0 | 498.8 | 15.0 | 10.4 | 762.0 | 0.9922 | 0.7313 |
| swarmos_mhb_sep | 0/5 | 7.0 | None | 0 | 3 | 0 | 440.4 | 6.6 | 9.8 | 871.4 | 0.9985 | 0.732 |
| swarmos_nofb | 0/5 | 5.0 | None | 2 | 15 | 2 | 147.8 | 27.8 | 15.6 | 1137.2 | 0.9875 | 0.634 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.5376, recall 0.9029, mean lead 19.168 ticks (TP 186, FP 160, FN 20)
- `swarmos_mhb_sep`: precision 0.6271, recall 0.9204, mean lead 17.08 ticks (TP 185, FP 110, FN 16)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| swarmos_mhb_sep vs swarmos | tasks_complete | 5 | 66.19 | [-52.16, 184.54] | 3/5 | not met |
| swarmos_nofb vs swarmos | tasks_complete | 5 | 14.44 | [-54.46, 83.35] | 2/5 | not met |

## rush_50/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos | 0/5 | 5.2 | None | 0 | 5 | 0 | 108.4 | 11.6 | 12.0 | 800.0 | 0.9928 | 0.72 |
| swarmos_mhb_sep | 0/5 | 5.6 | None | 0 | 4 | 0 | 92.0 | 12.0 | 14.6 | 1173.0 | 1.0124 | 0.722 |
| swarmos_nofb | 0/5 | 5.2 | None | 0 | 5 | 0 | 108.4 | 11.6 | 12.0 | 800.0 | 0.9928 | 0.72 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.5774, recall 0.9038, mean lead 17.152 ticks (TP 235, FP 172, FN 25)
- `swarmos_mhb_sep`: precision 0.5881, recall 0.9241, mean lead 16.244 ticks (TP 207, FP 145, FN 17)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| swarmos_mhb_sep vs swarmos | tasks_complete | 5 | 6.33 | [-23.45, 36.12] | 2/5 | not met |
| swarmos_nofb vs swarmos | tasks_complete | 5 | 0.0 | [0.0, 0.0] | 0/5 | not met |

## rush_50/outage3s

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos | 0/5 | 5.2 | None | 0 | 6 | 0 | 109.8 | 21.0 | 17.6 | 1117.6 | 0.9995 | 0.72 |
| swarmos_mhb_sep | 0/5 | 5.6 | None | 0 | 2 | 0 | 74.0 | 9.4 | 11.4 | 958.0 | 1.0059 | 0.742 |
| swarmos_nofb | 0/5 | 6.4 | None | 12 | 14 | 5 | 81.4 | 12.4 | 15.2 | 999.2 | 1.0065 | 0.008 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.5091, recall 0.8991, mean lead 17.012 ticks (TP 196, FP 189, FN 22)
- `swarmos_mhb_sep`: precision 0.6192, recall 0.9122, mean lead 16.694 ticks (TP 187, FP 115, FN 18)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| swarmos_mhb_sep vs swarmos | tasks_complete | 5 | 14.5 | [-79.7, 108.7] | 1/5 | not met |
| swarmos_nofb vs swarmos | tasks_complete | 5 | 29.0 | [-32.67, 90.67] | 3/5 | not met |

## rush_50/outage6s

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos | 0/5 | 5.4 | None | 0 | 8 | 0 | 89.0 | 13.8 | 9.2 | 828.4 | 0.9885 | 0.72 |
| swarmos_mhb_sep | 0/5 | 5.8 | None | 0 | 2 | 0 | 94.8 | 9.8 | 10.8 | 1054.4 | 0.9998 | 0.742 |
| swarmos_nofb | 0/5 | 6.4 | None | 15 | 19 | 5 | 79.0 | 10.0 | 8.6 | 637.2 | 1.0047 | 0.004 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.5241, recall 0.895, mean lead 16.994 ticks (TP 196, FP 178, FN 23)
- `swarmos_mhb_sep`: precision 0.5383, recall 0.8955, mean lead 16.856 ticks (TP 197, FP 169, FN 23)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| swarmos_mhb_sep vs swarmos | tasks_complete | 5 | 7.67 | [-18.98, 34.31] | 2/5 | not met |
| swarmos_nofb vs swarmos | tasks_complete | 5 | 22.14 | [-34.67, 78.96] | 2/5 | not met |

## rush_50/partition_east

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swarmos | 0/5 | 5.8 | None | 0 | 7 | 0 | 93.8 | 10.6 | 10.0 | 713.8 | 0.9823 | 0.72 |
| swarmos_mhb_sep | 0/5 | 6.6 | None | 0 | 3 | 0 | 82.8 | 13.2 | 14.8 | 1152.8 | 0.9966 | 0.722 |
| swarmos_nofb | 0/5 | 6.0 | None | 1 | 8 | 1 | 91.4 | 12.2 | 14.4 | 957.2 | 0.9877 | 0.4919 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.5611, recall 0.9, mean lead 16.748 ticks (TP 225, FP 176, FN 25)
- `swarmos_mhb_sep`: precision 0.5978, recall 0.9167, mean lead 16.39 ticks (TP 165, FP 111, FN 15)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| swarmos_mhb_sep vs swarmos | tasks_complete | 5 | 22.67 | [-37.17, 82.5] | 3/5 | not met |
| swarmos_nofb vs swarmos | tasks_complete | 5 | 4.0 | [-7.1, 15.1] | 1/5 | not met |
