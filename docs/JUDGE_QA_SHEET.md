# SWARMOS - Judge Q&A Sheet

SIH26123, sponsor Bharat Electronics Limited. Read this the night before, not on
stage. Answers are short on purpose: a 20-second answer that names a file is
stronger than a 90-second answer that names nothing.

Two rules that apply to every answer below:

1. **Never invent a number.** If you do not know it, say "I do not have that
   measured" and name the file where it would live. Every measured number in this
   sheet exists in the repository.
2. **Never oversell the ML.** It is advisory. Saying so is a design strength.

---

## CURRENT C2 RESULT: v3 product default (2026-09-27). Read this first.

Source: `docs/C2_V3_PRODUCT_RESULT.md`. Narrative: `docs/JUDGE_NARRATIVE_C2_V3.md`.
These are simulation benchmark results, not hardware results. Older C2 numbers
further down this sheet (-19.3 %, -5.5 % "parity", +2.0 %) are SUPERSEDED
history; do not quote them as current.

**Q. Did you meet the 20 % target (C2)?**
Yes, for the product-default configuration, under a frozen protocol. On the
overlapping-paths floor (`overlap_batch`), SWARMOS as shipped vs textbook
stop-and-wait + F1 + F6:

- time reduction **+48.9 %, 95 % CI [+35.3 %, +62.5 %]** over 40 fresh seeds;
- SWARMOS finished **40/40** batches, the reference **21/40**;
- no seed that SWARMOS failed while the reference finished;
- all five frozen decision conditions passed.

**Q. Is SWARMOS just faster?**
No, and we say so. On the 21 seeds where both finished, SWARMOS is **+17.5 %
faster, CI [+1.4 %, +33.6 %]**. That is below 20 % if you judge speed alone.
Most of the +48.9 % comes from SWARMOS finishing batches that stop-and-wait
never finishes (a failed run counts at the 3000 s cap).

**Q. And on an open floor?**
The capped improvement is +33.7 %, CI [+4.5 %, +62.8 %], and SWARMOS finishes
40/40 against the reference's 15/40. But when both finish, SWARMOS is
**slower**: mean -44.4 %, CI [-105.8 %, +17.1 %], faster on only 4 of 15 seeds.
The open-floor advantage is reliability, not speed.

**Q. What did you change to get there, and is it still safe?**
The product default is F1 + F3 + F5 + F6.

- F1: the path-aware safety check. It only forbids more motion, and it is
  given to the reference arms too.
- F3: the robot not closing keeps right of way.
- F5: the standoff breaker. It replans; it never grants extra motion.
- F6: a 300-tick release cooldown, given to the reference arms too.

F2(a)/(b) (relaxing the floor) are OFF. The 0.75 m floor is unchanged.

Across all 240 runs there were 0 collisions and 0 invariant failures, and
SWARMOS had 0 margin breaches and 0 frozen pairs. The only margin breach in the
whole benchmark (0.748 m, inside the margin, not a contact) came from the
**tuned reference arm** on the open floor.

**Q. How do we know you did not cherry-pick?**

- The protocol was frozen before the first run, with its sha256 recorded and
  byte-identical afterwards.
- The seeds (600001-600040) were fresh and fixed in advance.
- No run was excluded.
- 240/240 runs were replayed bit-exactly under the recorded code identity
  (`f3dabbf0...094f`).
- Two earlier protocols are kept as history, including the one that said
  NOT MET.

**Q. Is the live Compare tab the benchmark?**
No. It is a one-seed illustration. Its SWARMOS arm still uses the pre-v3
settings (without F1/F3/F5/F6), and its ghost arm is tuned stop-and-wait
without F1/F6. Quote C2 only from the frozen benchmark.

| Quantity (v3, simulation) | Value | Source |
| --- | --- | --- |
| Primary capped time reduction, overlap | +48.9 %, CI [+35.3, +62.5] | `docs/C2_V3_PRODUCT_RESULT.md` |
| Finish rate, overlap (SWARMOS / textbook / tuned) | 40/40 / 21/40 / 24/40 | same |
| Common-finish speed, overlap | +17.5 %, CI [+1.4, +33.6] | same |
| Open floor capped / common-finish | +33.7 % [+4.5, +62.8] / -44.4 % [-105.8, +17.1] | same |
| Finish rate, open floor (SWARMOS / textbook) | 40/40 / 15/40 | same |
| Collisions / invariant failures (240 runs) | 0 / 0 | same |
| SWARMOS margin breaches / frozen pairs | 0 / 0 | same |
| Replay | 240/240 exact | `reports/c2v3/replay_all.log` |
| Tests at freeze | pytest 672 passed; UI verifier 39/1 warn/0; backend 82/0; browser 26/0 | `reports/c2v3/prefreeze_*` |

---

## Tier 1 - almost certain to be asked

**Q. What is actually new here? Multi-robot path planning is a solved field.**

Path planning is solved; we use WHCA* and Contract Net, both standard, and we say
so. Three things are ours:

- **Adversarial robot containment** - not a failed robot, a robot that is alive
  and violating the protocol. The neighbours quarantine it and the fleet keeps
  working. We have not found this in the AMR literature and it is the part a
  defence customer cares about most.
- **Runtime assurance separation** - the ML advises, a deterministic arbiter
  decides, and the ML is structurally prevented from entering the safety path.
  This is Simplex architecture (Sha, 2001) applied to fleet coordination.
- **Deterministic replay** - every run emits a trace hash; same seed gives a
  byte-identical hash, so an incident can be replayed exactly.

**Q. Show me the improvement over a baseline.**

Open the Compare tab. Zero collisions across 27 paired 9000-tick runs - met. On
throughput we targeted plus 20 percent and measured **minus 19 percent, 95
percent CI [minus 36, minus 3]**. We did not hit it. We also know why, and the
reason is a measurement bug, not a hand-wave: the task supply is exhausted before
the run window closes, so the second half of the comparison is an empty
warehouse, and `avg_completion_s` is survivorship-biased - an arm that completes 3
tasks scores "faster" than one that completes 12. Re-scoring on `tasks_per_min`
with matched completion counts is our next work item. It is all written up in
`docs/SUCCESS_CRITERIA_VERIFICATION.md`.

**Q. So your system is slower. Why would anyone deploy it?**

Because the throughput number we currently report is not measuring throughput, it
is measuring an artefact, and we will not claim a win on a statistic we do not
trust. What we can defend today: zero collisions, a bounded 100 ms decision
budget with measured headroom, graceful degradation under robot failure, and
containment of a misbehaving robot. In a warehouse, one collision costs more than
a few percent of throughput.

**Q. Where is the AI? This looks like classical algorithms.**

There is a learned congestion forecaster that predicts where the warehouse will
jam and biases task assignment away from it. It is deliberately advisory: it can
change which task a robot takes, it can never change whether a robot is allowed
to move into an occupied cell. If you disable it, the fleet is slower but exactly
as safe. That is the property we wanted.

**Q. Is this centralised or distributed?**

Decisions are local: each robot uses only neighbours inside a 15 m radio horizon,
with 10 Hz heartbeats, 200 ms suspicion and 500 ms confirmation. The single
process you are looking at is the simulator hosting all of them, not a central
brain. The coordination code takes no global state it could not obtain over radio.

---

## Tier 2 - likely

**Q. Real robots or simulation only?**

Simulation only, and we will not pretend otherwise. The coordination layer takes
pose, battery and task state and returns a motion verdict - that interface is what
a ROS 2 node would supply. Porting means replacing the state source, not
rewriting the policy.

**Q. How many robots does it scale to?**

We demo fleet 8 because that is the fleet of the C2 benchmark floor
(`overlap_batch`; the open-floor benchmark uses 12). The scenarios go to 50
(`rush_50`). The cost driver is neighbours within 15 m, not fleet size, so the
per-robot cost is roughly constant as the warehouse grows with the fleet. What we
have not done is a scaling study to 500 - do not claim one.

**Q. Can it run on the robot? "Edge AI" is in the problem statement.**

The decision budget is 100 ms per tick and the Analytics tab shows the measured
p50/p95/p99 against it. It is integer and float arithmetic over a handful of
neighbours - no GPU. We have not measured it on an actual embedded target, so we
quote headroom on this machine, not a board.

**Q. What happens if the network partitions?**

Each side keeps coordinating within itself, because the protocol never needed the
other side. Robots that go silent are treated as static obstacles after
confirmation, which is the conservative choice - you route around them rather
than assuming they moved.

**Q. Deadlock - two robots facing each other in a one-wide aisle?**

Try it: `narrow_aisle_deadlock`, fleet 24, in the Lab tab. Detection uses the
Coffman conditions over the wait-for graph; resolution breaks the cycle by
revoking the weaker claim. The arbiter's decision is binding, so there is no
oscillation.

**Q. How do you know the simulator is not just agreeing with you?**

Three ways. The simulator is the single source of robot state and the coordination
layer cannot write to it - it can only return verdicts. Collisions are measured
geometrically at 0.70 m, independent of the policy. And the baseline arm runs in
the same simulator, so a simulator that flattered us would flatter the baseline
too - which is exactly what happened: the baseline also scored zero collisions.

---

## Tier 3 - harder, be honest

**Q. Your 575 tests - what do they actually prove?**

They pin behaviour, not correctness. They cover the arbiter's decision table, the
failure detector timings, the deadlock cycle breaker, the API contract and the
determinism of the trace hash. They do not constitute a safety case. A real
deployment needs hardware-in-the-loop and a hazard analysis, and we have neither.

**Q. Team of five - who wrote what?**

Six modules: frontend, backend, ML, coordination, simulation, database and
analytics, with frozen interfaces in `docs/INTEGRATION_CONTRACTS.md`. Answer for
the module you own and hand over for the rest; do not narrate someone else's code.

**Q. Why build your own simulator instead of using Gazebo?**

Determinism and speed. We need thousands of 9000-tick runs to make a statistical
claim, and we need the same seed to give a byte-identical trace. A physics
simulator gives neither cheaply. The trade-off is that we do not model wheel slip,
sensor noise or dynamics - so our numbers are about coordination, not control.

**Q. Biggest weakness?**

(Updated 2026-09-27.) No hardware: everything is simulation. Second, speed:
when both arms finish, SWARMOS is only +17.5 % faster on the overlap floor (CI
lower bound +1.4 %) and slower on the open floor. Our C2 margin comes mostly
from finishing batches the baseline does not. We would rather be asked about
those than have them found.

---

## Numbers you may quote (all measured, all in the repo)

| Quantity | Value | Where |
| --- | --- | --- |
| Collisions, 27 paired 9000-tick runs | 0 | `docs/SUCCESS_CRITERIA_VERIFICATION.md` |
| Throughput vs baseline (SUPERSEDED v0 statistic; current: see top of sheet) | -19.3 pct, CI [-36.0, -2.6] | same |
| Decision budget | 100 ms per tick, 10 Hz | `app/sim/clock.py` |
| Radio horizon | 15 m | `app/coordination/swarm_policy.py` |
| Failure detection | 200 ms suspicion, 500 ms confirmation | same |
| Collision threshold | 0.70 m centre to centre | `app/sim/engine.py` |
| Hard stop distance | 0.75 m | `app/coordination/swarm_policy.py` |
| Automated tests | 672 passing at the v3 freeze (575 when this table was first written) | `./run.sh --test`, `reports/c2v3/prefreeze_pytest.log` |
| Largest scenario | 50 robots (`rush_50`) | `app/sim/scenarios.py` |

## Three sentences never to say

- "SWARMOS is 20 percent faster everywhere." (It is not. The +48.9 % C2 result is on
  the overlapping-paths floor and is mostly reliability; common-finish speed is
  +17.5 %, and on the open floor SWARMOS is slower when both finish.)
- "The AI decides when robots should stop." (It never does. The arbiter does.)
- "It is production ready." (It is a simulator with no hardware validation.)

---

## 2026-09-26 additions (all measured; directories under `reports/experiments/`)

**Q. How do you know "zero collisions" is not just a lucky run?**
Four machine-checked invariants run every tick on TRUE positions: contact,
step authority, no motion while held/failed/contained, and legal status
transitions. The same monitor on a no-coordination control FAILS every run
with hundreds of contacts, naming the pair and tick. We also report minimum
separation and margin breaches at the 0.75 m floor, not just a count.

**Q. What happens when the network fails?**
We measured it. Before this release, the kernel only saw robots it could hear,
and a 6 s outage produced 15 collisions in 5 runs. Now a robot that is sensed
but not heard is treated as an obstacle. Result: 0 collisions across 9 radio
conditions (loss, latency, outage, blackout, partition), with the fleet still
completing work.

**Q. Where is the intelligence / what is predictive?**
Each robot predicts conflicts ~1.7 s ahead from the paths its neighbours
already broadcast. Recall is 0.90-0.95. Precision is 0.71 on the open floor
and 0.18 in single-file aisles, and we say why (holds resolve predicted
meetings early). Every high-risk prediction is logged with a six-term risk
score, the decision taken and the outcome.

**Q. Did you meet the 20% target?** (SUPERSEDED 2026-09-27; see the v3 answer
at the top of this sheet.)
As of 2026-09-26: no. On a fixed batch with overlapping paths, measured as
makespan against textbook stop-and-wait over 9 paired seeds, our best variant
was at parity (-5.5%, CI [-42, +31]) and behind on the open floor. We publish the
directory and the replay command. We also found and fixed two real defects on
the way: a motion jog outside the kernel's verified envelope, and a
network-dependent safety gap.

**Q. Why not a GNN or RL planner like the papers?**
The GNN paper's own robots collide (success down to 69.7%), and the safe-RL
paper holds safety only in expectation after 8 GPU hours per team size. We
keep learning out of the safety path and verify the path that matters.

### Numbers you may quote (2026-09-26)

| Quantity | Value | Source |
| --- | --- | --- |
| Collisions, SWARMOS, every experiment run | 0 | all `reports/experiments/*` |
| Collisions, no-coordination control | 316 / 639 (overlap / open floor, 9 runs each) | `*_c2_benchmark` |
| Outage collisions without / with perception fallback | 15 -> 0 (6 s outage, 5 runs) | `*_comm_degradation` |
| C2 best variant vs stop-and-wait, overlap floor (SUPERSEDED by v3) | -5.5 pct, CI [-42.3, +31.2] | `*_deadlock_breakers` |
| Lookahead recall / median lead | 0.90-0.95 / ~17 ticks | same |
| Automated tests | see README | `./run.sh --test` |
