# SWARMOS - research positioning (SIH26123)

How SWARMOS relates to five recent papers, what gap each leaves open, and what
SWARMOS actually implements and measures about it. Every "built" row points to
code and a test; every number points to an experiment directory under
`reports/experiments/` (see `docs/SUCCESS_CRITERIA_VERIFICATION.md`). Nothing
here claims that a primitive (A*, reservations, auctions, one-way lanes,
decentralized messaging) is new; the claim is the integration and its measured
behaviour under congestion, failure and degraded communication.

Novelty classes used below: **E** established technique, **R**
research-inspired adaptation, **I** differentiated system integration.

## The five papers

| # | Paper | What it does | Gap / limitation relevant to SIH26123 |
|---|---|---|---|
| 1 | Maoudj et al., *Lifelong MAPF for Shipment Preparation in Stochastic Warehouses*, IEEE CASE 2024 | Zone-prioritised task assignment (ZP-TA) + decentralized IDCMAPF motion with local give-way rules; stochastic pick/drop durations; makespan on a fixed batch of 500 tasks | Zone rule counts active tasks only (no timing, no dock queue); assignment is centralized; grid world, no continuous kinematics, no comms impairment, no safety monitor |
| 2 | Tan et al., *CREST: Constraint-Release Execution for Warehouse Shelf Rearrangement*, IEEE RA-L 2026 | Temporal-plan-graph execution with proactive constraint release; Property 2: any order respecting the precedence arcs is collision-free under delays | Offline, full information, centralized; online task arrival is listed as future work |
| 3 | Ali & Abdelmoneem, *Decentralized Path Planning Using GNNs on HBE-Robocar*, ICICIS 2025 | CNN -> GNN -> MLP imitation policy, local message passing, 2-robot hardware demo | Learned policy **collides**: success 69.7-98.9%, up to 410 conflicts per 1000 cases; no packet-loss study; fixed team size; no task allocation |
| 4 | Zeng et al., *Decentralized Auction-Based Task Allocation under Time Windows* (APTA), IEEE ICUS 2025 | CBBA-style bundle bidding on marginal insertion cost, consensus for conflict-free ownership; ~9.3% less travel than greedy | Perfect comms, homogeneous robots, free-space travel times (no congestion), static task set, no robot failure |
| 5 | Mu et al., *Reliable Task Allocation Using Safe Deep RL*, IEEE T-Reliability 2026 | Allocation as a Constrained MDP, Lagrangian safety multiplier, GAT encoder; reports Safety Violation Rate and min-separation distribution | Offline welding cells, 8 h GPU training, retrain per team size; safety holds in expectation (their d = 5 variant collides) |

## What SWARMOS does about each gap

| Gap | SWARMOS mechanism | Class | Status | Evidence |
|---|---|---|---|---|
| Learned / heuristic planners collide (3, 5) | Simplex runtime-assurance kernel downstream of every decision; ML fenced out of the safety path | E + I | Built (pre-existing) | 0 collisions in every SWARMOS run of every experiment; `tests/test_ml_fence.py` |
| "Zero collisions" is a weak safety statement (5 reports distributions) | Runtime Safety Invariant Monitor: INV-1..4 checked every tick on TRUE positions, three proximity layers, min-separation histogram, **negative control that must FAIL** | E metric, I integration | Built | `tests/test_safety_invariants.py`; `noop` arm fails INV-1 in every run |
| Safety depends on the network (4 assumes perfect comms) | Perception-backed kernel fallback: a robot sighted but not currently heard enters the kernel as an obstacle | R | Built, ON in product | Before: 1-20 collisions per condition under loss / latency / outage / blackout. After: 0 in all. `reports/comm_safety_fallback.log`, `tests/test_perception_fallback.py` |
| Comms impairment is untested (3, 4) | LINK_IMPAIR (loss, latency, timed outage) and ZONE_PARTITION wired into the radio; degradation sweep | I | Built | `tests/test_link_faults.py`; comm-sweep experiment |
| Conflicts handled only when they happen (1, 3) | Bounded predictive lookahead on intents each robot already hears within 15 m (no new messages) + explainable six-term risk score | R | Built, observe-only | Recall 0.90-0.95, median lead ~17 ticks (1.7 s); precision 0.18 (corridors) - 0.71 (open floor). `tests/test_lookahead_risk.py` |
| Decisions are opaque (all five) | Decision records: prediction, risk terms, each robot's verdict and reason, outcome; `/api/explain/<id>`; Inspector panel | I | Built | `tests/test_batch_and_audits.py`, INV-6 digest determinism |
| Deadlock only observed indirectly | Policy-agnostic wait-for-graph audit: cycles formed, persistent (>= 1 s) deadlocks, durations | E | Built (audit, not a detector the robots run) | Reported per arm in every experiment |
| Makespan on a fixed workload (1, 2) vs our survivorship-biased average | `overlap_batch` / `open_floor_batch` fixed-batch scenarios, textbook stop-and-wait arm, censored makespan, paired Student-t CI, stored config + replay check | R | Built | `tools/run_experiment.py`, `tools/replay_check.py` |
| Traffic-rule planning is a classical MAPF family | One-way lanes on single-file segments derived from the onboard map | E | Built, **measured and not adopted** (it made makespan worse) | `swarmos_traffic` arm |
| Decentralised deadlock escape without relaxing the floor (1, 3) | F1 path-aware kernel check (all arms), F3 leader keeps right of way, F5 standoff breaker, F6 release cooldown (all arms). Product default since 2026-09-27 | R + I | Built, ON in product | C2 v3 frozen benchmark: overlap +48.9 %, CI [+35.3, +62.5], finish 40/40 vs 21/40; common-finish +17.5 % [+1.4, +33.6]; open floor slower when both finish. `docs/C2_V3_PRODUCT_RESULT.md` |
| Online temporal-plan-graph execution (2), lease-based consensus allocation (4), congestion-priced allocation (1, 5) | - | R | **Roadmap, not built** | - |

## Defects found by the new instruments (and fixed)

1. **Network-dependent safety.** The kernel saw only radio peers. Measured
   collisions under every degraded-radio condition, including the existing
   single-robot blackout demo fault. Fixed by the perception fallback.
2. **Backtrack jog outside the verified envelope.** A fresh path began at the
   centre of the robot's current cell; a robot a few centimetres past it drove
   back before turning. That jog lay outside the straight swept segment the
   kernel clears, pushed pairs inside the 0.75 m floor, and froze both robots.
   Fixed in the engine (`_drop_backtrack`), applied to every arm. Measured on
   one seed: deadlock cycles 221 -> 27, stall releases hundreds -> 1.
3. **Dead benchmark endpoint** (`/api/benchmark/run` always failed) and a
   **second latent crash** (NaN in the JSON) - both fixed and tested.
4. **Faults that did nothing** (`LINK_IMPAIR`, `ZONE_PARTITION`) and a Compare
   tab button for a fault that does not exist - fixed; the UI verifier now
   checks it.

## Evaluated deadlock breakers (flagged, OFF in the product)

- **Mutual-hold break** (ladder): the right-of-way contest could come out
  asymmetric - each robot scores itself with its current yield streak and the
  peer with last tick's broadcast - so both yielded forever. Fixed by a
  deterministic id tie-break when both declare a hold. Helps the corridor floor
  (persistent deadlocks 257 -> 15), hurts the open floor on its own.
- **Separating-motion exemption** (kernel): lets a robot move away from a held
  peer it is already at the 0.75 m floor with. Its first version collided (5 of
  6 configurations) BEFORE the backtrack fix; after it, 0 collisions in 126
  runs, and with the mutual-hold break it removes every did-not-finish on the
  overlapping-paths floor. It is still a relaxation of the kernel veto and it
  raises margin breaches on the dense floor (88 -> 259), so it is kept OFF and
  presented with its evidence.

## Rejected after measurement

- **One-way lanes**: safe, but worse makespan on both batch floors.
- **Separating-motion exemption, first version** (before the backtrack fix):
  collisions in 5 of 6 configurations.

## Honest headline for judges (updated 2026-09-27)

SWARMOS's distinctive, defensible contribution is **measured safety and
resilience**:

- a verified kernel with invariant monitoring and a negative control;
- a network-independent safety floor, with a published before/after;
- an explainable, reproducible benchmark.

On the SIH C2 criterion, the frozen v3 simulation benchmark of the
**product default** reports C2 **MET** on the overlapping-paths floor:

- +48.9 %, 95 % CI [+35.3, +62.5] vs textbook stop-and-wait + F1 + F6;
- SWARMOS finished 40/40, the reference 21/40;
- 0 collisions in 240 runs;
- 240/240 replayed exactly.

The gain is mostly **reliability**, not raw speed. On seeds both finish it is
+17.5 % [+1.4, +33.6], and on the open floor SWARMOS is slower when both
finish. See `docs/C2_V3_PRODUCT_RESULT.md` and
`docs/JUDGE_NARRATIVE_C2_V3.md`. The earlier NOT MET results are history in
`docs/SUCCESS_CRITERIA_VERIFICATION.md`.
