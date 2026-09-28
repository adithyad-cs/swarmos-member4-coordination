# Why SWARMOS fails C2: root-cause analysis (2026-09-27)

Diagnosis only. No code, protocol or frozen result was changed; the code
identity is still `ba4086a6...9656`. All evidence is from:

- the frozen experiment: `reports/experiments/20260927T045112Z_c2_frozen/runs.jsonl`;
- read-only traces of its runs, with scripts and raw output in
  `reports/diagnosis_20260927/`:
  - `classify.py`: first floor entry of every pair, plus the terminal state of
    each robot still holding a task;
  - `t1.py` to `t4.py`: per-tick traces;
  - `classified.jsonl`: 75 runs.

## A. Root causes, ranked by measured impact

| # | Cause | Where | Measured impact |
|---|---|---|---|
| RC1 | **At-floor freeze with no escape.** Once a pair is inside 0.75 m, even by 1 mm, the SWARMOS kernel vetoes every motion of both robots, including motion AWAY from each other. The stop-and-wait arms carry an escape that lets such a pair open the gap; SWARMOS does not, so the at-floor rule is NOT identical between arms. | `swarm_policy._monitor` (no opening exemption; KNOWN LIMITATION note) vs `policy.StopAndWaitPolicy.arbitrate` lines 284-290 | A task-holder ends frozen inside the floor in **15/20** overlap DNFs and **8/8** traced open-floor DNFs. |
| RC2 | **Floor entry: the kernel's swept chord does not cover the real trajectory at a turn.** The kernel tests the straight line `here -> _step_envelope(project_step(0.22 m along path))`. When the path turns within that 0.22 m, the robot drives the L-shaped path (to the corner, then along) while the chord cuts diagonally. The chord clears the floor and the real motion does not. The breach is a few mm. | `swarm_policy._monitor` `swept()`; `_step_envelope`; robot motion `SimRobot.step` (straight chase of `path[0]`) | 45/45 floor entries in the traced SWARMOS runs. Frozen results: SWARMOS overlap runs with at least one margin breach finished only 10/26, against 10/14 with none. Open floor: 40/40 SWARMOS runs breached; mhb runs with 0 breaches finished 5/5. |
| RC3 | **The contest creates the breach geometry.** The loser YIELDs at 0.76-0.97 m and stands still; the winner PROCEEDs at full speed, or SLOW as clamped by the kernel, past it, usually toward a turn. `following` is heading-based, so at a turn it flips to "not following", and the robot in FRONT can lose the contest to the one behind it. | `swarm_policy._decide` / `_contest`; `_worst_encounter` (`following = dot >= FOLLOW_COS`) | Every one of the 45 traced floor entries is "one robot moves past a stationary YIELDing peer" (24 PROCEED, 21 SLOW). |
| RC4 | **Near-floor standoff (0.76-0.79 m) at merges and head-on.** Each robot's next step would breach the floor against the other's standing point. The contest winner is vetoed by the kernel, the roles swap every `COMMIT_TICKS`, and neither robot ever moves. | `_contest` with `COMMIT_TICKS`; `_monitor` | 5/20 overlap DNFs (seeds 900006, 900014, 900015, 900029, 900036). |
| RC5 | **Recovery cannot break RC1 or RC4.** Three mechanisms fire and none changes the geometry: MONITOR_STUCK REROUTE every 4 ticks, `_plan` falling back to the same route when the avoid-hint is infeasible, and stall release, which re-dispatches the task to the SAME nearest robot on the next tick. | `_monitor` MONITOR_STUCK_TICKS; `engine._plan` hint fallback; `engine._check_stalls` + `_dispatch` | 900018: 88 stall/release/assign cycles on the same pair. Frozen means (overlap): replans 16,203 SWARMOS vs 1,300 stop-and-wait; stall releases 158 vs 22. |
| RC6 | **Open-floor cascade.** One frozen pair blocks a two-way aisle, and the robots behind it YIELD or are held. | RC1 plus the ladder | Traced open-floor DNFs: 59 task-holders stuck across 8 runs (about 7 of 12 robots each). Frozen open floor: persistent deadlocks 501 (SWARMOS) vs 36 (tuned baseline). |
| RC7 | **Dispatch into a wedge / idle robots in the way.** Idle, parking-bound robots take part in floor entries. The dispatcher assigns work to robots that are frozen, because nearest wins. | `engine._dispatch` (nearest), `_choose_parking` | 6/15 final overlap floor episodes began with an idle robot in the pair (5 idle/idle, 1 idle/task); 7/39 terminal task-holders were blocked by an idle robot. |

Not root causes (checked, rejected):

- **Two robots sent to the same pick cell:** only 2/20 overlap DNFs (`goals.jsonl`).
- **Lookahead:** it is observe-only, so predictions never change motion. It
  predicts about 90% of conflicts about 17 ticks ahead (recall 0.90, precision
  0.42-0.58) and that information is unused.
- **Communications:** 0 comm-induced holds in the healthy-radio benchmark.

Why the stop-and-wait arms fail differently: 0 margin breaches in all 160 of
their runs. Their failed runs end with task-holders MOVING and no peer in the
way (39/53 textbook, 53/55 tuned), which is lockstep reroute livelock. They
also have the separating escape, so they never freeze.

Why open_floor_batch is worse:

- More robots (12) and two-way aisles means more contests with the loser
  standing next to the winner's path. Every SWARMOS run breached.
- One frozen pair then blocks a shared aisle and cascades (RC6).

Why runs hit the 3000 s cap: the batch is almost done. The overlap DNFs stop
at 20-23 of 24 tasks, and the mean time from last completion to the cap is
2,329 s. After the freeze, nothing can undo it (RC5).

Over-conservative? Locally safe but globally poor? Yes, in one specific
place. A 1 mm breach becomes a permanent freeze, and three recovery layers
keep re-trying the same thing. The floor itself is not the problem. The kernel
is both slightly UNSOUND (RC2: it lets the pair in) and has no sound way out
(RC1).

## B. Evidence index

| Cause | Evidence |
|---|---|
| RC1 | `t1.py overlap_batch swarmos 900018`: R005 and R008 at 0.735 m from tick 2800 to the cap. R005 wants to move west, AWAY from R008, and is vetoed by "swept path comes within 0.74 m". `analyse.py`: 15/20 and 8/8. |
| RC2 | `t3.py ... 900018 2799 R005 R008`: planned chord gap 0.756, actual 0.735, the path turning at (30.5, 27.5). `t3.py ... 900012 2157 R003 R006`: planned 0.755, actual 0.749, turning at (38.5, 3.5). `runs.jsonl` breach-vs-DNF split (table above). |
| RC3 | `classified.jsonl` onsets: 45/45 have one mover and one stationary YIELD. 900018 tick 2798: R008 (in front) yields to R005 (behind). |
| RC4 | `t4.py ... 900029 9000 9160 R001 R002`: 0.78 m, alternating YIELD/WAIT every 8 ticks, same route after every release. |
| RC5 | 900018 events: `task_stalled` then `task_released` then `task_assigned` to the same robot, 88 times. `runs.jsonl` replans / reroutes / stall means. |
| RC6 | `analyse.py` open-floor block; frozen `summary.md` persistent deadlocks. |
| RC7 | `analyse.py` pair composition and "blocked by an idle robot" counts. |

## C. Safe fix candidates

Every candidate keeps the binding kernel and adds constraints, or changes
only the advisory ladder, dispatch or recovery. Each can be tested alone and
must be measured on NEW development seeds.

| Fix | For | What | Safety argument | Fairness |
|---|---|---|---|---|
| F1 **Polyline sweep** | RC2 | The kernel (and the baseline's check, which has the same chord) tests the polyline `here -> each waypoint within the step -> endpoint` instead of one chord. Keep the `_step_envelope` extension on the last leg. | Strictly MORE constraining: the polyline covers the robot's real trajectory, so it can only veto more. | Apply the shared geometry fix to BOTH arms. It is a correctness fix of the common safety rule. |
| F2 **Identical at-floor rule** | RC1 | The two arms must have the same rule inside the floor. Two options, and this is **your decision**: (a) give SWARMOS the baseline's existing rule, then re-audit with F1 in place. This relaxes the SWARMOS kernel to match the baseline, which you have said not to do without evidence. (b) Keep the SWARMOS kernel and REMOVE the rule from the baseline, which may handicap the baseline. | (a) was measured to collide BEFORE the polyline and backtrack fixes; with F1 it is unmeasured and must be proven. (b) is safe. | Either makes the rule identical, which the protocol claimed but the code did not do. |
| F3 **Leader keeps right of way** | RC3 | In the ladder, a robot whose step does not reduce its distance to the peer (it is ahead, or moving away) never yields to that peer. Classify "following" by relative position, not heading alone. | Ladder only; the kernel still vets every step. | SWARMOS-only, legitimately: it is SWARMOS's own coordination logic. |
| F4 **Corner-aware approach** | RC2 + RC3 | A contest winner passing within CONFLICT_M of a stationary loser gets SLOW until its path is straight, so the swept step stays short near a turn. | Only reduces motion. | SWARMOS-only (ladder). |
| F5 **Standoff breaker** | RC4 | On a mutual veto (both robots held against each other for N ticks), the deterministic loser (lower utility, id tie-break) replans with the peer's current cell AND the next cells of the peer's intent forbidden, and an ascending cost for passing the peer, so it retreats or detours. | Planning only; every motion still passes the kernel. | SWARMOS-only (recovery). |
| F6 **Recovery that changes something** | RC5 | Stall release excludes the released robot from re-taking that task for K ticks; REROUTE is suppressed when the new route equals the old one. | Dispatch and planning only. | Engine-level, so it applies to all arms. It also helps the baselines' livelock, and should be reported as such. |
| F7 **Park out of the way / no dispatch into a freeze** | RC7 | Idle robots yield to task-holders (task term already in the utility); the dispatcher skips robots held for more than N ticks. | No motion change. | Engine-level, all arms. |
| F8 **Lookahead-informed hold** (later) | RC3 | Use the existing predictions (17-tick lead) to hold the predicted loser early, at the entry of a single-file segment, before it reaches the contest band. | Adds holds only. | SWARMOS-only. |

## D. Experiment plan (smallest set)

Dev seeds: a new, pre-declared block (for example 700001-700020) that is
disjoint from the evaluation seeds and from everything used so far. Scenarios
`overlap_batch` and `open_floor_batch`. Arms: `stop_and_wait`, `baseline`,
`swarmos`, and one variant per fix. Metrics are the frozen-protocol set plus
margin breaches, floor entries, and turn-induced entries.

| Step | Experiment | Pass condition to keep the fix |
|---|---|---|
| 1 | **F1 alone** (all arms, shared geometry) | Margin breaches drop toward 0 in SWARMOS; 0 collisions; 0 invariant failures; baseline makespan not worse by more than noise |
| 2 | **F1 + F3** | Floor entries per run fall further; finish rate up; no rise in YIELD count |
| 3 | **F1 + F3 + F5** | Overlap standoff DNFs disappear; persistent deadlocks fall |
| 4 | **+ F6** (all arms) | Replans and stall releases fall; report its effect on the baselines too |
| 5 | **F2 decision** (only if RC1 still causes DNFs after steps 1-4) | Your choice of (a) or (b); if (a), 0 collisions over at least 40 dev runs per scenario, with min separation reported |
| 6 | Unit and regression gate | pytest, UI verifier, audits; margin breach and floor entry counted in `runs.jsonl` |

Each step is one `run_experiment` call on the dev seeds. Keep a fix only if it
improves completion time or finish rate AND keeps 0 collisions and 0
invariant failures. Only after the set is fixed: a NEW frozen protocol with
new evaluation seeds, not 900001-900040.

## E. Demo impact

1. **F1 + F3 + F5** remove the most visible failure in a live demo: two robots
   standing still next to each other forever in an aisle. That is exactly the
   end state of 15/20 overlap and 8/8 open-floor failures.
2. **F6** removes the "stall, release, reassign" loop. On screen that loop is a
   robot that flickers between WAITING and assigned and never moves.
3. The **Decision Inspector already explains** each step of this failure (the
   contest margin, the veto reason). After the fix, the same panel can show
   "held at the turn to keep the 0.75 m floor". That is a strong,
   honest safety story.
4. **Lookahead (F8)** turns an unused prediction into visible, early,
   explained decisions, which is the demo's "predict, then act" beat.
5. **Recommended demo scenario:** `corridor_demo` in the Compare tab, after
   re-validation on dev seeds. Do not show `open_floor_batch` until RC1 and
   RC6 are fixed.
