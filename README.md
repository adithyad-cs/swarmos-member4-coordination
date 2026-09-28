# SWARMOS

**Edge-AI Based Distributed Fleet Coordination for Autonomous Mobile Robots (AMRs)**
SIH26123 — Smart India Hackathon — Team Member 4 (Coordination)

A distributed fleet-coordination system for warehouse AMRs: up to 50 robots
pick and drop tasks on a simulated warehouse floor, coordinated by a
decentralized negotiation layer, backstopped by a hard safety kernel, with an
edge-AI advisory layer strictly outside the safety path, and a live web
dashboard for operators.

No build step, no bundler, no Node.js — the frontend is plain HTML/CSS/vanilla
JavaScript (native ES modules), and the backend is a single Python process.

---

## 1. Clone the repository

```bash
git clone https://github.com/adithyad-cs/swarmos-member4-coordination.git
cd swarmos-member4-coordination
```

If the repository is private, you will need a GitHub account with access,
plus either an SSH key or a Personal Access Token configured on the machine
you are cloning to. If you hit an authentication prompt, use your GitHub
username and a Personal Access Token (not your account password) when asked.

---

## 2. System requirements

| Requirement | Details |
|---|---|
| **Python** | 3.10 or newer (3.11/3.12/3.13 all work). The code uses PEP 604 `X \| Y` type-hint syntax, which fails to import on Python < 3.10. |
| **Python packages** | `starlette`, `uvicorn`, `pydantic`, `websockets` (all on PyPI). `websockets` is **required**: without it uvicorn answers the dashboard's websocket with 404 and the map never fills. |
| **Browser** | Any modern browser — Chrome, Firefox, Edge. No extensions or special settings needed. |
| **OS** | Linux, macOS, or Windows (WSL recommended on Windows for the `run.sh` script; see below for a plain-Python alternative) |
| **Disk / network** | No database server, no external network access needed to run the simulation itself. |

Nothing in this list is specific to any particular company environment or
internal tooling — it is all standard, publicly available software.

**Optional** (only needed for extra, non-essential features):

| Optional package | Needed for |
|---|---|
| `pytest` | Running the automated test suite (`./run.sh --test`) |
| `python-docx` | Regenerating the Word documents in `docs/gen_*_docx.py` |
| `python-pptx` | Regenerating the PowerPoint decks in `docs/gen_*_pptx.py` |
| a local Chrome/Chromium binary | Running the developer diagnostic scripts in `tools/diag_*.py` and the browser audit `tools/audit_browser.mjs` (not needed to use the product) |

---

## 3. Install dependencies

```bash
python3 --version          # confirm 3.10+
pip install starlette uvicorn pydantic websockets
```

If you also want to run tests or regenerate the docs/PPTs:

```bash
pip install pytest httpx python-docx python-pptx
```

---

## 4. Run it

```bash
./run.sh                 # start the server on port 8770
./run.sh --open          # start, wait for health check, then open a browser
./run.sh --demo          # --open, and also auto-start the reference demo run
./run.sh 8080             # start on a different port
./run.sh --test          # run the automated test suite instead of serving
./run.sh --check         # quick environment sanity check, then exit
```

Then open **http://127.0.0.1:8770/** in your browser (or let `--open`/`--demo`
do it for you).

If `./run.sh` does not work on your system (for example, on plain Windows
without WSL, or if your shell is not bash), start the server directly with
plain Python instead:

```bash
python3 -m uvicorn app.api.server:app --host 127.0.0.1 --port 8770
```

then open `http://127.0.0.1:8770/` yourself.

### Stopping the server

Press `Ctrl-C` in the terminal where it is running.

---

## 5. Run the test suite

```bash
./run.sh --test
```

or directly:

```bash
PYTHONPATH=. python3 -m pytest tests/ -q
```

All 621 tests should pass. If you see a `PluginValidationError` at
collection time, a stale site-wide pytest plugin is interfering; work
around it with:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. python3 -m pytest tests/ -q
```

---

## 6. Project layout

```
app/sim/            simulation engine, robot/task/warehouse models, scenarios
app/coordination/   the coordination policy (verdict ladder, safety monitor,
                     adversarial containment)
app/ml/             the advisory-only congestion forecaster
app/db/             persistence and the paired-comparison statistics engine
app/api/            the Starlette web server (REST + websocket)
web/                the browser dashboard (plain HTML/CSS/JS, no build step)
tests/              the automated test suite
tools/              diagnostic and one-off developer scripts
docs/               specification documents, session notes, and the
                    generator scripts for the Word/PPT deliverables
```

### Current C2 result (simulation benchmark, frozen protocol v3, 2026-09-27)

**Product default: F1 + F3 + F5 + F6.**

- F2(a) and F2(b) are off.
- F6 is a 300-tick release cooldown.
- The safety floor is 0.75 m.

**Primary result**, on `overlap_batch`, SWARMOS as shipped vs textbook
stop-and-wait + F1 + F6, over 40 fresh seeds (600001-600040):

- capped time reduction **+48.9 %, 95 % CI [+35.3 %, +62.5 %]**;
- finish rate 40/40 vs 21/40;
- no seed failed only by SWARMOS;
- all five frozen decision conditions passed. **C2 is met for the product
  default in this benchmark.**

**Caveats:**

- On seeds where both finished, SWARMOS is +17.5 %, CI [+1.4 %, +33.6 %]. That
  is below 20 % on speed alone; most of the gain is finishing batches the
  reference does not.
- On `open_floor_batch`: capped +33.7 % [+4.5 %, +62.8 %] and finish 40/40 vs
  15/40, but SWARMOS is slower when both finish.

**Safety and integrity:**

- 0 collisions and 0 invariant failures in 240 runs.
- The only margin breach (0.748 m) came from the tuned reference arm.
- Replay 240/240 exact; code identity
  `f3dabbf0d732bfc218a1ab31f906299ca1baee5c4b1de148534b16c0d023094f`.

Details: `docs/C2_V3_PRODUCT_RESULT.md`, `docs/JUDGE_NARRATIVE_C2_V3.md`,
`docs/C2_FROZEN_PROTOCOL_V3.md`, `reports/c2v3/`. This is a simulation result
and is not a physical-world certification.

### Reproducible experiments

```bash
# the SIH C2 benchmark: fixed batch, makespan, paired seeds, 95% CI
PYTHONPATH=. python3 tools/run_experiment.py --name c2 \
    --scenarios overlap_batch open_floor_batch \
    --arms stop_and_wait baseline swarmos --reference stop_and_wait

# communication degradation sweep (loss, latency, outage, blackout, partition)
PYTHONPATH=. python3 tools/run_experiment.py --name comm --comm-sweep \
    --scenarios rush_50 --fleet 16 --ticks 1200 --arms swarmos swarmos_nofb

# re-run stored runs and check the trace hashes match bit-for-bit
PYTHONPATH=. python3 tools/replay_check.py reports/experiments/<dir>

# replay the frozen C2 v3 product benchmark (all 240 runs, identity required)
PYTHONPATH=. python3 tools/replay_check.py \
    reports/experiments/20260927T130822Z_c2v3_frozen \
    --all --require-identity --workers 4
```

Each run writes `config.json`, `runs.jsonl` and `summary.md` under
`reports/experiments/`. The current C2 result is `docs/C2_V3_PRODUCT_RESULT.md`.
Earlier measurements and how the result was reached are in
`docs/SUCCESS_CRITERIA_VERIFICATION.md` (history, marked superseded). The
literature comparison is `docs/RESEARCH_POSITIONING.md`.

See `docs/GRIDLOCK_DEFECT_20260922.md` and `SWARMOS_JUDGE_MASTER_DOCUMENT.docx`
for a full technical write-up of the architecture, feature inventory, and
known-issues history.

---

## 7. Troubleshooting

- **"No module named starlette/uvicorn/pydantic"** — run
  `pip install starlette uvicorn pydantic websockets` (use `pip3` if `pip` points to
  Python 2 on your system).
- **"ENTER SWARMOS" button does nothing when opening `web/landing.html`
  directly from disk (`file://...`)** — this is expected and handled: the
  page will navigate you to the running server's own copy of the page on
  the first click; click **ENTER SWARMOS** a second time there to actually
  start the simulation. This only applies if you open the HTML file
  directly instead of using `./run.sh`.
- **Dashboard shows "Disconnected" and an empty map, and the server log says
  "No supported WebSocket library detected"** - install `websockets`
  (`pip install websockets`) and restart the server. `./run.sh --check`
  reports this.
- **Port 8770 already in use** — pass a different port:
  `./run.sh 8080`, then open `http://127.0.0.1:8080/`.
