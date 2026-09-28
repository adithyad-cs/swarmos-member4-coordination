# SWARMOS architecture map BEFORE the advanced-intelligence work (V0 = V3 product)

Recorded 2026-09-27T14:35Z.

- HEAD: `a6e1804`.
- V3 code identity: `f3dabbf0...094f`.

Status legend:

- LIVE_RUNTIME: called on every product run.
- OBSERVE_ONLY: runs live but never changes a decision.
- EXPERIMENTAL: flagged, OFF in the product.
- TEST_ONLY: exercised only by tests or tools.
- UNUSED: not called anywhere.

| Area | Module / function | Status | Notes |
|---|---|---|---|
| Simulation | `app/sim/engine.py SimEngine.step` | LIVE_RUNTIME | Sole state writer (law 1) |
| AMR state model | `app/coordination/models.py AMRState, MovementIntent` | LIVE_RUNTIME | Broadcast per robot per tick |
| Message system | `app/coordination/messages.py CoordinationMessage`; `MessageType` = ROBOT_STATE, PATH_INTENT, HEARTBEAT | LIVE_RUNTIME | Only ROBOT_STATE is sent in practice |
| Radio | `app/coordination/radio.py` (15 m range, loss/latency/partition, failure detector) | LIVE_RUNTIME | |
| Product policy factory | `app/api/runner._make_policy("swarmos")` | LIVE_RUNTIME | F1+F3+F5, F6 via `release_cooldown_ticks` |
| **Second SWARMOS factory** | `app/sim/cosim.make_treatment_policy` | LIVE_RUNTIME (Compare only) | **STALE**: no F1/F3/F5/F6. Demo-integrity bug. |
| Compare reference | `app/sim/cosim.make_baseline_policy` | LIVE_RUNTIME (Compare only) | Tuned stop-and-wait without F1/F6, not the C2 reference |
| Graded ladder | `SwarmPolicy._decide/_contest/_leader_verdict/_break_standoff` | LIVE_RUNTIME | |
| Safety kernel | `SwarmPolicy._monitor` (0.75 m floor, polyline sweep) | LIVE_RUNTIME, binding | |
| Perception fallback | `SwarmPolicy._monitor` sensed peers | LIVE_RUNTIME | |
| Integrity / quorum | `app/coordination/integrity.py` | LIVE when `integrity=True` (off by default) | |
| Task dispatcher | `SimEngine._dispatch` | LIVE_RUNTIME, CENTRAL | Greedy nearest-robot, capability/battery gates, WIP limit |
| Task auction (right-of-way) | `app/coordination/auction.py NegotiationEngine` | TEST_ONLY | Right-of-way negotiation, not task allocation; no runtime caller |
| Reservations | `app/coordination/reservation.py` | TEST_ONLY | |
| Conflict detector | `app/coordination/conflict.py` | TEST_ONLY | |
| Intent / peer registries, transport | `intent_registry.py`, `peer_registry.py`, `transport.py` | TEST_ONLY | |
| Lookahead | `app/coordination/lookahead.py predict_pair` | OBSERVE_ONLY | Analytic sampling of broadcast intents |
| Risk score | `app/coordination/risk.py` | OBSERVE_ONLY | |
| Prediction scoring | `app/sim/prediction.py` | OBSERVE_ONLY | |
| Decision records | `app/sim/decisions.py DecisionLog` | OBSERVE_ONLY | Records predicted-conflict decisions; `/api/explain` |
| Deadlock / livelock audits | `app/sim/deadlock_audit.py`, `engine._audit_livelock` | OBSERVE_ONLY | |
| ML forecaster | `app/ml/forecast.py` via `engine._advise` | OBSERVE_ONLY (advisory, scored, never binding) | Measured worse than persistence (X-05). Fenced by `tests/test_ml_fence.py` |
| Stall release + F6 | `engine._check_stalls`, `release_cooldown_ticks` | LIVE_RUNTIME | |
| Traffic rules, mutual-hold break, separating exemption | `swarm_policy` flags | EXPERIMENTAL (OFF) | |
| Benchmark engine | `tools/run_experiment.py` | LIVE (tooling) | Code identity, arm configs |
| Replay | `tools/replay_check.py` | LIVE (tooling) | |
| API benchmark path | `server /api/benchmark/run` | LIVE_RUNTIME | Product `_make_policy` (swarmos and baseline) |
| Lab path | `app/api/runner.RunManager` | LIVE_RUNTIME | Product `_make_policy` |
| Compare path | `app/api/cosim_runner` -> `app/sim/cosim.CoSimulation` | LIVE_RUNTIME | Stale factories (above) |
| UI | `web/js/panels/*` (inspector shows decision records; compare shows deltas) | LIVE | |

## Constraints found

- **No numpy, scikit-learn or scipy in the runtime environment.** Runtime
  inference must be dependency-free.
- **`tests/test_ml_fence.py`:** `app/coordination` must not import `app/ml`
  (law 3). The new predictor keeps that rule. The model lives in `app/ml`, and
  the product factory INJECTS it into the policy as an advisor object; the
  kernel never sees it.
