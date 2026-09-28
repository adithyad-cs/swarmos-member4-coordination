# SWARMOS - Live Demo Run Order

SIH26123 - Edge-AI Based Distributed Fleet Coordination for AMRs in Smart
Warehouses. Sponsor: Bharat Electronics Limited. Theme: Robotics & Drones.

Target length: **5 minutes of demo + 3 minutes of Q&A.** Every beat below has a
time budget, a single sentence to say, and an exact click. Do not improvise new
clicks - anything not in this list is a risk you have not rehearsed.

---

## 0. Before the judges arrive (T-10 min)

```
cd /home/fdipglob_ai_tools/nxp60742/acc_id_work/chin_20260920
./run.sh --demo
```

Then in the browser: `http://127.0.0.1:8770`

If demoing from a laptop over SSH, `run.sh` prints the exact tunnel line:

```
ssh -L 8770:127.0.0.1:8770 <host>
```

Pre-flight checklist - all five must be true before you present:

- [ ] Landing screen shows the AMR hero art and the wordmark glyph.
- [ ] Bottom strip reads `VERDICTS --` (a dash, never `NaN`).
- [ ] `./run.sh --test` has been run once today and printed 575 passed.
- [ ] Browser zoom is 100 pct, window is maximised, width >= 1400 px.
- [ ] Nothing else is bound to port 8770 (`./run.sh --check`).

Set the browser to full screen (F11). Close every other tab: a stray tab is the
single most common way a live demo looks unprofessional.

---

## 1. Beat 1 - the problem, on the landing screen (0:00 - 0:30)

**Do:** nothing. Leave the landing screen up.

**Say:** "A smart warehouse runs dozens of autonomous mobile robots in aisles
narrower than two robots. The hard part is not navigation, it is what happens
when two robots want the same square metre at the same moment, and the network
between them is unreliable. SWARMOS is the coordination layer that decides that,
on the edge, in under 100 milliseconds per tick."

Point at the dashed ring in the hero art: "that is the 15 metre radio horizon -
every robot decides using only what it can hear."

---

## 2. Beat 2 - start the run (0:30 - 1:15)

**Do:** click **Start demo run**.

**Say:** "rush_50 scenario, seed 11, fleet of 8. Ten ticks per second." As the
robots appear: "colour here means state and nothing else - amber is waiting,
red is blocked, blue is charging, teal is a sovereign agent."

Let it run. Point at the hero metric: "tasks per minute, top left, is the number
the warehouse operator actually cares about."

**If it does not start:** the Lab tab now reports the server's real reason in
plain English. Read it out loud - that is a feature, not a stumble.

---

## 3. Beat 3 - a conflict, resolved (1:15 - 2:00)

**Do:** click any robot that is amber or red to select it. Its trail appears.

**Say:** "That robot is yielding. It is not yielding because a central server
told it to - it is yielding because the safety arbiter on board decided the
other robot has the stronger claim, and that decision is binding. The machine
learning layer can advise, but it can never override this. That separation is
structural in the code, not a policy we promise to follow."

Point at VERDICTS in the bottom strip: "every one of those is an arbiter
decision, counted."

---

## 4. Beat 4 - inject a fault (2:00 - 3:00)

**Do:** Lab tab -> inject a fault on a robot that is mid-aisle.

**Say:** "A real fleet degrades. I am going to fail a robot in the middle of a
narrow aisle." Watch the fleet reroute. "Nobody stopped. The others detected the
silence within 200 milliseconds and replanned around a static obstacle."

Then, the strongest beat for a BEL panel:

**Do:** inject the rogue / adversarial fault.

**Say:** "Now a worse case: a robot that is not dead but is misbehaving -
ignoring the protocol. Defence customers care about this far more than about
throughput. SWARMOS contains it: the neighbours quarantine the offender and keep
working. That is our most novel contribution."

---

## 5. Beat 5 - the honest measurement (3:00 - 4:15)

**Do:** Compare tab (X-12, counterfactual co-simulation).

**Say:** "This is the same warehouse, same seed, same task list, run twice: once
with SWARMOS arbitration and once with a baseline. Identical up to the tick where
the two policies first disagree - and we show you that tick."

Then say: "What you are watching is one seed, an illustration. This live view
still runs the pre-v3 SWARMOS settings. The numbers I am about to quote come
from a frozen simulation benchmark, not from this screen."

Then use the lines of **Beat 5 (C2 v3 PRODUCT result)** in the addendum below,
quoted exactly, caveats included:

- +48.9 %, CI +35.3 to +62.5;
- 40/40 vs 21/40;
- +17.5 % common-finish;
- open floor slower when both finish.

(Superseded script, kept for the record: the earlier version of this beat
quoted "minus 19 percent, CI minus 36 to minus 3". That was the old
avg_completion_s statistic, before the fixed-batch protocol. Never quote it
as current.)

This beat wins more credit than a fake win would. Judges have seen dozens of
teams claim a round improvement number with n=1.

---

## 6. Beat 6 - determinism, the closing line (4:15 - 5:00)

**Do:** Analytics tab, point at the trace hash.

**Say:** "Every run emits a trace hash. Same scenario and same seed gives a
byte-identical hash, so any incident in this system can be replayed exactly.
For a safety-critical fleet that is the difference between a bug report and an
investigation. 672 automated tests, six modules, and the coordination decision
budget is 100 milliseconds a tick with measured headroom. Every one of the 240
C2 benchmark runs replays bit-exactly."

Stop talking. Invite questions.

---

## Recovery moves

| Symptom | Move |
| --- | --- |
| Page shows a degraded banner about frames | It is telling the truth; say "the UI reports staleness rather than freezing a stale picture" and press Start again. |
| Nothing renders | Reload the tab. Engine state is server side; the run survives. |
| Port busy | `./run.sh --check`, then `./run.sh --demo 8771`. |
| A judge asks for a scenario you have not rehearsed | Lab tab, `narrow_aisle_deadlock`, fleet 24. Say what you expect to see before you press Start. |

## What never to do on stage

- Do not claim SWARMOS is 20 percent faster in general. C2 is met on the
  overlapping-paths floor for the product default (+48.9 %, mostly
  reliability). Common-finish speed is +17.5 %, and the open floor is slower
  when both finish.
- Do not present the live Compare tab as the benchmark result.
- Do not call the ML layer a safety feature. It is advisory, by design.
- Do not resize the window mid-demo.
- Do not open a code editor. If asked, open the file they asked for and nothing else.

---

## Addendum (2026-09-26) - new beats, all backed by stored measurements

### Beat 3b - predicted conflict, explained (use `corridor_demo`)

1. In the Lab, pick scenario `corridor_demo` (6 robots, 12 tasks, single-file
   aisles), seed 11, then press Start.
2. Open the Inspector and click a robot heading into an aisle. Within the
   first minute a **Predicted conflicts** card appears. Read it aloud:
   - "Predicted head-on with R0xx in N ticks";
   - the risk band and its six terms;
   - "Decision: YIELD - yielding to R0xx, utility margin ...";
   - then the outcome.
3. Line: *"Every robot predicts from the paths its neighbours already broadcast
   within 15 m. No central planner, no extra messages. Every decision is
   recorded with why."*
4. The Analytics tab shows the **Safety invariants** block: verdict PASS,
   INV-1..4 at 0, minimum separation, margin breaches and lookahead
   precision/recall.
5. This is one seed, used as an illustration. The C2 numbers come only from
   the frozen multi-seed benchmark (`docs/C2_V3_PRODUCT_RESULT.md`).

### Beat 4b - pull the network, safety holds

- Inject `link_impair` with a 100% drop and a duration, which is a fleet-wide
  outage (API: `{"fault":"link_impair","drop_pct":100,"ticks":60}`), or
  `comm_blackout`.
- Line: *"Before this release, a 6-second outage caused 15 collisions in five
  runs. Robots now fall back to onboard sensing when they cannot hear a
  neighbour: zero, across nine radio conditions."* Source:
  `reports/experiments/*_comm_degradation`.

### Beat 5 - the honest measurement (C2 v3 PRODUCT result, 2026-09-27)

Supersedes the 2026-09-26 "C2 is not met / parity" beat. Source:
`docs/C2_V3_PRODUCT_RESULT.md`; say "simulation benchmark" every time.

- Line: *"Under a protocol frozen before the run, on 40 fresh seeds, SWARMOS as
  shipped beat textbook stop-and-wait on the overlapping-paths floor by +48.9 %,
  95 % CI +35.3 to +62.5. It finished 40 of 40 batches; stop-and-wait finished
  21. All five pre-registered conditions passed, and all 240 runs replay
  bit-exactly."*
- Line, immediately after, unprompted: *"Most of that is reliability. Where both
  finish, we are +17.5 % faster, CI +1.4 to +33.6, which is under 20 % on speed
  alone. On the open floor we finish 40 of 40 against 15, but when both finish
  we are slower."*
- Safety line: *"0 collisions and 0 invariant failures in 240 runs. The only
  margin breach, 0.748 m, came from the tuned stop-and-wait reference, not from
  SWARMOS."*
- The negative control collides hundreds of times, which proves the safety
  monitor is real.
- Offer the replay check:
  `tools/replay_check.py reports/experiments/20260927T130822Z_c2v3_frozen --all --require-identity --workers 4`.
- **Do not present the live Compare tab as the benchmark.** Its SWARMOS arm uses
  the pre-v3 settings (without F1/F3/F5/F6) and its ghost arm is tuned
  stop-and-wait without F1/F6. It is a one-seed illustration.
