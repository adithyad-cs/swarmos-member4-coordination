# Experiment `c2v3_pipeline_smoke`

- git: `a6e18041c8151077485fcdb63c6fc1769594cefa+uncommitted-changes`
- code identity (sha256): `f3dabbf0d732bfc218a1ab31f906299ca1baee5c4b1de148534b16c0d023094f`
- created: 20260927T130648Z
- seeds: [101, 102]
- reference arm: `stop_and_wait+F1+F6`
- command: `PYTHONPATH=. python3 tools/run_experiment.py --name c2v3_pipeline_smoke --scenarios overlap_batch --arms stop_and_wait+F1+F6 baseline+F1+F6 swarmos --reference stop_and_wait+F1+F6 --seeds 101 102 --workers 4`

Makespan for runs that did not finish is CENSORED at the scenario cap. That understates the failing arm's true time, so it flatters the arm that finishes less; a censored target is marked MET only when the treatment never failed a seed the reference finished.

## overlap_batch/normal

| arm | DNF | tasks done (mean) | makespan censored (mean s) | collisions | margin breaches | safety FAIL runs | wait-cycles (mean) | persistent deadlocks >=1 s (mean) | stall releases (mean) | livelock episodes (mean) | replans (mean) | path eff. | min sep (m) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline+F1+F6 | 1/2 | 23.5 | 1682.4 | 0 | 0 | 0 | 73.0 | 0.0 | 0.0 | 3.0 | 377.5 | 0.7355 | 0.772 |
| stop_and_wait+F1+F6 | 1/2 | 23.0 | 1764.2 | 0 | 0 | 0 | 102.0 | 84.0 | 1.0 | 5.0 | 426.5 | 0.6323 | 0.7864 |
| swarmos | 0/2 | 24.0 | 499.95 | 0 | 0 | 0 | 51.0 | 28.5 | 0.0 | 0.5 | 734.5 | 0.8599 | 0.756 |

| arm | finish rate | makespan finished (mean / median s) | t90 censored (mean s) | throughput (tasks/min) | WAIT | YIELD | REROUTE | stop events | backtracks | conflicts / resolved | predicted | comm holds | invariant failures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline+F1+F6 | 0.5 | 364.8 / 364.8 | 419.35 | 2.205 | 1269.5 | 0.0 | 155.5 | 260.0 | 63.0 | 192.5 / 192.5 | 0.0 | None | 0 |
| stop_and_wait+F1+F6 | 0.5 | 528.4 / 528.4 | 617.15 | 1.58 | 5926.5 | 0.0 | 179.0 | 360.5 | 103.0 | 284.5 / 284.5 | 0.0 | None | 0 |
| swarmos | 1.0 | 499.95 / 499.95 | 425.75 | 2.91 | 443.5 | 2402.0 | 334.0 | 197.5 | 131.0 | 43.0 / 41.5 | 88.5 | 0.0 | 0 |

| arm | floor entries (total) | floor pair-ticks (mean) | frozen pairs (total) | runs with a frozen pair | recovery actions (mean: stall releases + REROUTE) |
|---|---|---|---|---|---|
| baseline+F1+F6 | 0 | 0.0 | 0 | 0 | 155.5 |
| stop_and_wait+F1+F6 | 0 | 0.0 | 0 | 0 | 180.0 |
| swarmos | 0 | 0.0 | 0 | 0 | 334.0 |

Lookahead (observe-only scoring):

- `swarmos`: precision 0.4746, recall 0.9767, mean lead 13.87 ticks (TP 84, FP 93, FN 2)

| comparison | metric | n | mean improvement % | 95% CI % | wins | >= target? |
|---|---|---|---|---|---|---|
| baseline+F1+F6 vs stop_and_wait+F1+F6 | makespan_censored_s | 2 | -189.96 | [-3719.63, 3339.72] | 1/2 | not met |
| baseline+F1+F6 vs stop_and_wait+F1+F6 | t90_censored_s | 2 | 25.86 | [-327.86, 379.58] | 1/2 | not met |
| baseline+F1+F6 vs stop_and_wait+F1+F6 | tasks_complete | 2 | 2.46 | [-81.76, 86.69] | 1/2 | not met |
| swarmos vs stop_and_wait+F1+F6 | makespan_censored_s | 2 | 40.42 | [-526.28, 607.12] | 1/2 | not met |
| swarmos vs stop_and_wait+F1+F6 | t90_censored_s | 2 | 27.14 | [-194.3, 248.57] | 2/2 | not met |
| swarmos vs stop_and_wait+F1+F6 | tasks_complete | 2 | 4.55 | [-53.21, 62.3] | 1/2 | not met |

- `baseline+F1+F6 vs stop_and_wait+F1+F6`: treatment-only DNF seeds [101]; reference-only DNF seeds [102]

- `swarmos vs stop_and_wait+F1+F6`: treatment-only DNF seeds none; reference-only DNF seeds [102]
