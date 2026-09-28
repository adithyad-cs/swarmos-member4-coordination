# SWARMOS: judge narrative (C2 v3 PRODUCT result)

Every number on this page is a SIMULATION BENCHMARK result, copied from
`docs/C2_V3_PRODUCT_RESULT.md`. The frozen protocol is
`docs/C2_FROZEN_PROTOCOL_V3.md`; the raw data is
`reports/experiments/20260927T130822Z_c2v3_frozen/` and the records are in
`reports/c2v3/`. Nothing here is a physical-world or certification claim.

## 1. The problem

A warehouse fleet of autonomous mobile robots shares narrow aisles. The
classical controller, stop-and-wait, is safe but conservative. Two robots that
meet head-on in a single-file aisle both stop, time out, and replan, often
into the same conflict again. Batches of work stall or never finish.

## 2. Why decentralised coordination

- Each SWARMOS robot decides from its own 15 m radio inbox and onboard
  sensing. No central planner is on the critical path, so there is no single
  point of failure.
- The fleet keeps working if one robot fails or the network degrades.
- A binding safety kernel (0.75 m floor) checks every motion, whatever the
  negotiation decided.

## 3. What the product fixes contribute (high level)

**The product default is F1 + F3 + F5 + F6.** F2(a) and F2(b) are OFF. The
safety floor stays 0.75 m.

| Fix | What it does | Why it is safe | Where |
|---|---|---|---|
| F1 path-aware safety check | The kernel checks the real path a robot drives around a corner, not only the straight line. | It can only forbid more motion, never less. | All arms, reference included |
| F3 leader keeps right of way | A robot that is not closing on its neighbour does not stop for it. | The negotiation layer only; the kernel still checks every step. | SWARMOS only |
| F5 standoff breaker | After 2 s of mutual hold, a deterministic choice makes one robot replan around the other. | It turns a hold into hold-and-replan; it never grants extra motion. | SWARMOS only |
| F6 release cooldown | A stalled task is not handed straight back to the same stuck robot, for 300 ticks (30 s). | Dispatch only. | All arms, reference included |

The fixes came from a traced root-cause analysis of the failed v1 benchmark
(`docs/C2_ROOT_CAUSE_ANALYSIS.md`). They were developed on separate
development seeds (`docs/IMPROVEMENT_CYCLE_20260927.md`).

## 4. What was measured

- **Criterion:** SIH26123 C2, at least 20 % less total task-completion time
  than traditional stop-and-wait on overlapping paths, with no loss of safety.
- **Primary scenario:** `overlap_batch`. Single-file aisles, 8 robots, a fixed
  batch of 24 tasks. Makespan is the time the last task finishes; the cap is
  3000 s, and a run that hits it is "did not finish" (DNF).
- **Secondary scenario:** `open_floor_batch`. Two-way aisles, 12 robots, 36
  tasks.
- **Arms:**
  - SWARMOS **product** (`swarmos`, exactly as the software ships);
  - textbook stop-and-wait + F1 + F6 (the **reference**);
  - tuned stop-and-wait + F1 + F6.
- **Statistic:** paired by seed, Student-t 95 % CI on the per-seed percentage
  reduction.

## 5. Why frozen protocols and fresh seeds

- **Frozen before running.** The protocol fixed all of the following before
  the first run:
  - the code identity (`f3dabbf0d732bfc218a1ab31f906299ca1baee5c4b1de148534b16c0d023094f`);
  - every flag and threshold;
  - the seeds, 600001-600040;
  - the decision rule;
  - the exact command.

  Its sha256 was recorded, and it was byte-identical after the benchmark.
- **Fresh seeds.** The seeds had never been used in development or in any
  earlier evaluation, so nothing was tuned on them.
- **No seed changes, no exclusions.** No seed was chosen, dropped, replaced or
  reordered, and every one of the 240 runs is reported. The design is
  3 arms x 2 scenarios x 40 seeds.
- **Replay.** Every run was replayed: 240/240 were bit-exact, with the code
  identity and every arm's configuration checked.
- **Earlier protocols are not reused.** v1 (C2 NOT MET) and v2 (evaluated arm
  only) are kept as history.

## 6. How safety and fairness were enforced

- **Safety was measured, not assumed.** Invariants are checked on TRUE
  positions every tick: contact < 0.70 m, step authority, no motion while
  held, and legal status transitions. A no-coordination control fails this
  monitor with hundreds of contacts, which proves it can fail.
- **Same floor for every arm.** All arms use the same 0.75 m floor and the
  same F1 path geometry.
- **F1 and F6 are shared.** The reference arms receive F1 and F6 too.
- **SWARMOS gets no safety relaxation.** F2(a) and F2(b) are OFF.
- **Remaining asymmetries favour the reference.** Stop-and-wait keeps its own
  rule for separating inside the margin, and it sees every robot's true
  position. SWARMOS sees only its radio inbox and sensors.
- **Identical workload.** Every arm gets the same workload for the same seed.

## 7. What the results demonstrate

**Primary C2 (`overlap_batch`, SWARMOS product vs textbook stop-and-wait + F1 + F6):**

| | Result |
|---|---|
| Capped time reduction | **+48.9 %, 95 % CI [+35.3 %, +62.5 %]** (n = 40) |
| Finish rate | **SWARMOS 40/40, reference 21/40** (tuned stop-and-wait 24/40) |
| Seeds SWARMOS failed while the reference finished | **none** |
| Frozen decision conditions | **all five passed**: CI lower bound >= +20 %; no seed failed only by SWARMOS; 0 collisions and 0 invariant failures; replay 240/240; no violation or substitution |

**C2 is MET for the product-default configuration under the frozen v3 rule.**

**Safety (all 240 runs):**

- 0 collisions and 0 invariant failures.
- SWARMOS: 0 margin breaches and 0 frozen pairs.
- **The only margin breach in the entire benchmark came from the tuned
  REFERENCE arm** (stop-and-wait + F1 + F6, STUCK_TICKS 8) on
  `open_floor_batch`, at 0.748 m. That is inside the 0.75 m margin but
  outside the 0.70 m contact threshold; it is not a collision.

## 8. Limitations and caveats (say these before you are asked)

- **The speed-only gain is smaller.** On the 21 overlap seeds where BOTH arms
  finished, SWARMOS is **+17.5 % faster, 95 % CI [+1.4 %, +33.6 %]**.
  - That is below a 20 % threshold if speed alone is considered.
  - The larger primary gain (+48.9 %) is substantially driven by SWARMOS
    completing batches the reference does not. The reference failed 19 of
    40 seeds that SWARMOS finished; a failed run is counted at the 3000 s cap.
- **Open floor (secondary): SWARMOS is slower when both finish.**
  - Capped improvement **+33.7 %, 95 % CI [+4.5 %, +62.8 %]**.
  - Finish rate **SWARMOS 40/40, reference 15/40**.
  - On the 15 seeds both arms finished, SWARMOS is **slower**: mean -44.4 %,
    95 % CI [-105.8 %, +17.1 %], faster on only 4 of 15.
  - SWARMOS is not universally faster. Its advantage there is reliability.
- **The tuned baseline is ahead on one metric.** It has fewer persistent
  deadlocks than SWARMOS (overlap 0.6 vs 3.5; open floor 16.3 vs 20.5), but it
  fails many more batches.
- **This is simulation, not certification.** Two synthetic floors, no
  hardware, no physical-world certification.
- **The live Compare tab is an illustration, not the benchmark.** The
  dashboard's co-simulation builds its SWARMOS arm with the pre-v3 settings
  (`app/sim/cosim.make_treatment_policy`, without F1/F3/F5/F6). Its ghost arm
  is tuned stop-and-wait without F1/F6. Quote C2 numbers only from the frozen
  benchmark. The Lab run and the API use the product policy.

## 9. Evidence checklist

| Item | Value |
|---|---|
| Runs | 240 = 3 arms x 2 scenarios x 40 seeds |
| Seeds | 600001-600040, fresh, fixed before the run |
| Protocol | `docs/C2_FROZEN_PROTOCOL_V3.md`; byte-identical after the run (`reports/c2v3/protocol_freeze_record.txt`) |
| Replay | 240/240 exact, code identity and arm configs MATCH (`reports/c2v3/replay_all.log`) |
| Code identity | `f3dabbf0d732bfc218a1ab31f906299ca1baee5c4b1de148534b16c0d023094f` |
| pytest (pre-freeze) | 672 passed |
| UI verifier | 39 pass, 1 known warning, 0 fail |
| Backend audit | 82 pass, 0 fail |
| Browser audit | 26 pass, 0 fail |
| Version control | nothing committed or pushed; HEAD remains `a6e1804` |

Reproduce:

```
PYTHONPATH=. python3 tools/replay_check.py \
    reports/experiments/20260927T130822Z_c2v3_frozen \
    --all --require-identity --workers 4
```
