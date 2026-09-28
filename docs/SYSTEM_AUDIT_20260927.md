# System regression and feature audit, 2026-09-27 (before the frozen C2 run)

All changes are uncommitted local working-tree changes. Nothing was committed
or pushed. Raw logs: `reports/audit_20260927/`.

## 1. Feature inventory and how each was verified

A feature is marked verified only if a check below exercised its behaviour
(not merely imported it).

| Area | Feature | Verified by | Result |
|---|---|---|---|
| Core sim | 6 scenarios build, spawn, move | audit_system core | PASS |
| | Task lifecycle, batch termination, cap -> DNF | audit_system core | PASS |
| | Determinism (trace hash), task stream seed-only | audit_system core, pytest | PASS |
| | Idle parking (batch) | audit_system core | PASS |
| Coordination | Bounded radio, intent broadcast | audit_system coordination | PASS |
| | Graded ladder PROCEED/SLOW/YIELD/WAIT/REROUTE, utility contest | audit_system coordination | PASS |
| | Failure detection + task release | audit_system coordination | PASS |
| | Perception fallback (no change on healthy radio) | audit_system, pytest | PASS |
| | Headline flags OFF (exemption, mutual-hold break, traffic) | audit_system, test_c2_protocol | PASS |
| | Reservation / auction / conflict libraries | unit tests only | NOT in the live path (documented) |
| Safety | INV-1..4, L2/L3 layers, min separation | audit_system safety, pytest | PASS |
| | Negative control (noop) FAILS INV-1 | audit_system safety | PASS |
| | Monitor-OFF collides (kernel does the work) | audit_system safety | PASS |
| | Identical 0.75 m floor for every arm | test_c2_protocol | PASS |
| Prediction / explain | Observe-only lookahead (trace identical) | audit_system prediction | PASS |
| | Decision records, digest determinism, explain API | audit_system, pytest | PASS |
| Faults | All 10 FaultKinds, engine level | audit_system faults | PASS (see 8) |
| | Live API inject, with and without a selected robot | audit_system api-faults | PASS |
| | Co-sim inject lands on both arms | audit_system api-faults | PASS |
| Benchmark | run_experiment / replay_check / benchmark endpoint | pytest, smoke, replay | PASS |
| Frontend | Landing, topbar, map, KPI, rail, Fleet, Inspector, Analytics, Lab, Compare, palette, keys, reconnect | audit_browser.mjs (real Chromium) | 26/26 PASS |
| | Static UI contract (ids, imports, fault buttons) | verify_ui_contract.py | 39 pass, 1 benign warn |
| Legacy | ML forecaster: advisory only, KILL_ML leaves hash unchanged | audit_system faults | PASS |

## 2. Audit result

Every feature marked PASS above was exercised end to end. The bugs below were
found by the audit, and each fix has a regression test.

## 3. Bugs found (this audit)

1. **Non-robot faults failed whenever a robot was selected in the Lab**
   (`unexpected keyword argument robot_id`), affecting 6 of 10 faults.
2. **Dashboard stuck "Disconnected"**: no websocket library in the documented
   install, so uvicorn answered `/ws/fleet` with 404. Found only by the real
   browser.
3. **Analytics panel ReferenceError** (`metres` not imported); runtime error on
   every frame.
4. **Battery-drained robot wedged for 5,400+ ticks**: the reroute avoid-hint
   equalled the start cell when the blocker shared the robot's cell, and was
   stripped.
5. **Stop-and-wait lockstep livelock** (baseline behaviour, not an engine bug):
   head-on robots time out on the same tick, reroute symmetrically, and meet
   again indefinitely. The stall release never fires because they move. The
   `policy.py` docstring claimed "livelock bounded", which is false.
6. **My own first fix for 5 was wrong.** An engine task release re-dispatched
   the task to the same pair, which re-formed the livelock and turned the
   tuned baseline's finish on seed 11 into a DNF. It was caught by the
   instrumentation tests and reverted (see 4).
7. **Benchmark statistics claim was false.** "Censoring never manufactures an
   improvement" is only true if the treatment arm never DNFs on a seed the
   reference finished; censoring flatters whichever arm fails.
8. **Missing benchmark metrics**: t90, stop-and-wait events, backtracks,
   resolved conflicts, comm-induced holds, livelock episodes, finish rate,
   finished-only / both-finished statistics, and code identity.

## 4. Bugs fixed

| # | Fix (smallest layer) | Regression test |
|---|---|---|
| 1 | `engine.fault_accepts` plus `RunManager.inject` drop and report `ignored_params` | `test_api.py` (3 tests), audit api-faults |
| 2 | `websockets` added to README, pyproject and `run.sh` checks | `test_install_contract.py`, browser audit |
| 3 | Import fixed; the verifier gains `check_imports` (proven to FAIL without the fix) | verifier |
| 4 | `engine._blocker_cell` | `test_batch_and_audits.py` (unit + battery regression) |
| 5 | Baseline left unchanged (not tuned against the evaluation). The docstring is corrected, and an observe-only livelock audit (`LIVELOCK_WINDOW_TICKS`, KPIs `livelock_episodes` / `livelock_ticks`) makes the cause of DNF visible. | `test_batch_and_audits.py` (4 tests incl. trace unchanged) |
| 6 | Release removed; observe-only only | same |
| 7 | Docstring corrected. A censored target is marked MET only when the treatment has no treatment-only DNF seeds (`not_admissible` otherwise), and DNF seed lists are reported. | `test_benchmark_instrumentation.py::test_censored_target_is_not_admissible...` |
| 8 | Read-only instrumentation in the engine, prediction and policy; runner records, summary and md; `code_identity` + `--expect-identity`; replay compares identity and more metrics | `test_benchmark_instrumentation.py` (8), `test_c2_protocol.py` (4) |

## 5. Remaining issues (not fixed; reported)

- **Many DNFs in every arm on the smoke seeds** (`reports/experiments/20260927T001148Z_c2_smoke`):
  - overlap_batch: stop-and-wait DNF 2/3, tuned 2/3, SWARMOS 0/3.
  - open_floor_batch: SWARMOS DNF **3/3** (25-32 of 36 tasks), stop-and-wait 2/3, tuned 2/3.
  - SWARMOS on the open floor is a real product weakness. The frozen protocol
    does not use open_floor_batch for the C2 verdict, and that was decided
    before seeing any evaluation data.
- **Validity threat:** C2 on overlap_batch may be decided largely by
  stop-and-wait livelock DNFs. The protocol reports finished-only and
  both-finished statistics and DNF seed lists so this is visible. It does not
  change the baseline.
- A robot holding a task can drain its battery to 0 (the charge rule applies
  to task-less robots only).
- The reservation, auction and conflict libraries are unit-tested but not in
  the live path.
- The kernel's at-the-floor freeze limitation remains. SWARMOS min separation
  was 0.744 m in one smoke run (an L2 margin breach below the 0.75 m floor;
  contact is < 0.70 m).
- `contests` vs `contests_won` count different things (documented in `stats()`).
- Experiment directories from 2026-09-26 are superseded (the engine changed
  in fix 4); their replays will not match the current code.
- Verifier warning: HTML ids declared but never read by JS (benign, known).

## 6-9. Gate results at freeze

| Check | Result |
|---|---|
| pytest (full) | **650 passed**, 0 failed (`reports/audit_20260927/pytest.log`) |
| UI contract verifier (with API) | 39 pass, 1 warn, 0 FAIL |
| Real-browser audit | 26 pass, 0 FAIL |
| Backend / fault-matrix audit | 82 pass, 0 FAIL, covering all 10 FaultKinds at engine level, 10 live faults x {no robot, robot selected}, and 10 co-sim faults |
| Replay (smoke dir) | 6/6 reproduced exactly |

## 10. Frozen C2 protocol

`docs/C2_FROZEN_PROTOCOL.md`

## Frozen identity

- `ba4086a693013487342c7832c6e9ff23bad8c7a8247fffb2e878091664179656`
- base `a6e1804` + uncommitted tree
