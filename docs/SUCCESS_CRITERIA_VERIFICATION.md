# Success criteria - measured, including the two defects the measurement found

> **CURRENT C2 STATUS (2026-09-27): MET for the product-default configuration,
> under frozen protocol v3.** Full result: `docs/C2_V3_PRODUCT_RESULT.md`;
> narrative: `docs/JUDGE_NARRATIVE_C2_V3.md`. All figures are simulation.
>
> - **Primary** (`overlap_batch`, SWARMOS product vs textbook stop-and-wait +
>   F1 + F6, 40 fresh seeds 600001-600040):
>   - capped time reduction **+48.9 %, 95 % CI [+35.3, +62.5]**;
>   - finish rate SWARMOS 40/40 vs reference 21/40;
>   - no seed failed only by SWARMOS;
>   - all five frozen conditions passed.
> - **Speed caveat:** on seeds where both finished, **+17.5 %, CI [+1.4,
>   +33.6]**. That is below 20 % if speed alone is considered; the primary gain
>   is substantially reliability.
> - **Open floor (secondary):**
>   - capped **+33.7 %, CI [+4.5, +62.8]**;
>   - finish rate 40/40 vs 15/40;
>   - SWARMOS is **slower** when both finish (-44.4 %, CI [-105.8, +17.1]).
> - **Safety (240 runs):**
>   - 0 collisions, 0 invariant failures;
>   - SWARMOS had 0 margin breaches and 0 frozen pairs;
>   - the only margin breach was the tuned reference arm, open floor, 0.748 m.
> - **Integrity:**
>   - replay 240/240 exact;
>   - code identity `f3dabbf0d732bfc218a1ab31f906299ca1baee5c4b1de148534b16c0d023094f`.
>
> **The C2 sections below are HISTORY and are SUPERSEDED.** They cover the
> avg_completion_s measurement (NOT MET, -19.3 %) and the 2026-09-26
> fixed-batch measurement (NOT MET, parity). They are kept unchanged as the
> record of how the result was reached: v1 NOT MET, then root cause, then
> fixes, then v2 on the evaluated arm, then v3 on the product.

SWARMOS / SIH26123. This document records what was measured, on what code, with
what result. It replaced an earlier version that reported **C1 PASS** and noted
that the stop-and-wait baseline was "also collision-free". Both of those
statements were false. They were produced by a 1800-tick verification that was
too short to reach the failure, and correcting them is the substance of this
document.

Reproduce everything here with:

```
cd <repo>
PYTHONPATH=. python3 tools/verify_criteria_powered.py 9000 9
```

Runtime is about 38 minutes. Seeds are `11 13 17 19 23 29 31 37 41`, scenarios
are `rush_50` (fleet 50), `narrow_aisle_deadlock` (fleet 24) and `blocked_aisle`
(fleet 40), and every seed is run in **paired arms** - the same scenario and the
same seed under `baseline` (tuned stop-and-wait) and under `swarmos`.

---

## C1 - zero collisions

**Criterion.** No pair of robots ever comes within `COLLISION_DISTANCE_M = 0.70`
m, the footprint of two 0.35 m robots, in the SwarmOS arm.

### What the first powered run actually returned

The earlier 1800-tick run reported zero collisions in both arms and was published
as a PASS. Extending the same harness to 9000 ticks and nine seeds, and splitting
the collision count **per arm** (`tools/patch_criteria_c1_arms.py`), returned:

```
C1 zero collisions in the SwarmOS arm: 7  FAIL
   baseline arm collisions (control, expected > 0): 0
   blocked_aisle seed=29 swarmos=1
   rush_50      seed=19 swarmos=1
   rush_50      seed=29 swarmos=2
   rush_50      seed=31 swarmos=2
   rush_50      seed=41 swarmos=1
```

Seven collisions, **all of them in the SwarmOS arm and none in the stop-and-wait
control** - the exact inverse of the project's central safety claim. The
aggregate count in the old harness had hidden which arm they belonged to, and
1800 ticks never reached tick 700, where the first one happens.

This is recorded in full rather than quietly fixed because the shape of the
failure is the useful part: a safety argument that is only ever checked on short
runs is not a safety argument.

### Defect 1 - the engine moved robots further than the arbiter authorised

`tools/diag_c1_monitor.py blocked_aisle 29 700 R007 R019` gave the decisive
trace. At tick 699 the safety monitor cleared `scale=0.25`, believing closest
approach would be 0.7539 m - a margin of 0.0039 m above the 0.750 m hard-stop
floor - and so authorised at most `0.25 * MAX_STEP_M = 0.055` m of travel. The
engine then displaced R007 by **0.0777 m**, when its charged motion budget was
only `v * dt = 0.160 * 0.1 = 0.016` m. `path_pts` fell from 5 to 4 on the same
tick.

Root cause, `app/sim/robot.py`, inside `SimRobot.step`:

```python
if leg <= WAYPOINT_TOLERANCE_M:
    self.x, self.y = wx, wy
    self.path.pop(0)
    continue
```

The snap exists to stop float error drifting a robot off the aisle centreline,
which is legitimate. But it charged neither `moved` nor `budget`, so a robot
collected up to `WAYPOINT_TOLERANCE_M = 0.08` m of **free, uncharged**
displacement per waypoint per tick, on top of whatever its granted speed allowed.

That breaks the single invariant the whole coordination layer rests on: granting
`speed_scale = f` must move a robot at most `f * MAX_STEP_M`. Once it is broken
no margin is meaningful, because the monitor is clearing a swept envelope the
engine does not respect.

**Fix** (`tools/patch_c1_waypoint_snap.py`): take the snap only when the budget
can afford it, and charge it.

```python
if leg <= WAYPOINT_TOLERANCE_M and leg <= budget:
    self.x, self.y = wx, wy
    self.path.pop(0)
    moved += leg
    budget -= leg
    continue
```

An unaffordable near-waypoint falls through to the proportional branch and snaps
on a later tick, so the anti-drift guarantee survives without granting motion
nobody authorised.

**Effect**, re-measured at 9000 ticks with `tools/diag_c1_stepbound.py`:

| run | collisions | overlap ticks | near misses | worst overshoot |
|---|---|---|---|---|
| blocked_aisle 29 | 1 -> 0 | 8301 -> 0 | 230010 -> 12658 | 0.000000 m |
| rush_50 19 | clean | 0 | - | 0.000000 m |
| rush_50 31 | clean | 0 | - | 0.000000 m |

Full re-run of the powered harness: **7 collisions -> 1**
(`reports/criteria_after_c1fix.log`).

Two probe bugs were found while verifying this, and both are worth recording
because either one would have produced a confident wrong answer:

- Using the **post-step `velocity`** as the bound reported 24 phantom breaches of
  exactly 0.200 m. `SimRobot.step` zeroes `velocity` on arrival, and `_drain`
  does the same on a flat battery, so the post-step value is not the velocity the
  tick ran at.
- Sampling **`speed_scale` before `eng.step()`** reported 566 phantom breaches.
  `_apply_verdicts` assigns `speed_scale` *inside* `step()`, before the robots
  move, and nothing resets it afterwards - so the **post**-step value is the
  grant that governed the tick that just ran.

### Defect 2 - the monitor bounded its own step with a truncated projection

One collision survived. `tools/diag_c1_stepbound.py blocked_aisle 17 9000`
reported `worst overshoot 0.000000 m` and zero step-authority breaches, yet still
`collisions=1 overlap_ticks=8282` - proving the residual was a different
mechanism, not a weaker version of the first.

`tools/diag_c1_collision.py blocked_aisle 17 9000` localised it:

```
COLLISION at tick=719  closest pair R030-R040 at 0.6980 m
  R030 MOVING  (47.466, 39.5) v=0.540
  R040 WAITING (48.164, 39.5) v=0.000
```

`tools/diag_c1_pair.py blocked_aisle 17 714 720 R030 R040` showed the pair
closing steadily under SLOW verdicts - 0.7900, 0.7820, 0.7720, 0.7660, 0.7520 -
and then, at 719, R030 cleared to full speed and drove into a stationary R040.
`tools/diag_c1_monitor.py blocked_aisle 17 721 R030 R040` named the cause at
tick 718:

```
tick=718 intent=yes step_len=0.0440 rest_gap=0.7520
    swept_gaps  1.00:0.7520  0.75:0.7520  0.50:0.7520  0.25:0.7520
    verdict=PROCEED speed_scale=1.0
ENGINE tick=719 moved=0.0540 scale=1.000 d 0.7520 -> 0.6980
```

The monitor built its swept envelope from `project_step(me, MAX_STEP_M)`, which
walks the robot's **published movement intent**. When the remaining path is
shorter than a step, that projection stops at the end of the path - here 0.0440
m. Every swept gap therefore read back as the standing-still gap 0.7520 m, every
fraction of the ladder looked clear, and the full step was granted. The engine
then moved R030 0.0540 m straight at R040, crossing both the 0.750 m floor and
the 0.700 m collision distance in one tick.

The projection is **not** an upper bound on one tick of motion. The path is
consumed as the robot moves, a replan can lengthen it, and the reported copy the
monitor reads lags the true state. Whenever the projection is shorter than
`MAX_STEP_M` the envelope silently understates the approach, and an understated
envelope makes the entire floor unsound: no margin survives if the monitor is
measuring the wrong segment.

**Fix** (`tools/patch_c1_sound_envelope.py`): keep the direction, which the
projection does know, and extend the distance to the step the engine can actually
deliver.

```python
def _step_envelope(here, projected):
    dx, dy = projected[0] - here[0], projected[1] - here[1]
    reach = math.hypot(dx, dy)
    if reach <= 1e-12 or reach >= MAX_STEP_M:
        return projected
    grow = MAX_STEP_M / reach
    return (here[0] + dx * grow, here[1] + dy * grow)
```

A robot with no direction at all is left where it stands: inventing a heading for
a stationary robot would manufacture motion nobody intends and wedge the aisle.
The change is strictly conservative - the envelope only ever grows - so nothing
previously refused becomes allowed.

Deliberately **not** changed: the `granted` segments a robot publishes for its
peers, which also call `project_step`. Assuming more peer motion than was granted
was already measured to cost 31 percent of robot-ticks to phantom motion. Only
the bound a robot applies to **itself** was unsound, and only that was widened.

**Effect**, `tools/diag_c1_stepbound.py`, 9000 ticks:

| run | collisions | overlap ticks | tasks done | avg completion |
|---|---|---|---|---|
| blocked_aisle 17 | **1 -> 0** | **8282 -> 0** | 13 | 109.86 s |
| blocked_aisle 29 | 0 | 0 | 8 | 103.13 s |
| blocked_aisle 19 | 0 | 0 | 11 | 116.33 s |

### Regression cover

`tests/test_c1_step_authority.py`, four tests, all of which fail on the pre-fix
code:

- `test_displacement_never_exceeds_granted_speed[blocked_aisle-29]` and
  `[rush_50-19]` - 800 ticks, asserts per-tick travel never exceeds
  `max_speed * speed_scale * dt`. Catches defect 1 directly.
- `test_blocked_aisle_seed29_is_collision_free_past_tick_700` - runs to 900, past
  the failure, so a fix that merely delays the breach does not pass.
- `test_blocked_aisle_seed17_is_collision_free_past_tick_719` - defect 2. Note
  that the step-authority test above **cannot** catch this one; it needed its own
  case.
- `test_step_envelope_never_understates_a_tick_of_motion` - unit cover on
  `_step_envelope`: a short projection is grown to `MAX_STEP_M`, a long one is
  left alone, a stationary robot is not moved, and the bearing is preserved.

Full suite after both fixes: **575 passed in 91.81 s**.

### C1 verdict

**C1 is MET as of the post-defect-2 measurement: 0 collisions across 27 paired
9000-tick runs** (`reports/criteria_after_envelope_fix.log`, quoted in full in
the "Final powered result" section below). That statement is only worth what the
route to it is worth, so the route is stated plainly: the criterion was *not*
met when it was first measured honestly, the earlier measurement that said it
was had been run too short to expose the failures, two real defects were behind
the 7 collisions, both were root-caused to a specific tick and a specific line,
both were fixed, and both fixes are now pinned by tests that fail on the old
code.

Note also what C1 does **not** show. The stop-and-wait control is collision-free
too. C1 is therefore **necessary rather than differentiating**: what it
establishes is that negotiation, containment and sovereign fallback did not cost
us the safety property - not that they bought it.

---

## C2 - 20 percent reduction in average task completion time

> SUPERSEDED (history). Current C2 status: the box at the top of this file and
> `docs/C2_V3_PRODUCT_RESULT.md`.

**Criterion.** SwarmOS reduces `avg_completion_s` by at least 20 percent against
the stop-and-wait baseline, paired by scenario and seed.

### Result

From the post-defect-1 powered run (`reports/criteria_after_c1fix.log`, 9000
ticks, 9 seeds, 3 scenarios, 27 paired runs):

```
C2 paired reduction in avg_completion_s, n=27 paired runs
  mean            : -13.7 pct
  std dev         :  32.7 pct
  95 pct CI       : [-26.6, -0.7] pct
  target          : >= 20 pct
  tasks completed : min=1  median=10  max=28  (per arm per run)
  verdict         : NOT MET - the whole interval sits below the bar
```

**C2 is NOT MET, and the sign is negative.** On this statistic, over these
scenarios, SwarmOS is *slower* than stop-and-wait, and the 95 percent confidence
interval lies entirely below zero. That is reported as measured. The earlier
document quoted +2.3 percent from a 1800-tick run; the powered number is worse,
and the powered number is the one that counts.

### Two structural findings that matter more than the number

The previous document listed four things that "would make C2 answerable". Two of
them have now been settled, and the answers change what the criterion can mean.

**1. Task supply, not run length, is the binding constraint - so longer runs
cannot power C2.** At 9000 ticks the `blocked_aisle` baseline numbers are
byte-identical to the 1800-tick run: seeds 11/13/17 give 85.19 / 74.54 / 90.27 s
with 16 / 14 / 14 tasks done. Five times the run length produced **zero
additional completed tasks** - the scenario's task generator is exhausted. This
confirms item 4 of the old list and **refutes item 1**: "run it for 18000 ticks"
was the wrong prescription and would have burned an hour to reproduce the same
numbers. The effect is scenario-specific - `narrow_aisle_deadlock` is *not*
exhausted at 1800 (seed 11 baseline moves 96.49 -> 112.74 s) - which is exactly
why a single aggregate over three scenarios was misleading.

**2. `avg_completion_s` compared across arms is survivorship-biased, and is the
wrong statistic for C2.** `narrow_aisle_deadlock` seed 11: the baseline records
112.74 s with **12 tasks done**; SwarmOS records 83.57 s with **3 tasks done**.
The harness scored that "+25.9 percent better". SwarmOS looks faster only because
it finished a quarter as many tasks - the easy ones. The mean of the completed
subset says nothing about the arm when the subsets differ in size and in
difficulty.

A sound C2 must therefore either compare at **equal completion counts** (the
time to the *n*th completion, with *n* the lesser of the two arms) or measure
**throughput** (`tasks_per_min` over a fixed horizon), which has no survivorship
problem because the denominator is wall-clock, not a self-selected sample.

### What we claim, and what we do not

We do not claim C2. We claim that the criterion as written is not measurable on
these scenarios, that we know precisely why, and that the honest replacement is
specified. Presenting +57.9 percent (the best single seed) would be as wrong as
presenting -47.8 percent (the worst).

Remaining work on C2, in the order that would change a conclusion:

1. Re-score the existing paired runs with an equal-completion-count statistic and
   with `tasks_per_min`. No new simulation needed - the data is already on disk.
2. Raise task supply in `blocked_aisle` and `rush_50` until neither arm is
   idle-limited, then re-run. Until that holds, no coordination policy can move
   the number.
3. Only then, more seeds and a confidence interval on the corrected statistic.

---

## Final powered result

> SUPERSEDED (history): an avg_completion_s measurement from before the fixed-batch
> protocol. Current C2 status: the box at the top of this file.

Reproduced with `tools/verify_criteria_powered.py 9000 9`; 3 scenarios x 9 seeds
x 2 arms = 54 runs, 27 pairs, wall clock 2319.9 s. Log:
`reports/criteria_after_envelope_fix.log`.

```
C1 zero collisions in the SwarmOS arm: 0  PASS
   baseline arm collisions (control, expected > 0): 0
--------------------------------------------------------------------------
C2 paired reduction in avg_completion_s, n=27 paired runs
  mean            : -19.3 pct
  std dev         :  42.2 pct
  95 pct CI       : [-36.0, -2.6] pct
  target          : >= 20 pct
  tasks completed : min=1  median=10  max=28  (per arm per run)
  verdict         : NOT MET - the whole interval sits below the bar
  elapsed         : 2319.9 s
```

### What this says

- **C1: PASS.** Zero collisions, zero overlap ticks, in the arm that previously
  produced 7 collisions. No `SwarmOS collision run:` line appears anywhere in the
  log - the collision reporter printed nothing because there was nothing to
  report. The two per-seed regression tests (`blocked_aisle` 29 and 17) lock the
  two specific ticks that used to fail.
- **C1 control caveat, unchanged.** The stop-and-wait baseline is also at 0. C1
  is necessary, not differentiating: it shows negotiation, containment and
  sovereign fallback did not cost the safety property.
- **C2: still NOT MET, and the point estimate moved further negative**, from
  -13.7 pct to **-19.3 pct**, with the CI widening to [-36.0, -2.6] pct. The
  interval still lies entirely below zero, so the direction is not in doubt on
  this statistic.

### Why C2 got worse when a safety bug was fixed

This is the expected direction, and it is worth saying out loud rather than
hiding. Defect 2 was the arbiter under-estimating a robot's own one-tick reach,
so it was granting speed it should have withheld. Making the bound sound means
the arbiter now withholds that speed. Throughput paid for safety - which is
precisely the trade a binding safety arbiter exists to make. A number that had
improved after this fix would have been evidence the fix was not doing anything.

It remains true that the statistic itself is unsound for a cross-arm comparison
(see the survivorship-bias finding above): `avg_completion_s` averages only the
tasks that finished, and the two arms do not finish the same tasks. The honest
reading of C2 today is "not met on a biased statistic, and not yet measured on an
unbiased one", and fixing the statistic is the first roadmap item - not because
it is likely to flip the sign, but because the current number cannot support
either conclusion.

---

## 2026-09-26 addendum - C2 re-measured the way SIH defines it

> SUPERSEDED (history) by the frozen v1 -> v2 -> v3 evaluations of
> 2026-09-27. Current C2 status: the box at the top of this file and
> `docs/C2_V3_PRODUCT_RESULT.md`.

The section above scored C2 on `avg_completion_s` over an open arrival stream,
which is survivorship-biased (only finished tasks count, and a run finished
1-28 tasks). SIH26123 asks for *total task-completion time versus traditional
stop-and-wait on overlapping paths*. That is only defined for a FIXED workload,
so it is now measured as **makespan on a fixed batch**, the definition used by
the lifelong-MAPF literature (Maoudj et al., CASE 2024).

Every number below comes from a stored experiment directory containing the
config, git revision, every run with its trace hash, and the summary. Anyone
can re-run a stored run and check the hash:

    PYTHONPATH=. python3 tools/replay_check.py reports/experiments/<dir>

### Setup

- `overlap_batch`: single-file aisles, picks on the south wall, drops on the
  north wall, so loaded and empty robots meet head-on in the same aisles.
  8 robots, 24 tasks, cap 3000 s.
- `open_floor_batch`: the `rush_50` two-way-aisle floor, 12 robots, 36 tasks,
  cap 3000 s.
- Arms:
  - `stop_and_wait`: textbook, `STUCK_TICKS=30`. This is the SIH arm.
  - `baseline`: tuned, `STUCK_TICKS=8`.
  - `swarmos`: the product policy.
  - flagged variants of `swarmos`.
  - `noop`: the negative control.
- 9 paired seeds (11 13 17 19 23 29 31 37 41), with a Student-t 95% CI on the
  per-seed percentage reduction.
- A run that hits the cap is did-not-finish (DNF), and its makespan is CENSORED
  at the cap. That understates the failing arm's time, so censoring can never
  create an improvement.

### Defects the new instruments found first (fixed before measuring)

1. **Backtrack jog outside the verified envelope.**
   - A fresh path began at the centre of the robot's current cell. A robot a
     few cm past it drove back first.
   - That motion lay outside the straight swept segment the kernel clears. It
     pushed pairs inside the 0.75 m floor, where the kernel vetoes every move
     of both robots.
   - Fixed in the engine (`_drop_backtrack`), for all arms.
   - Measured on seed 11: deadlock cycles 221 -> 27, stall releases in the
     hundreds -> 1.
2. **Idle robots parked on drop stations.** A drop station is a cell in a
   single-file row, so a parked robot blocked it. Batch scenarios now park
   idle robots on the perimeter ring, for both arms.

### Result (`reports/experiments/20260926T212555Z_c2_benchmark`, `..._deadlock_breakers`)

| scenario | arm | DNF | mean makespan, censored (s) | persistent deadlocks >=1 s | collisions |
|---|---|---|---|---|---|
| overlap_batch | stop_and_wait | 1/9 | 855 | 31.7 | 0 |
| overlap_batch | baseline (tuned) | 0/9 | 569 | 3.4 | 0 |
| overlap_batch | swarmos | 4/9 | 1718 | 257.1 | 0 |
| overlap_batch | swarmos + mutual-hold break + separating exemption | **0/9** | **619** | **8.1** | 0 |
| open_floor_batch | stop_and_wait | 3/9 | 1379 | 199.8 | 0 |
| open_floor_batch | baseline (tuned) | 3/9 | 1380 | 4.0 | 0 |
| open_floor_batch | swarmos | 8/9 | 2773 | 34.7 | 0 |
| open_floor_batch | swarmos + both breakers | 4/9 | 1725 | 101.2 | 0 |
| both | noop (no coordination) | 0/9 | 311 / 448 | - | **316 / 639** |

**Paired makespan reduction vs textbook stop-and-wait (positive = SWARMOS faster):**

- `overlap_batch`:
  - `swarmos`: -226.6%, CI [-449.6, -3.6]
  - `swarmos` + both breakers: **-5.5%, CI [-42.3, +31.2]** (parity)
- `open_floor_batch`:
  - `swarmos`: -245.1%, CI [-412.5, -77.7]
  - `swarmos` + both breakers: -138.4%, CI [-315.6, +38.8]

**C2 verdict: NOT MET.**

- The best SWARMOS variant reaches statistical parity with textbook
  stop-and-wait on the overlapping-paths floor and still trails it on the open
  floor.
- The tuned baseline beats both, which shows how much of this benchmark comes
  down to the deadlock-recovery timeout rather than to negotiation.
- This is published as measured.
- The no-coordination control is fastest only because it drives through other
  robots: 316-639 contact violations. That is why fast-and-unsafe is not a
  comparison arm.

### What did help, and what did not (ablation)

| change | effect on SWARMOS (vs `swarmos`) | adopted? |
|---|---|---|
| backtrack fix (engine, all arms) | removed the dominant wedge on the traced seed | yes (defect fix) |
| mutual-hold break (ladder) | overlap: persistent deadlocks 257 -> 15; open floor: WORSE (DNF 8 -> 9) | not on its own |
| + separating-motion exemption (kernel) | overlap DNF 4 -> 0, makespan 1718 -> 619 s; open-floor DNF 8 -> 4 | see safety evidence below |
| one-way lanes on single-file segments | worse on both floors (overlap DNF 8/9) | no - rejected |
| observe-only lookahead | identical motion (same trace); adds prediction scoring | yes (explainability only) |

### Safety evidence for the separating-motion exemption

- Its first version collided in 5 of 6 configurations. That was before the
  backtrack fix, whose off-segment jog breaks the exemption's reasoning. The
  version measured here is the same rule after that fix.
- 18 benchmark runs: 0 collisions.
- `..._exemption_safety`: `rush_50` (50 robots), `narrow_aisle_deadlock`,
  `blocked_aisle` and `corridor_demo`, 9 seeds x 3000 ticks, 36 runs:
  0 collisions, 0 invariant failures.
- `..._comm_degradation`: 9 radio conditions x 5 seeds: 0 collisions.
- 9000-tick runs: see the long-run section below.

### Communication degradation (`..._comm_degradation`, rush_50, 16 robots, 1200 ticks, 5 seeds)

| condition | swarmos (fallback ON) collisions | swarmos without fallback collisions |
|---|---|---|
| normal | 0 | 0 |
| 10% loss | 0 | 0 |
| 30% loss | 0 | 2 |
| 100 ms latency | 0 | 0 |
| 500 ms latency | 0 | 3 |
| 3 s fleet-wide outage | 0 | 12 |
| 6 s fleet-wide outage | 0 | 15 |
| single-robot blackout | 0 | 4 |
| EAST zone partition | 0 | 1 |

Task completion stays in the same band across conditions (5-7 tasks per run
in this short window). The fleet degrades gracefully instead of failing.
Before this work the product shipped without the fallback: the right-hand
column was the real behaviour of the system.

### Predictive lookahead, scored (observe-only)

| floor | precision | recall | mean lead |
|---|---|---|---|
| open floor | 0.71 | 0.95 | 16.4 ticks (1.6 s) |
| single-file overlap floor | 0.18 | 0.90 | 17.6 ticks |

Precision is low on the single-file floor: many predicted head-on meetings
never reach the conflict band because the ladder holds one robot earlier. Per
the scoring rule, that counts as a false positive.

### Long-run safety (`..._long_run_safety`, 9 seeds; rush_50 at 50 robots for 9000 ticks, narrow_aisle_deadlock and blocked_aisle to their scenario end)

| scenario | arm | collisions | invariant FAIL runs | margin breaches (sum) | min sep (m) | tasks (mean) |
|---|---|---|---|---|---|---|
| rush_50 | swarmos | 0 | 0 | 88 | 0.724 | 24.2 |
| rush_50 | swarmos + both breakers | 0 | 0 | 259 | 0.722 | 38.3 |
| narrow_aisle_deadlock | swarmos | 0 | 0 | 5 | 0.730 | 5.6 |
| narrow_aisle_deadlock | swarmos + both breakers | 0 | 0 | 4 | 0.740 | 6.2 |
| blocked_aisle | swarmos | 0 | 0 | 21 | 0.722 | 8.8 |
| blocked_aisle | swarmos + both breakers | 0 | 0 | 31 | 0.727 | 10.6 |

**Decision on the breakers: kept behind their flags, OFF in the product.**

- Across 126 runs the separating-motion exemption produced no collision and no
  invariant failure, and it improves throughput.
- But it is a relaxation of the safety kernel's veto, and it measurably spends
  more of the safety margin: margin breaches on the dense floor rose from 88 to
  259, with minimum separation still >= 0.722 m.
- The project rule is not to weaken the kernel, so this is presented as an
  evaluated option with its evidence, not switched on silently.
- The mutual-hold break alone made the open floor worse, so it is not enabled
  on its own either.
- Enable both with `SwarmPolicy(mutual_hold_break=True,
  separating_exemption=True)`, or the `swarmos_mhb_sep` experiment arm.
