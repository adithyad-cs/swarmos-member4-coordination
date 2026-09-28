/* Simulation Lab.
 *
 * Run control plus the determinism receipt (novelty N3). The receipt is the
 * only honest way to SHOW determinism in a live demo: run a seed, record the
 * trace hash, re-run the same seed, and compare the two hashes on screen. If
 * they differ the panel says so in plain words rather than hiding it.
 *
 * Every control here is disabled when the transport is not live, because a
 * button that silently does nothing is worse than a button that is visibly
 * unavailable.
 */
import { store, LINK } from "../store.js";
import { shortHash, int } from "../format.js";

const FAULTS = [
  { id: "robot_failure", label: "Robot failure (kill one robot)" },
  { id: "comm_blackout", label: "Comm blackout (cut one robot's radio 6 s)" },
  { id: "link_impair", label: "Link impairment (drops and latency, fleet-wide)" },
  { id: "blocked_aisle", label: "Block an aisle (static obstacle)" },
  { id: "rogue_agent", label: "Rogue agent (adversarial robot)" },
];

export class LabPanel {
  constructor(el, transport) {
    this.el = el;
    this.transport = transport;
    this.scenarios = null;
    this.baselineHash = null;
    this.compareHash = null;
    this.busy = false;
    this._built = false;
    this._note = "";
  }

  async init() {
    const res = await this.transport.scenarios();
    if (res.ok && Array.isArray(res.data && res.data.scenarios)) {
      this.scenarios = res.data.scenarios;
    } else {
      this.scenarios = null;
      this._note = res.error ? `Scenario list unavailable: ${res.error}` : "";
    }
    this.render();
  }

  render() {
    if (!this._built) this._build();
    this._update();
  }

  _build() {
    const opts = this.scenarios
      // The server key is ScenarioSpec.as_dict().name. There is no 'id'
      // field, so a fallback must land on another FIELD, never on the
      // whole record - that is what produced value="[object Object]".
      ? this.scenarios.map((s) => `<option value="${s.name}">${s.title || s.name}</option>`).join("")
      : `<option value="rush_50">rush_50</option>
         <option value="narrow_aisle_deadlock">narrow_aisle_deadlock</option>
         <option value="blocked_aisle">blocked_aisle</option>`;

    this.el.innerHTML = `
      <h2 class="panel__title">Run configuration</h2>
      <div class="field">
        <label class="field__label" for="lab-scenario">Scenario</label>
        <select class="field__control" id="lab-scenario">${opts}</select>
        <div class="field__hint" id="lab-scenario-hint">${this.scenarios ? "Loaded from the server." : "Server list unavailable; showing the built-in scenarios."}</div>
      </div>
      <div class="field">
        <label class="field__label" for="lab-fleet">Fleet size</label>
        <input class="field__control num" id="lab-fleet" type="number" min="1" max="50" step="1" value="24">
        <div class="field__hint">Sustained 10 Hz is verified up to 50 robots.</div>
      </div>
      <div class="field">
        <label class="field__label" for="lab-seed">Seed</label>
        <input class="field__control num" id="lab-seed" type="number" min="0" step="1" value="11">
        <div class="field__hint">Same seed and same scenario must reproduce the same trace hash.</div>
      </div>
      <div class="field">
        <label class="field__label" for="lab-integrity">Message integrity</label>
        <select class="field__control" id="lab-integrity">
          <option value="off" selected>Off</option>
          <option value="on">Signed messages and sentinel council</option>
        </select>
        <div class="field__hint">When on, robots sign their broadcasts and neighbours
          cross-check position claims. Two independent witnesses are required before
          any robot is contained. Off by default, and off changes nothing: the trace
          hash is identical either way.</div>
      </div>
      <div class="field">
        <label class="field__label" for="lab-advanced">Advanced intelligence</label>
        <select class="field__control" id="lab-advanced">
          <option value="off" selected>Off (shipped product)</option>
          <option value="on">Edge AI + proactive coordination + live auction</option>
        </select>
        <div class="field__hint">Edge AI predicts pair conflicts and the robot may
          pre-hold; tasks are allocated by robot bids exchanged over the radio under
          WMS leases. Advisory only: the safety kernel still decides every motion.
          Live counters appear in Analytics.</div>
      </div>
      <div class="btn-row">
        <button class="btn btn--primary" id="lab-start">Start</button>
        <button class="btn" id="lab-pause">Pause</button>
        <button class="btn" id="lab-step">Step</button>
        <button class="btn" id="lab-stop">Stop</button>
      </div>
      <div class="field__hint" id="lab-note"></div>

      <div class="panel__section">
        <h2 class="panel__title">Fault injection</h2>
        <div class="field">
          <label class="field__label" for="lab-fault">Fault</label>
          <select class="field__control" id="lab-fault">
            ${FAULTS.map((f) => `<option value="${f.id}">${f.label}</option>`).join("")}
          </select>
          <div class="field__hint">Faults are injected into the live run at the next tick boundary.</div>
        </div>
        <div class="btn-row"><button class="btn" id="lab-inject">Inject</button></div>
      </div>

      <div class="panel__section">
        <h2 class="panel__title">Determinism receipt</h2>
        <div class="field__hint">Capture the hash of the current run, re-run the same seed, then compare.</div>
        <div class="btn-row">
          <button class="btn" id="lab-capture">Capture hash</button>
          <button class="btn" id="lab-compare">Compare now</button>
        </div>
        <div id="lab-hashes"></div>
      </div>`;

    const on = (id, fn) => this.el.querySelector(id).addEventListener("click", fn);
    on("#lab-start", () => this._start());
    on("#lab-pause", () => this._pause());
    on("#lab-step", () => this._guard(() => this.transport.stepRun(1)));
    on("#lab-stop", () => this._guard(() => this.transport.stopRun()));
    on("#lab-inject", () => this._inject());
    on("#lab-capture", () => this._hash("baseline"));
    on("#lab-compare", () => this._hash("compare"));
    this._built = true;
  }

  _cfg() {
    return {
      scenario: this.el.querySelector("#lab-scenario").value,
      fleet_size: Number(this.el.querySelector("#lab-fleet").value),
      seed: Number(this.el.querySelector("#lab-seed").value),
      integrity: this.el.querySelector("#lab-integrity").value === "on",
      advanced: this.el.querySelector("#lab-advanced").value === "on",
    };
  }

  async _guard(fn) {
    if (this.busy) return;
    this.busy = true;
    this._update();
    const res = await fn();
    this.busy = false;
    this._note = res && res.ok === false ? res.error || "Request failed." : "";
    this.render();
  }

  _start() {
    this.baselineHash = null;
    this.compareHash = null;
    return this._guard(() => this.transport.startRun(this._cfg()));
  }

  _pause() {
    return this._guard(() => (store.running ? this.transport.pauseRun() : this.transport.resumeRun()));
  }

  _inject() {
    const fault = this.el.querySelector("#lab-fault").value;
    const target = store.selectedRobot || null;
    return this._guard(() => this.transport.injectFault({ fault, robot_id: target }));
  }

  async _hash(slot) {
    const res = await this.transport.traceHash();
    if (!res.ok) {
      this._note = res.error || "Trace hash unavailable.";
      this.render();
      return;
    }
    const h = res.data && (res.data.hash || res.data.trace_hash);
    if (slot === "baseline") this.baselineHash = h || null;
    else this.compareHash = h || null;
    this._note = "";
    this.render();
  }

  _update() {
    const live = store.link !== LINK.DOWN;
    const dis = (id, cond) => { const n = this.el.querySelector(id); if (n) n.disabled = cond; };
    dis("#lab-start", !live || this.busy);
    dis("#lab-pause", !live || this.busy || !store.hasData);
    dis("#lab-step", !live || this.busy || !store.hasData);
    dis("#lab-stop", !live || this.busy || !store.hasData);
    dis("#lab-inject", !live || this.busy || !store.hasData);
    dis("#lab-capture", !live || this.busy || !store.hasData);
    dis("#lab-compare", !live || this.busy || !this.baselineHash);

    const pause = this.el.querySelector("#lab-pause");
    if (pause) pause.textContent = store.hasData && !store.running ? "Resume" : "Pause";

    const note = this.el.querySelector("#lab-note");
    if (note) {
      note.textContent = this._note
        ? this._note
        : live
          ? `Tick ${int(store.tick)} \u00b7 ${store.running ? "running" : store.hasData ? "paused" : "idle"}`
          : "Backend is not connected. Run controls are unavailable.";
    }

    const box = this.el.querySelector("#lab-hashes");
    if (!box) return;
    if (!this.baselineHash && !this.compareHash) {
      box.innerHTML = `<div class="empty">
        <div class="empty__cause">No hash captured yet.</div>
        <div class="empty__action">Run a scenario, then press Capture hash.</div>
      </div>`;
      return;
    }
    const match = this.baselineHash && this.compareHash ? this.baselineHash === this.compareHash : null;
    box.innerHTML = `
      <div class="hashline" data-match="${match === null ? "" : match}">
        <span class="kv__k">Captured</span><span class="num">${shortHash(this.baselineHash)}</span>
      </div>
      <div class="hashline" data-match="${match === null ? "" : match}">
        <span class="kv__k">Re-run</span><span class="num">${shortHash(this.compareHash)}</span>
      </div>
      <div class="field__hint">${
        match === null
          ? "Re-run the same seed and press Compare now."
          : match
            ? "Identical. The run is bit-for-bit reproducible from the seed."
            : "MISMATCH. These two runs diverged; determinism is not holding for this configuration."
      }</div>`;
  }
}
