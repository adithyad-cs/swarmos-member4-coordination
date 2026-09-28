# Session summary - 2026-09-26: research gaps, SIH C2 benchmark, safety evidence

> Historical record. Its C2 statements ("NOT MET", parity) are SUPERSEDED by
> the 2026-09-27 frozen evaluations. The current product result is
> `docs/C2_V3_PRODUCT_RESULT.md`.

Branch `claude/sleepy-ride-lsj94c`. **All changes are uncommitted and nothing was pushed**, per the owner's instruction.

Test gate at the end of the session: **621 passed** (576 before).
UI contract verifier at the end of the session: **37 pass, 1 warn (the known benign one), 0 FAIL**.

## What was built

| Area | What | Files | Tests |
|---|---|---|---|
| Credibility fixes | `/api/benchmark/run` crashed on every call (factory arity), plus a second crash (NaN in JSON) | `app/api/server.py` | `test_api.py` |
|  | `LINK_IMPAIR` / `ZONE_PARTITION` did nothing; now wired to the radio, with `ticks` for timed outages, and latency quantised to ticks | `app/sim/engine.py`, `app/coordination/radio.py` | `test_link_faults.py` |
|  | Compare-tab fault buttons fixed; the verifier now checks them | `web/js/panels/cosim.js`, `tools/verify_ui_contract.py` | verifier |
|  | Housekeeping: `pyproject.toml`, leaked `trans.log` and `.acc` logs deleted, stray footer lines removed from 60 files | - | - |
| Network-independent safety | Perception-backed kernel fallback (a robot sighted but not heard becomes an obstacle). ON in the product. Only adds constraints; normal runs are bit-identical | `swarm_policy.py` (`SENSED_EXTRA_M`) | `test_perception_fallback.py` |
| SIH C2 benchmark | `overlap_batch`, `open_floor_batch`, `corridor_demo` fixed-batch scenarios; `TextbookStopAndWaitPolicy`; makespan / total completion / path efficiency KPIs; idle parking in batch scenarios (both arms) | `scenarios.py`, `policy.py`, `engine.py`, `runner.py` | `test_batch_and_audits.py` |
| Reproducibility | Experiment runner (config + runs.jsonl + paired-CI summary) and replay checker | `tools/run_experiment.py`, `tools/replay_check.py` | replay-checked every experiment directory |
| Safety invariant monitor | INV-1..4 checked every tick; three proximity layers; min separation and histogram; verdict; negative control | `engine.py` | `test_safety_invariants.py` |
| Predictive lookahead + risk | Per-robot prediction on broadcast intents (no new messages), a six-term explainable risk score, and prediction scoring (precision / recall / lead) | `coordination/lookahead.py`, `coordination/risk.py`, `sim/prediction.py` | `test_lookahead_risk.py` |
| Deadlock audit | Policy-agnostic wait-for-graph cycles, including persistent ones (>= 1 s) | `sim/deadlock_audit.py` | `test_batch_and_audits.py` |
| Explainability | Decision records (prediction -> risk -> each robot's decision and reason -> outcome); `GET /api/explain/<id>`; Inspector "Predicted conflicts"; Analytics "Safety invariants" block | `sim/decisions.py`, `server.py`, `web/js/*` | `test_api.py`, INV-6 digest test |
| Engine defect fix | Leading-waypoint backtrack jog outside the kernel's verified envelope, which pushed pairs inside the 0.75 m floor. All arms | `engine.py` `_drop_backtrack` | `test_batch_and_audits.py` |
| Flagged, OFF | One-way lanes (`traffic_rules`), mutual-hold break, separating-motion exemption | `coordination/traffic.py`, `swarm_policy.py` | `test_deadlock_breakers.py`, traffic tests |

## What was measured (`reports/experiments/*`)

- **C2 is NOT MET.**
  - On the fixed batch against textbook stop-and-wait, the product SWARMOS is far behind: DNF 4/9 and 8/9 on the two floors.
  - The best flagged variant reaches parity on the overlapping-paths floor (-5.5%, CI [-42, +31]) and is still behind on the open floor.
  - The tuned baseline beats both.
- **Safety.**
  - 0 collisions in every SWARMOS run across all five experiments: benchmark, breakers, exemption sweep, 9 comm conditions and long runs.
  - The no-coordination control collides 316-639 times per scenario (9 runs each), which proves the monitor.
- **Comms.**
  - Without the fallback, SWARMOS collided under 30% loss, 500 ms latency, outages, blackout and partition (up to 15 per 5 runs).
  - With the fallback: 0 in all conditions.
- **Lookahead.** Recall 0.90-0.95, median lead about 17 ticks, precision 0.18 (corridors) to 0.71 (open floor).

## Decisions and why

- Perception fallback ON: it closes a measured safety gap and changes nothing in normal runs.
- Observe-only lookahead ON: no motion change; it feeds explanations.
- Separating-motion exemption OFF: it is safe in 126 runs but relaxes the kernel veto and raises margin breaches. The owner's rule is not to weaken the kernel, so this is the owner's call, with the evidence in `docs/SUCCESS_CRITERIA_VERIFICATION.md`.
- Mutual-hold break OFF: on its own it hurt the open floor.
- One-way lanes OFF: they made makespan worse.

## Not built (flagged, not faked)

- Proactive corridor holds driven by lookahead
- Adaptive recovery choice (WAIT / CONCEDE / REROUTE costing)
- Robot-side decentralized wait-for-graph detection (the engine audit exists)
- Congestion-priced allocator
- Task leasing
- Online TPG / CBBA / GNN / MARL / multi-process UDP

## Next steps, by expected value

1. Decide on the separating exemption. If enabled, rerun `tools/run_experiment.py` for the C2 matrix and republish.
2. The open-floor gap: SWARMOS still forms persistent deadlocks where the tuned baseline does not. The wait-for-graph audit plus decision records now make each one traceable.
3. The at-the-floor kernel freeze is the remaining structural limitation (`swarm_policy._monitor`, KNOWN LIMITATION).
