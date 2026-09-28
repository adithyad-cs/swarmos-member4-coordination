# Controlled improvement cycle, 2026-09-27

This follows `docs/C2_ROOT_CAUSE_ANALYSIS.md`, sections C and D, in the
declared order: F1, then F1+F3, then +F5, then +F6. F2(a) is evaluated only if
freezes still cause failures.

- Development seeds: 700001-700020 (`tools/run_experiment.py DEV_SEEDS`),
  declared before any fix was measured.
- The seeds are disjoint from the frozen C2 evaluation seeds (pinned by
  `tests/test_c2_protocol.py`).
- Every number below is the whole 20-seed block. Nothing was tuned on one seed.

The frozen C2 experiment (`reports/experiments/20260927T045112Z_c2_frozen`)
is untouched. Its full replay reproduced **320/320** runs exactly under the
frozen identity (`reports/audit_20260927/replay_c2_frozen_all.log`). The
cycle was developed in an isolated copy while that replay ran, and was copied
in only after it finished.

Raw data: `reports/experiments_dev_20260927/` (config, runs.jsonl, summary
per step; `compare.py` prints the table below).

## What each fix is

Every fix is flag-controlled and OFF by default, so the product and the
frozen baselines are unchanged until enabled. With every flag off, the code
reproduces the frozen C2 trace hashes bit for bit (checked on three arms).

| Fix | Where | What | Safety argument |
|---|---|---|---|
| F1 | `app/sim/sweep.py`; `SwarmPolicy(polyline_sweep=)`; `StopAndWaitPolicy.POLYLINE_SWEEP` | The safety check tests the real path a step drives (the legs through its waypoints) as well as the old chord. Shared by BOTH arms. | The sweep always contains the old chord, so it can only veto more. Tests: the traced corner case, "never less strict than the chord" (2,000 random cases), and a real SimRobot step always lying on its sweep (300 cases). |
| F3 | `SwarmPolicy(leader_rule=)`, `_leader_verdict` | In the contest band, a robot not closing on its peer keeps right of way; the closing one yields. After `YIELD_PATIENCE` it hands back to the contest. | Ladder only; the kernel vets every step. |
| F5 | `SwarmPolicy(standoff_breaker=)`, `_break_standoff`; `Verdict.avoid_points` | After 2 s of mutual hold, a deterministic loser (alternating every 20 s) replans around the peer's cell and its next 3 m of route. | It turns a hold into a hold-and-replan (REROUTE, zero motion), so it grants no motion. |
| F6 | `SimEngine.release_cooldown_ticks` | After a stall release, the same robot may not take the same task back for 30 s. | Dispatch only. Engine-level, so it applies to EVERY arm, the baselines included. |

## Results (20 dev seeds per cell; 0 collisions, 0 invariant failures in every cell)

"Capped mean" counts a run that did not finish at the 3000 s cap. Frozen
pairs are pairs inside the 0.75 m floor for at least 60 s at the end of a
run. Recovery actions are REROUTE verdicts and stall releases.

| Scenario | Arm | Finished | Mean time, finished (s) | Capped mean (s) | Margin breaches | Frozen pairs | Replans | REROUTE | Stall releases | Persistent deadlocks |
|---|---|---|---|---|---|---|---|---|---|---|
| overlap | stop_and_wait | 9/20 | 914 | 2062 | 0 | 0 | 1528 | 711 | 44 | 99 |
| overlap | stop_and_wait+F1+F6 | 7/20 | 857 | 2250 | 0 | 0 | 1533 | 734 | 2.5 | 138 |
| overlap | baseline (tuned) | 12/20 | 773 | 1664 | 0 | 0 | 523 | 228 | 1.3 | 0.8 |
| overlap | baseline+F1+F6 | 14/20 | 718 | 1402 | 0 | 0 | 507 | 221 | 1.1 | 0.7 |
| overlap | swarmos (unchanged) | 11/20 | 577 | 1667 | 10 | 10 | 13063 | 6424 | 166 | 134 |
| overlap | swarmos+F1 | 17/20 | 659 | 1010 | 0 | 0 | 4973 | 2428 | 56 | 85 |
| overlap | swarmos+F1+F3 | 15/20 | 482 | 1111 | 0 | 0 | 10197 | 5031 | 76 | 62 |
| overlap | swarmos+F1+F3+F5 | 20/20 | 486 | 486 | 0 | 0 | 695 | 312 | 1.5 | 5.5 |
| overlap | **swarmos+F1+F3+F5+F6** | **20/20** | **485** | **485** | 0 | 0 | 684 | 307 | 1.5 | 4.2 |
| overlap | swarmos+F1+F5 (control) | 19/20 | 601 | 721 | 0 | 0 | 1924 | 928 | 0.9 | 62 |
| overlap | swarmos+F1+F5+F6 (control) | 20/20 | 599 | 599 | 0 | 0 | 857 | 394 | 1.0 | 3.0 |
| open floor | stop_and_wait | 10/20 | 565 | 1782 | 1 | 0 | 3657 | 1754 | 51 | 468 |
| open floor | stop_and_wait+F1+F6 | 13/20 | 556 | 1412 | 0 | 0 | 2453 | 1173 | 5.7 | 358 |
| open floor | baseline (tuned) | 10/20 | 785 | 1892 | 1 | 0 | 10425 | 5080 | 154 | 12 |
| open floor | baseline+F1+F6 | 13/20 | 737 | 1529 | 0 | 0 | 7049 | 3436 | 55 | 6.5 |
| open floor | swarmos (unchanged) | 0/20 | - | 3000 | 49 | 48 | 61094 | 30092 | 926 | 418 |
| open floor | swarmos+F1 | 8/20 | 744 | 2098 | 0 | 0 | 32179 | 15839 | 449 | 461 |
| open floor | swarmos+F1+F3 | 12/20 | 638 | 1583 | 0 | 0 | 21200 | 10433 | 250 | 338 |
| open floor | swarmos+F1+F3+F5 | 14/20 | 602 | 1321 | 0 | 0 | 11305 | 5545 | 121 | 17 |
| open floor | **swarmos+F1+F3+F5+F6** | **20/20** | **649** | **649** | 0 | 0 | 2281 | 1083 | 5.8 | 32 |
| open floor | swarmos+F1+F5 (control) | 18/20 | 661 | 895 | 0 | 0 | 6770 | 3318 | 32 | 77 |
| open floor | swarmos+F1+F5+F6 (control) | 16/20 | 654 | 1123 | 0 | 0 | 7918 | 3889 | 23 | 68 |

## Paired statistics

Final SWARMOS (F1+F3+F5+F6) against stop-and-wait with the shared fixes
(F1+F6: the same safety geometry and the same engine), from
`reports/experiments_dev_20260927/*_dev4_F6/summary.md`:

| Metric | overlap | open floor |
|---|---|---|
| Capped-time reduction | **+60.6%, 95% CI [43.4, 77.7]**, 19/20 wins, admissible (no seed failed by SWARMOS alone) | +13.8%, CI [-10.6, 38.3] |
| Time on seeds both finished | +17.6%, CI [-10.8, 45.9] (n = 7, 6 wins) | **-21.5%, CI [-34.1, -9.0]** (n = 13): SWARMOS is SLOWER |
| t90, capped | +33.6%, CI [17.3, 49.8] | +13.6%, CI [-5.8, 33.1] |
| Seeds failed by the reference alone | 13 | 7 |

## Decisions at each step

1. **F1: keep.** It removed every floor entry and every frozen pair
   (overlap 10 -> 0, open floor 48 -> 0). It barely changed the baselines,
   which had almost no floor entries, so the shared geometry fix does not favour
   SWARMOS.
2. **F3: mixed alone.** On its own (open floor better, overlap -2 finishes) and
   on top of F5 (overlap better, open floor worse) the result was mixed. A
   control arm without F3 was added rather than deciding by judgement. With
   F6, F3 is better on BOTH scenarios (F1+F3+F5+F6 against F1+F5+F6: 40/40
   against 36/40 finished; 485 against 599 s and 649 against 1123 s). **Kept.**
3. **F5: the decisive fix.** Overlap went from 15-17/20 to 20/20. Replans fell
   15x and stall releases fell from about 76 to 1.5. **Kept.**
4. **F6: kept.** It completes the open floor (14 -> 20/20). It applies to the
   baselines too: open floor 10 -> 13/20 for both; overlap for the textbook
   arm 9 -> 7/20 and for the tuned arm 12 -> 14/20.
5. **F2(a): not needed and not implemented.** Since F1 there are 0 floor
   entries and 0 frozen pairs in every SWARMOS dev run, so the condition
   ("freezes still cause failures") is not met. The SWARMOS kernel keeps no
   separating escape. The at-floor rule therefore still differs from the
   baseline's, which keeps its own escape. The rule is never exercised by
   SWARMOS in these runs.

## Still open (measured, not hidden)

- **Open floor: SWARMOS is about 21% slower than stop-and-wait on the seeds
  both finish.** Its lead comes from finishing seeds the baseline does not.
- **A mirror-dodge livelock was traced** (dev 700012, open floor, F1+F3+F5):
  two robots switch lanes in lockstep in a two-lane aisle. F6 happened to clear
  it in the final configuration. A sliding-window standoff detector (F5') is
  the candidate if it reappears; it was not added inside this plan.
- These are DEVELOPMENT results on 20 seeds. They are not a C2 claim. A C2
  claim needs:
  - a new frozen protocol;
  - the new code identity;
  - arms defined as above (the references carry the shared F1+F6 fixes);
  - 30+ NEW evaluation seeds (900001-900040 are spent).
- The fixes are OFF in the product policy (`app/api/runner._make_policy`)
  until that decision is made.
