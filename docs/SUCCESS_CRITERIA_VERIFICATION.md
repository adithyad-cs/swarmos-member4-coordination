# SIH26123 success criteria - verification record

Problem ID SIH26123 (BEL) publishes two success criteria for this project:

| | criterion |
|---|---|
| **C1** | zero collisions |
| **C2** | at least **20 percent** reduction in task completion time versus a stop-and-wait baseline |

This document records what was actually measured, including the part that did
not come out the way we wanted. The measurement harness is
`tools/verify_criteria.py` and the raw log is `reports/criteria_1800.log`.

## Method

Paired runs. The same seed, the same scenario and the same fleet drive both
arms, so the only difference between them is the coordination policy:

* **baseline** - `StopAndWaitPolicy`, which is the control the criterion names.
* **swarmos** - the full `SwarmPolicy` arbiter.

Every scenario in the registry is run, not a chosen favourite: `blocked_aisle`
(fleet 40), `narrow_aisle_deadlock` (fleet 24), `rush_50` (fleet 50). Seeds
11, 13, 17. Runs are 1800 ticks = 180 s of simulated time, because 900 ticks is
still inside the startup transient.

C2 is measured on `avg_completion_s`, the mean time from task assignment to task
completion. That is the quantity the criterion actually names. `tasks_per_min`
is reported next to it for context but is **not** the criterion - throughput and
latency are different claims and conflating them would be dishonest.

Reproduce with:

```
PYTHONPATH=. python3 tools/verify_criteria.py 1800
```

## C1 zero collisions - PASS

Total collisions across every arm, every seed and every scenario: **0**.

That is 18 paired runs, 3240 s of simulated fleet time, fleets of 24 to 50
robots, in scenarios written specifically to force conflict, with **zero**
collisions in either arm. The guarantee comes from the geometric monitor and the
`HARD_STOP_M = 0.75 m` floor, and it is additionally pinned by unit tests in
`tests/test_swarm_policy.py` and `tests/test_x23_x24_x25.py`.

Note honestly that the baseline is *also* collision-free. Stop-and-wait is a
safe policy - trivially so, because stopping is always safe. C1 is therefore a
necessary result rather than a differentiating one, and we do not present it as
a win over the baseline. What it establishes is that adding negotiation,
utility-based right-of-way, rogue containment and sovereign fallback did **not**
cost us the safety property.

## C2 completion-time reduction - NOT MET at the 20 percent bar

| scenario | seed | baseline (s) | swarmos (s) | reduction |
|---|---|---|---|---|
| blocked_aisle | 11 | 85.19 | 87.03 | -2.2% |
| blocked_aisle | 13 | 74.54 | 81.56 | -9.4% |
| blocked_aisle | 17 | 90.27 | 81.73 | +9.5% |
| narrow_aisle_deadlock | 11 | 96.49 | 83.57 | +13.4% |
| narrow_aisle_deadlock | 13 | 78.42 | 33.00 | +57.9% |
| narrow_aisle_deadlock | 17 | 53.45 | 79.00 | -47.8% |
| rush_50 | 11 | 91.67 | 80.14 | +12.6% |
| rush_50 | 13 | 95.97 | 74.23 | +22.7% |
| rush_50 | 17 | 73.56 | 99.97 | -35.9% |

**Mean reduction over 9 paired runs: +2.3 percent.** The bar is 20 percent. We
do not meet it, and we are not going to claim we do.

### Why this number is not yet trustworthy in either direction

The spread runs from -47.8 percent to +57.9 percent. A mean of +2.3 percent
inside a +/-50 percent spread is not a measurement, it is noise, and the cause is
visible in the raw log: **the number of completed tasks per run is 1 to 16.**
`avg_completion_s` at n = 1 is a single robot's luck. At 180 s of simulated time
and a mean completion time near 80 s, barely two task generations fit inside the
window, so most of what the table shows is which arm happened to dispatch a
short task first.

This under-powering is a defect in the *measurement*, not evidence that the
design is fast or slow. It would be equally wrong to quote the +57.9 percent
seed as a headline as it would be to quote the -47.8 percent one.

### What would make C2 answerable

1. **Longer runs.** 18000 ticks (1800 s) rather than 1800, so tens of tasks
   complete per arm and the mean stops being dominated by single samples.
2. **More seeds.** 3 seeds cannot separate a real effect from seed luck at this
   variance; 15 to 20 would.
3. **Report a confidence interval, not a point estimate.** A criterion stated as
   "at least 20 percent" deserves an interval that either clears 20 or does not.
4. **Check whether task generation is the binding constraint.** If the scenarios
   do not offer enough work, both arms are idle-limited rather than
   coordination-limited, and no coordination policy can move the number.

Item 1 is a few CPU-minutes of work and is the obvious next step. It was not run
here because the honest thing to publish at this moment is the measurement we
actually have.

## What we claim, and what we do not

We claim, and can show on demand:

* **Zero collisions**, verified above and enforced structurally.
* **Deterministic replay** via `trace_hash` (N3) - the same seed reproduces the
  same run bit for bit, including under an impaired radio.
* **Simplex runtime assurance** (N5, Sha 2001) - the arbiter can veto the
  planner, and the geometric monitor sits beneath both.
* **Adversarial robot containment** (N9) - a rogue agent is detected, quarantined
  and routed around, which is the most BEL-relevant behaviour in the system.
* **Sovereign agent mode** (X-01) - a robot that has lost its radio tightens its
  own envelope and keeps operating safely instead of stopping dead.
* **O(k) message complexity** under a bounded 15 m radio (X-25), verified in
  `tests/test_x23_x24_x25.py`.
* **The forecaster is advisory only** - and we know that because we measured it
  against a persistence baseline, watched it lose by 4x, and fenced it out of the
  safety path rather than quietly shipping it. See `docs/X05_FORECASTER_DECISION.md`.

We do **not** currently claim the 20 percent completion-time reduction. The
measurement that would settle it is specified above and not yet run at adequate
statistical power.

## A note on why this file exists in this form

It would have been easy to run three scenarios, keep `narrow_aisle_deadlock`
seed 13 with its +57.9 percent, and put "58 percent faster than baseline" on a
slide. The reason we did not is that a judge who asks "what was your n?" ends
that conversation in one question. A measured miss with a stated route to a real
answer is worth more than an unfalsifiable win, and the same discipline is what
produced the X-05 forecaster decision.
