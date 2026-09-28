# SWARMOS Advanced Intelligence v1

Edge-AI conflict prediction, prediction-driven proactive coordination, live
distributed task allocation and the Compare demo-integrity fix.

Date: 2026-09-27. Nothing here is committed; everything is local and
uncommitted on top of `a6e1804`. Every number below has a file path behind it.

---

## A. Starting point: the V3 product baseline (V0)

- **Product:** `app/product.make_swarmos_policy()`. It runs the graded ladder,
  the binding Simplex safety kernel (0.75 m floor), the perception fallback and
  the observe-only analytic lookahead (H 15), plus these fixes:
  - F1 polyline sweep;
  - F3 leader rule;
  - F5 standoff breaker;
  - F6 release cooldown.
- **Off:** F2(a) and F2(b).
- **Frozen C2 v3 result:** +48.9 % [+35.3, +62.5] vs textbook stop-and-wait;
  finish 40/40 vs 21/40; identity `f3dabbf0…`; seeds 600001–600040; 240/240
  replayed. That result is unchanged and is not re-tuned here.
- **Baseline records:**
  - `reports/advanced_v1/baseline_record.txt`;
  - `reports/advanced_v1/immutable_evidence_sha256.txt` (98 historical
    evidence files, re-verified unchanged at the end);
  - `reports/advanced_v1/ARCHITECTURE_MAP_BEFORE.md`.

## B. The Compare demo-integrity fix

**Defect.** The Compare tab built its SWARMOS arm with a private, stale
factory (`cosim.make_treatment_policy`) that lacked F1/F3/F5/F6. What a
judge watched was not what was benchmarked.

**Fix:**
- `app/product.py` is now the single factory for every runtime path: Lab
  (`app/api/runner`), Compare (`app/sim/cosim`) and the benchmark.
- The reference arm is explicit: `COMPARE_REFERENCE = "stop_and_wait+F1+F6"`,
  which is the frozen C2 v3 reference.
- `describe_policy` reads the configuration back from the built object. The
  co-simulation publishes it in hello, frames and summary, and the Compare
  panel renders it (`data-cosim-config`).

**Guards:**
- `tests/test_compare_product_policy.py`:
  - PRODUCT_POLICY == COMPARE_SWARMOS_POLICY (configuration read-back);
  - the Compare treatment trace is bit-identical to a product engine;
  - `cosim.py` builds no controller of its own (AST check).
- Browser audit step: "Compare tab: SwarmOS arm shows the PRODUCT
  configuration, reference arm the C2 reference".

## C. Architecture (safety layering)

```
   Edge AI (advisory)          per robot, own inbox only, pure-Python model
          │  prediction {p, conflict, confidence, horizon, model, sha}
          ▼
   Coordination                ladder (+ PRE-HOLD proposal when PC is on)
          │  proposal (a Verdict); PC can only turn motion into a HOLD
          ▼
   Binding safety kernel       SwarmPolicy._monitor: 0.75 m floor, polyline
          │                    sweep, perception fallback - never consults AI
          ▼
   Engine                      sole state writer; invariant monitor on TRUE positions
```

- **The AI never touches the kernel.** `_monitor`'s source references no AI,
  proactive or auction symbol (`tests/test_edge_ai.py`).
- **Law 3 still holds:** `app/coordination` never imports `app/ml`
  (`tests/test_ml_fence.py`). The model is injected by `app/product.py`.
- **No heavy ML runtime:** `app/` imports no numpy, scikit-learn, torch or
  scipy (`tests/test_edge_ai.py`).
- **Safe fallback.** A missing, corrupt, tampered or feature-mismatched
  artifact, or an inference error at runtime, leaves the advisor OFF with the
  reason recorded. Coordination is then deterministic and trace-identical to
  V0 (tests).
- **Adversarial check.** A hostile model (always "conflict", confidence 1.0)
  and a blind model (always "no conflict") both leave every safety invariant
  at 0 (tests).
- **Allocation stays outside the safety path.** It only decides who does
  which task; it grants no motion.

## D. Files

**New:**
- `app/product.py`: the single controller factory; flags; model injection.
- `app/coordination/edge_features.py`: 20 runtime features.
- `app/coordination/proactive.py`: pre-hold / resume with anti-oscillation.
- `app/coordination/task_auction.py`: robot-side bids, gossip and consensus
  matching.
- `app/ml/edge_predictor.py`: pure-Python inference, integrity check,
  calibrated confidence.
- `app/ml/models/edge_conflict_v1.json`: the trained artifact.
- `app/sim/lease_ledger.py`: WMS lease register and arbitration.
- Tools:
  - `tools/edge_ai_dataset.py`
  - `tools/edge_ai_train.py`
  - `tools/edge_ai_baselines.py`
  - `tools/edge_ai_parity.py`
  - `tools/advanced_e2e_trace.py`
- Tests:
  - `tests/test_compare_product_policy.py`
  - `tests/test_edge_ai.py`
  - `tests/test_proactive.py`
  - `tests/test_task_auction.py`
  - `tests/test_auction_runtime.py`
  - `tests/test_advanced_protocol.py`
- Docs: `docs/ADVANCED_FROZEN_PROTOCOL_V1.md` and this file.

**Modified:**
- `app/coordination/swarm_policy.py`:
  - flags;
  - edge prediction per robot;
  - the PRE-HOLD step;
  - TASK_BID broadcast and receive;
  - the onboard route estimate;
  - stats.
- `app/coordination/messages.py`: `TASK_BID`.
- `app/sim/policy.py`: `Verdict.proactive` and `Verdict.edge_advisory`.
- `app/sim/engine.py`:
  - auction dispatch;
  - leases;
  - oscillation metric;
  - `advanced` and `allocation` KPIs.
- `app/sim/decisions.py`: Edge-AI, proactive and allocation DecisionRecords
  in the same digest.
- `app/sim/cosim.py`: uses the product factory; exposes `policy_config`.
- `app/api/runner.py`: `_make_policy` delegates to the product; `advanced`
  run option.
- `app/api/server.py`: `advanced` start option.
- `app/api/cosim_runner.py`: `policy_config`.
- `tools/run_experiment.py`:
  - arms `+EAI`, `+PC`, `+AU`;
  - per-run advanced counters;
  - the frozen seed blocks.
- `tools/audit_browser.mjs`: two new steps.
- Web:
  - `web/js/cosim.js` and `web/js/panels/cosim.js`: Compare configuration;
  - `web/js/panels/lab.js`: the "Advanced intelligence" switch;
  - `web/js/panels/analytics.js`: the live "Advanced intelligence" block;
  - `web/js/panels/inspector.js`: Edge-AI, proactive and allocation records.

**Preserved (verified):**
- the historical frozen experiments;
- the protocols v1 to v3;
- the v3 raw results and replay records;
- the historical reports;
- git history.

## E. Feature flags

| Flag | Default (product) | What it switches |
|---|---|---|
| `EDGE_AI_PREDICTOR` | **OFF** | Per-robot inference on every inbox peer inside 6 m; advisory records only |
| `PREDICTIVE_COORDINATION` | **OFF** | PRE-HOLD proposals from the robot's own predictions (needs EAI to have predictions) |
| `LIVE_DISTRIBUTED_AUCTION` | **OFF** | Replaces the greedy dispatcher with radio bids, consensus matching and WMS leases |

- The flags are independent (`tests/test_advanced_protocol.py::test_flags_are_independent`).
- With all flags OFF, behaviour reproduces V3 exactly. 12/12 frozen v3 runs
  replayed trace-identically after the integration; the product default is
  pinned by tests.
- In the UI, Lab → "Advanced intelligence: on" starts a run with all three,
  and Analytics shows the live counters.

## F. Edge-AI model: dataset provenance

- **Generator:** `tools/edge_ai_dataset.py`.
- **Policy recorded:** the V0 product.
- **Scenarios:**
  - `overlap_batch` (8 robots);
  - `open_floor_batch` (12 robots);
  - `rush_50` (16 robots).
- **Sampling:** one row per ordered in-range pair every 4 ticks; tick cap 4000.
- **Label `yH`:** the TRUE pair distance falls below `CONFLICT_M` = 0.97 m
  within the next H ticks, H ∈ {10, 15, 25}.
- **Features:** 20, computed only from what the robot has at runtime: its own
  state, its radio inbox, and the static onboard map. Each has a source, unit
  and preprocessing step, documented in the table at the top of
  `edge_features.py`.
  - Geometry: `dist_m`, `closing_mps`, `heading_cos`, `tcpa_s`, `dcpa_m`.
  - Analytic lookahead: `la_min_m`, `la_lead_ticks`.
  - Motion: `my_speed`, `peer_speed`, `my_remaining_m`, `peer_remaining_m`.
  - Crowding and messaging: `neighbours_3m`, `peer_holding`,
    `msg_age_ticks`, `my_yield_streak`, `peer_yield_streak`, `my_free_nbrs`.
  - Route and work: `path_overlap`, `my_has_task`, `peer_has_task`.
- **Split by run (seed); no run contributes rows to two splits.** The seed
  blocks were verified fresh before use.

| Split | Seeds | Runs | Rows | Positives y25 | sha256 (file) |
|---|---|---|---|---|---|
| train | 1100001–1100030 | 90 | 867,020 | 63,196 | `f81a8065…` |
| validation | 1200001–1200010 | 30 | 296,332 | 21,324 | `a65cfedb…` |
| test | 1300001–1300010 | 30 | 292,602 | 20,144 | `6e393cfd…` |

Manifest: `reports/advanced_v1/dataset/manifest.json`.

## G. Model selection (validation only; the test split was touched once)

Candidates: logistic regression, decision tree (depth 6), gradient boosting
(80×d3), random forest (40×d8), all with seed 7.

Rules, fixed before training:
1. Take the best validation PR-AUC. Within 0.005, the cheaper model wins.
2. The threshold maximises validation F0.5 (precision-weighted, because a
   false positive costs a needless hold).
3. The horizon is the longest whose best F0.5 is within 0.05 of the best.

Validation (PR-AUC / best F0.5):

| H | logreg | tree | gbdt | forest |
|---|---|---|---|---|
| 10 | 0.761 / 0.751 | 0.796 / 0.793 | 0.833 / 0.822 | **0.858 / 0.829** |
| 15 | 0.741 / 0.743 | 0.784 / 0.774 | 0.821 / 0.804 | **0.840 / 0.813** |
| 25 | 0.710 / 0.713 | 0.767 / 0.757 | 0.801 / 0.781 | **0.821 / 0.795** |

**Chosen:** random forest, H 25 ticks (2.5 s), threshold 0.50. The artifact
is `edge-conflict-v1`, content sha256 `829ae8fe…41ef0c`, file sha256
`5de8afcd…12628`, size 690 KB (`reports/advanced_v1/model_report.json`).

## H. Prediction metrics (test split, 292,602 rows, evaluated once)

| Metric | Value |
|---|---|
| PR-AUC | **0.820** |
| ROC-AUC | **0.976** |
| Precision / recall at threshold | **0.855 / 0.606** |
| F1 / F0.5 | 0.710 / 0.790 |
| False-positive rate / false-negative rate | 0.0076 / 0.394 (FP 2,067, FN 7,930, TP 12,214) |
| Calibration | Brier 0.026, ECE 0.0094 |
| Mean lead of true positives | 9.5 ticks (0.95 s) before the conflict |

**Against non-ML baselines** on the same test rows
(`reports/advanced_v1/model_baselines.json`):

| Predictor | Precision | Recall | F1 | FPR |
|---|---|---|---|---|
| **Edge-AI model** | **0.855** | 0.606 | **0.710** | **0.008** |
| Analytic lookahead (15-tick intent rollout) | 0.484 | 0.713 | 0.577 | 0.056 |
| Constant-velocity CPA | 0.626 | 0.453 | 0.525 | 0.020 |
| Distance threshold (tuned on validation) | 0.503 | 0.060 | 0.108 | 0.004 |

The model beats the best analytic baseline on every scenario (per-scenario F1):

| Scenario | Model F1 | Analytic lookahead F1 |
|---|---|---|
| open floor | 0.713 | 0.644 |
| overlap | 0.697 | 0.628 |
| rush_50 | 0.712 | 0.530 |

**Honest correction.** The first model report's "analytic lookahead" row for
H 25 was a definition bug. The lookahead feature only sees 15 ticks and
encodes "none" as 16, so `≤ 25` was always true. It never affected selection,
which compared ML candidates only. It was re-scored correctly in
`model_baselines.json`, and the training script was fixed.

**Reproducibility and parity** (`reports/advanced_v1/model_parity.json`):
- Refitting the recorded procedure reproduces the artifact hash exactly.
- The runtime pure-Python predictor matches scikit-learn on all 292,602 test
  rows: max |Δp| = 0.0 and 0 decision disagreements.
- This came after one fix: the runtime now rounds features to float32 as
  scikit-learn does before walking trees. The first comparison showed
  |Δp| ≤ 0.016.

**Runtime cost:**
- 33–49 µs per pair in pure Python.
- Loaded model: 5.9 MB.
- Controller compute p95 per tick rises from 2.0 to 3.3 ms (8 robots) and
  from 3.3 to 6.9 ms (12 robots), against a 100 ms tick budget.

**Every prediction** carries probability, conflict, confidence (the empirical
correctness of its validation probability bin), horizon, timestamp (tick),
model version and model sha256.

**Low confidence and staleness:**
- Proactive action requires confidence ≥ 0.6 and a prediction ≤ 2 ticks old.
- Anything else is ignored and counted.

## I. Prediction-driven proactive coordination (PC)

**When it acts.** For each robot, from its own predictions. A pre-hold is
entered only if all of these hold:
- p ≥ threshold;
- confidence ≥ 0.6;
- the prediction is fresh;
- the peer is not already holding;
- the pair is not in cooldown;
- the pair is not yet inside `CONFLICT_M` (the reactive ladder owns imminent
  conflicts).

**Who holds.** Both robots compute the same holder from the same broadcast
states, so they agree without a message:
1. a robot closing on a peer that is not closing on it;
2. otherwise the robot without a task;
3. otherwise the robot with the longer remaining route;
4. otherwise the higher robot id.

**What it does.** It turns a PROCEED/SLOW proposal into `YIELD, speed 0,
proactive="PRE-HOLD"` with the prediction attached. The result still passes
`_monitor`.

**Release.** A pre-hold ends when any of these happens:
- the prediction clears (p < 0.6 × threshold, after a minimum hold of 5 ticks);
- the conflict becomes imminent (the ladder takes over);
- the hard cap of 25 ticks is reached.

The pair then enters a 40-tick cooldown.

**Anti-oscillation, all measured:**
- entry/exit hysteresis;
- minimum hold;
- cooldown;
- stale rejection;
- counters for repeat holds on the same peer, prediction reversals and the
  engine's decision-oscillation metric (a stop within 10 ticks of a resume).

**Development result** (dev seeds 1000001–1000020, `adv_dev_ablation_r2`):

| | overlap V0 → V2 | open floor V0 → V2 |
|---|---|---|
| Pre-holds per run | 0 → 34.4 | 0 → 58.4 |
| Pre-hold outcomes (per run) | 26.6 cleared, 7.7 imminent, 0.1 timeout | 41.9 cleared, 16.2 imminent, 0.3 timeout |
| Decision oscillations | 100.7 → 89.2 | 766 → 316 |
| Stop events | 169 → 175 | 929 → 476 |
| Finish rate | 20/20 → 20/20 | 18/20 → 19/20 |
| Paired makespan | +1.9 % [−7.5, +11.2] | finished-only −8.7 % [−17.1, −0.3] |

Two tuning attempts on the development seeds changed nothing significantly:
- stricter confidence (0.8);
- a 1.0 s time-to-conflict gate, or a 2-tick minimum hold.

Every variant's CI spanned zero, and every variant increased open-floor
oscillation. So the designed constants were kept, and the knob was removed.

## J. Live distributed task allocation (AU)

**Flow** (`task_auction.py`, `lease_ledger.py`, `engine._auction_dispatch`):

1. **Announce.** The WMS opens an auction with task, version, pick, drop,
   payload, priority and robots excluded by F6. Admission is identical to the
   greedy dispatcher's WIP rule.
2. **Bid.** Every eligible robot computes its own cost from its own state,
   onboard profile, onboard map and radio inbox:
   - **Eligibility:** idle, not failed or charging, can carry the payload,
     finishes above the battery reserve, and its radio is up.
   - **Cost:** travel (onboard-map route / own max speed) + congestion (3 s
     per inbox peer within 4 m of the pick) + predicted conflict risk (4 s ×
     its own Edge-AI conflict probabilities, when EAI is on) + low battery.
3. **Exchange.** `TASK_BID` messages go over the real bounded 15 m radio
   (loss, latency, partition and blackout all apply), with full-table gossip.
   They are signed when integrity is on.
4. **Decide.** When the 5-tick window closes, every robot runs the same
   deterministic matching over the bids it knows: auctions in WMS queue
   order, each to its cheapest bidder not already matched or known busy
   (cost, then robot id). It claims its match and sends its own sealed bids
   with the claim.
5. **Lease.** The WMS ledger registers the lease: task, owner, version, grant
   tick, expiry (TTL 50 ticks, renewed by heartbeat) and status. The ledger
   only arbitrates where the radio consensus was incomplete:
   - conflicting claims are resolved by (cost, robot id);
   - an auction with no valid claim is filled from the robots' own sealed
     bids.
   Every close records `decided_by`: consensus or arbitration.
6. **Execute.** The assignment path is shared with the greedy dispatcher, so
   execution is identical.

**Ownership safety:**
- **Duplicate:** the invariant is at most one active lease per task and per
  robot. A violation is counted, never hidden.
- **Stale:** a claim with an old version or a retired auction is rejected.
- **Stolen:** the WMS re-checks eligibility on every claim and grants nothing
  to a robot it cannot hear.

**Failure recovery.** Each case is tested in `tests/test_auction_runtime.py`:

| Case | Outcome |
|---|---|
| Winner fails | Lease released, task re-queued and re-auctioned |
| Winner radio blackout | No heartbeat, lease EXPIRED at TTL, task re-queued; re-leased as version 2 to another robot |
| Whole-fleet blackout | No lease to an unheard robot; auctions close with no winner and re-open; leases resume after the blackout |
| 60 % packet loss | Allocation continues; 0 duplicate ownership |
| No claims for `MAX_ROUNDS` | Deterministic fallback allocation, recorded |

**Development history (honest).** The first version was 10.6 % slower than
greedy dispatch (`adv_dev_ablation`). Two root causes were found:
- a robot that was cheapest for several simultaneous auctions blocked the
  runners-up, so tasks idled until a re-auction;
- the auction capped work-in-progress more strictly than greedy.

Both were fixed:
- full-table gossip with consensus matching;
- sealed-bid gap filling;
- identical admission.

In `adv_dev_ablation_r2` the auction is at statistical parity with greedy:
- overlap −3.6 % [−14.9, +7.8];
- open floor, finished-only −6.4 % [−15.9, +3.0].

Ownership violations were 0 in every run. Robot consensus decided 73–77 % of
closes; the rest were ledger arbitration. Bid-weight and bid-window variants
changed nothing significantly.

**Honest scope.**
- Bids are computed and exchanged by the robots, and robots decide winners
  by consensus where their radio views agree.
- The WMS announces work, keeps the lease register and arbitrates where the
  views do not agree.
- This is distributed bidding with WMS lease arbitration. It is not a fully
  decentralised system, and the auction algorithm is not novel: it is a
  standard sequential single-item auction with consensus, in the CBBA family.

## K. DecisionRecords, UI evidence and the end-to-end trace

**DecisionRecords.** The existing DecisionRecord system (`app/sim/decisions.py`)
gains three record types. They go into the same sealed digest as the existing
records, so replay covers them.
- **`edge_ai`:** prediction episodes (opened, then cleared or conflict
  occurred).
- **`proactive`:** PRE-HOLD, with the prediction, the kernel's final verdict
  (APPROVED when the hold stands) and the peer's decision, through to RESUME
  with its reason and whether a conflict occurred during the hold.
- **`allocation`:** auction opened, then bids, winner, cost factors,
  agreement and `decided_by`, then lease through completed / released /
  expired.

The Inspector renders all three.

**UI.** In the Analytics panel, the "Advanced intelligence" block shows live:
- flags;
- Edge-AI status;
- the model (version, kind, horizon, sha);
- predictions and positives;
- mean inference µs;
- pre-holds, resumes and release reasons;
- auctions and re-auctions;
- leases (granted / expired / fallback);
- bid messages and agreement;
- consensus vs arbitration;
- ownership violations.

A missing value renders "--", never an invented number. Compare shows both
arms' read-back configurations, including advanced flags.

**The required chain** is extracted by `tools/advanced_e2e_trace.py` from a
real V4 run (overlap_batch, dev seed 1000001), with every link read from the
engine. File: `reports/advanced_v1/e2e_trace.json`.

1. Task **T022**: auction `A-T022-v1` opened at tick 0.
2. Eight robots bid with cost factors. **R006** won by robot consensus (3
   of 8 bidders agreeing), cost 3.0 s.
3. Lease v1 granted to R006 at tick 6, expires at tick 56 (renewed by
   heartbeat).
4. `task_assigned via=auction` at tick 6.
5. R006's Edge AI predicts a conflict with R005: p 0.63, confidence 0.79, TTC
   1.5 s, H 25.
6. **PRE-HOLD** at tick 19.
7. The safety kernel's final verdict is YIELD at speed 0: **APPROVED**.
8. The prediction clears with **no conflict during the hold**, and R006
   **RESUMES** at tick 24 (held 5 ticks).
9. The task is picked at tick 58 and completed at tick 306.
10. The 14 Inspector records for R006 are included.
11. **Replay:** the same trace hash and the same decision digest.
12. Safety PASS.

## L. Degraded-operation tests (all three features ON)

| Condition | Test | Result |
|---|---|---|
| Loss 30 % + latency 500 ms | `test_all_three_features_survive_degraded_operation` | PASS |
| Zone partition (EAST) | same | PASS |
| Robot failure | same | PASS |
| Single-robot radio blackout | same | PASS |
| Task burst | same | PASS |
| Winner failure / winner blackout / lease expiry | `test_winner_*` | PASS |
| Whole-fleet blackout (auction timeout) | `test_silenced_fleet_*` | PASS |
| 60 % packet loss (auction) | `test_heavy_packet_loss_*` | PASS |
| Model missing / corrupt / tampered / feature mismatch | `test_missing_corrupt_*`, `test_missing_model_*` | PASS; falls back to V0 trace |
| Inference error at runtime | `test_inference_error_*` | PASS; advisor disabled, run continues |
| Stale / low-confidence prediction | `tests/test_proactive.py` | PASS |
| Hostile or blind model | `test_a_hostile_or_blind_model_*` | PASS; 0 invariant failures |

"Result" means every safety invariant is at 0, ownership stays unique, and
work completes.

## M. Development ablation (dev seeds 1000001–1000020)

`reports/experiments/20260927T190833Z_adv_dev_ablation_r2`. The analysis is in
`reports/advanced_v1/dev_ablation_r2_analysis.json`. All arms: safety PASS
20/20 on both scenarios.

| vs V0 (paired makespan, 95 % CI) | overlap | open floor (finished-only) | open-floor finish |
|---|---|---|---|
| V1 +EAI (observe-only) | 0.0 (bit-identical traces) | 0.0 | 18/20 |
| V2 +EAI+PC | +1.9 [−7.5, +11.2] | −8.7 [−17.6, +0.2] | 19/20 |
| V3A +AU | −3.6 [−14.9, +7.8] | −6.5 [−16.6, +3.7] | 18/20 |
| V4 all | **−8.7 [−16.8, −0.6]** | −3.2 [−11.8, +5.3] | **20/20** |

The first-round ablation (`20260927T175733Z_adv_dev_ablation`, before the
auction fixes) is kept unmodified as development history.

## N. Final frozen evaluation

**Protocol:** `docs/ADVANCED_FROZEN_PROTOCOL_V1.md`, frozen before the first
run (sha256 of the file in `reports/advanced_v1/protocol_freeze_record.txt`).

**Setup:**
- Fresh seeds 1400001–1400040, never used before; guarded by
  `tests/test_advanced_protocol.py`.
- Code identity `ae7c9aee…a86ac5`, enforced by `--expect-identity`.
- Model content sha256 `829ae8fe…41ef0c`, read back into every arm's config.
- Arms: A, V0, V1, V2, V3A and V4.
- Scenarios: `overlap_batch` and `open_floor_batch`.
- 480 runs, no exclusions, no tuning.

**Output:**
- Experiment: `reports/experiments/20260927T201720Z_adv_frozen`.
- Analysis: `reports/advanced_v1/final_eval_analysis.json`.
- Replay log: `reports/advanced_v1/frozen_replay_all.log`.

**Replay: 480/480 reproduced exactly**, with code-identity MATCH and arm-config
MATCH (model hash included).

### N.1 Safety

**All 480 runs:**
- 0 collisions;
- 0 invariant failures;
- safety PASS 40/40 for every arm on both scenarios;
- 0 margin breaches;
- minimum separation ≥ 0.750 m.

The AI features changed no safety outcome.

### N.2 Inertness of observe-only Edge AI

V1's trace hash equals V0's on **80/80** (scenario, seed) pairs, while the
model ran **8.2 million** inferences with 0 errors.

### N.3 Primary and secondary endpoints (paired vs V0; 95 % CI on the per-seed % reduction; positive means faster)

| Arm | overlap: all-seed (= common, n = 40) | open floor: all-seed censored | open floor: common-finish | open-floor finish | Treatment-only DNF |
|---|---|---|---|---|---|
| V1 | 0.0 (identical) | 0.0 | 0.0 (n = 36) | 36/40 | none |
| V2 | +0.2 [−6.9, +7.3] | +6.8 [−3.9, +17.5] | −1.5 [−9.2, +6.2] (n = 36) | **40/40** | none |
| V3A | 0.0 [−5.7, +5.8] | −19.7 [−51.4, +12.0] | −6.5 [−13.9, +1.0] (n = 34) | 38/40 | **1400009, 1400020** |
| V4 | −3.4 [−8.8, +1.9] | +3.4 [−6.0, +12.8] | −5.0 [−10.0, 0.0] (n = 36) | **40/40** | none |

- V0 finishes 40/40 on overlap and 36/40 on open floor. Its open-floor DNF
  seeds are 1400005, 1400008, 1400014 and 1400017; V2 and V4 finish all four.
- t90 vs V0:
  - V2: overlap +2.6 [−2.0, +7.2], open floor +2.5 [−6.1, +11.2];
  - V4: overlap −1.2 [−7.2, +4.8], open floor +3.5 [−2.5, +9.4].

### N.4 Coordination behaviour (means per run)

| Arm | overlap: oscillations | overlap: held-work ticks | overlap: replans | open floor: oscillations | open floor: stop events | open floor: held-work ticks | open floor: replans |
|---|---|---|---|---|---|---|---|
| V0 | 119.1 | 3,474 | 741 | 947.5 | 1,102 | 26,122 | 7,931 |
| V2 | 104.7 | 3,370 | 677 | **343.4 (−64 %)** | **495 (−55 %)** | **8,608 (−67 %)** | **2,128 (−73 %)** |
| V3A | 92.2 | 2,784 | 609 | 1,464.2 | 1,614 | 16,715 | 3,849 |
| V4 | 97.6 | 3,606 | 808 | **307.7 (−68 %)** | **460 (−58 %)** | **8,167 (−69 %)** | **1,863 (−77 %)** |

### N.5 Runtime activity (all hold)

- **Edge AI:** status `ok` and calls > 0 in every EAI run (240/240); 0
  errors; prediction reversal rate 0.4–1.0 % of calls; 42–45 µs mean per
  inference.
- **Proactive:**
  - pre-holds: 1,415 (V2) and 1,333 (V4) on overlap; 2,268 (V2) and 2,277
    (V4) on open floor;
  - every pre-hold released: 72–79 % cleared, 21–27 % handed to the reactive
    ladder as imminent, ≤ 0.3 % timeout;
  - mean hold 5.9–6.3 ticks.
- **Auction:**
  - leases granted in every AU run (160/160); **0 ownership violations**;
    0 lease expiries in normal conditions; 0 fallback allocations;
  - robot consensus decided 70–75 % of closes, WMS arbitration the rest;
  - mean auction latency 6.0 ticks (0.6 s).

### N.6 Against the reference A (stop-and-wait+F1+F6, all-seed censored)

| Arm | overlap | open floor |
|---|---|---|
| V0 | +51.2 [+38.6, +63.9] | +36.6 [+10.3, +62.9] |
| V2 | +51.2 [+38.3, +64.1] | +52.8 [+40.3, +65.4] |
| V4 | +48.0 [+34.0, +62.1] | +50.1 [+36.8, +63.5] |

A finishes 24/40 on overlap and 14/40 on open floor.

### N.7 Decision (pre-registered rule)

| Arm | Rule 1: CI lower bound > 0 on primary | Rule 2: no treatment-only DNF | Rules 3–5 (safety, activity, replay) | Promoted? |
|---|---|---|---|---|
| V2 | ✗ (−6.9) | ✓ | ✓ | **No** |
| V3A | ✗ (−5.7) | ✗ (2 seeds) | ✓ | **No** |
| V4 | ✗ (−8.8) | ✓ | ✓ | **No** |

**The product default stays V0.** The three features ship as runtime-active,
tested, replayable opt-in flags. They are demonstrated live via Lab →
"Advanced intelligence", and their measured effects are reported, not
claimed as speed-ups.

## O. Replay

Every number above is replayable:
- frozen evaluation: 480/480;
- pipeline smoke: 24/24;
- V0 regression after integration: 12/12 frozen v3 runs trace-identical;
- the end-to-end trace replays identically, decision digest included.

Edge-AI, proactive and allocation DecisionRecords are sealed into the
same digest as every other record.

## P. Safety summary

- The AI is advisory and can only produce a HOLD. The kernel never consults
  it.
- The allocator grants no motion.
- A hostile model, a blind model, a missing model and a runtime inference
  error are each tested with 0 invariant failures.
- 480/480 frozen runs are safe.
- The 0.75 m floor, the veto and every invariant are unchanged. The AI adds
  no exemption.

## Q. Runtime overhead (frozen run means)

| | V0 | V1/V2/V4 (Edge AI on) | V3A (auction) |
|---|---|---|---|
| Controller compute p95, 8 robots | 1.9 ms | 3.2–3.3 ms | 1.9 ms |
| Controller compute p95, 12 robots | 3.6 ms | 6.5–7.2 ms | 3.6 ms |
| Messages / robot / tick | 2.42 / 2.84 | 2.37–2.42 / 2.69–2.84 | 2.35 / 2.80 |

- Per-inference cost: 42–45 µs.
- Model: 690 KB file, 5.9 MB loaded.
- Everything stays well inside the 100 ms tick.

## R. Code and model identity

| | Value |
|---|---|
| Code identity (frozen) | `ae7c9aee82176521325c59ab9f90358d69d6648c39aca51810bcc72d96a86ac5` (178 files) |
| Model content sha256 | `829ae8fe2e2ab134e41cb48340ce86df93163870f5118200d57f69133941ef0c` |
| Model file sha256 | `5de8afcd716b4aebd28f0ab76dd2a33e19e77df93c92a748be11920dabb12628` |
| Dataset files | train `f81a8065…`, validation `a65cfedb…`, test `6e393cfd…` |
| Compare-fix identity (intermediate) | `601cc723…c955f` |
| Historical v3 identity (unchanged) | `f3dabbf0…023094f` |
| Git | HEAD `a6e1804`, nothing committed |

## S. Demo configuration

- **Default demo** (the product, V0): Lab with any scenario, "Advanced
  intelligence: Off".
- **Advanced demo:**
  1. Lab: `overlap_batch` → "Advanced intelligence: Edge AI + proactive +
     live auction" → Start.
  2. Analytics → "Advanced intelligence" shows live model identity,
     predictions, pre-holds and resumes, auctions, leases,
     consensus/arbitration and 0 ownership violations.
  3. Inspector on a robot shows its allocation record (bids, winner,
     factors, lease), its Edge-AI prediction and its PRE-HOLD → kernel
     APPROVED → RESUME.
- **Compare** shows both arms' read-back configuration: SwarmOS = product
  F1 + F3 + F5 + F6; reference = stop_and_wait+F1+F6.

## T. Exact judge-facing claims (allowed)

1. "Edge AI predicts congestion and conflict risk and provides advisory
   signals to coordination." (Test PR-AUC 0.820, precision 0.855, beating
   every analytic baseline; runs per robot in ~45 µs.)
2. "Final movement remains constrained by the deterministic binding safety
   kernel." (The kernel never consults the model; 480/480 frozen runs safe.)
3. "Task allocation uses distributed runtime bids." (Robots bid from their
   own state over the peer radio and decide by consensus in 70–75 % of
   auctions; a WMS ledger registers leases and arbitrates the rest.)
4. "SWARMOS incorporates congestion and predicted conflict into allocation."
   (Bid cost terms; each winner's cost factors are shown in the Inspector.)
5. "On the open floor, prediction-driven pre-holds cut decision oscillation
   by 64 %, replans by 73 % and held-work time by 67 %, and the batch
   finished on all 40 fresh seeds (vs 36/40), with no significant change in
   completion time." (Frozen evaluation.)

**Not claimed:**
- "AI controls the robots";
- "AI guarantees safety";
- a novel auction algorithm;
- full decentralisation;
- any speed-up from the advanced features (none was significant);
- physical-world safety.

## U. Known limitations

- **No makespan gain.** None of the three features improves makespan
  significantly. The auction alone lost two open-floor seeds that V0
  finished.
- **Model recall is 0.61.** The model is tuned for precision; 39 % of
  conflicts within 2.5 s are not predicted. The reactive ladder and the
  kernel still handle them.
- **Consensus is partial.** It decides only 70–75 % of auctions with the
  15 m radio; the WMS ledger arbitrates the rest from the robots' own bids.
- **Training data is simulated only**, from the V0 policy. Distribution shift
  under PC/AU (the model changes what it predicts) is not re-trained for.
- **The lease heartbeat reads the simulated radio state.** A real deployment
  needs a real WMS link.
- **Simulation only.** There is no hardware validation.
