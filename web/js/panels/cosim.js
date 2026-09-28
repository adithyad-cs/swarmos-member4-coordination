/* Compare panel: the X-12 counterfactual co-simulation.
 *
 * Two identical warehouses, identical seeds, identical task streams. One is
 * arbitrated by the SwarmOS policy, one by a stop-and-wait baseline. Because
 * both are seeded and both emit a trace hash, any row in this panel can be
 * reproduced exactly - that is the whole point, and it is why the hashes are
 * shown rather than hidden.
 *
 * Reading rules obeyed here:
 *  - a value that does not exist renders as DASH, never as 0
 *  - a KPI missing from either arm is dropped upstream and never invented
 *  - saturated colour marks the WINNING arm only, and only when there is a
 *    real difference; a tie is ink, not green
 *  - no animation beyond the 160 ms row transition already in the CSS
 */

import { ARM_TREATMENT, ARM_BASELINE } from "../cosim.js";
import { store } from "../store.js";
import { num, int, DASH, shortHash } from "../format.js";

/* Human labels for the headline KPIs. The server sends machine keys; a panel
 * that shows machine keys to a judge has not finished its job. */
const KPI_LABEL = {
  tasks_complete: "Tasks done",
  tasks_per_min: "Tasks / min",
  collisions: "Collisions",
  near_misses: "Near misses",
  p95_completion_s: "p95 completion",
  avg_wait_s: "Avg wait",
  sla_miss_pct: "SLA miss",
  replans: "Replans",
};

/* Digits per KPI. Integers stay integers: "22.0 collisions" is noise. */
const KPI_DIGITS = {
  tasks_complete: 0,
  collisions: 0,
  near_misses: 0,
  replans: 0,
  tasks_per_min: 1,
  p95_completion_s: 1,
  avg_wait_s: 1,
  sla_miss_pct: 1,
};

// Every id here must be a real FaultKind value: the verifier enforces it.
// DEMAND_SPIKE used to sit here and was rejected by the server on every click.
const FAULTS = [
  ["ROGUE_ROBOT", "Rogue robot"],
  ["ROBOT_FAILURE", "Robot failure"],
  ["COMM_BLACKOUT", "Comm blackout"],
  ["LINK_IMPAIR", "Link impairment"],
  ["TASK_BURST", "Demand spike"],
];

function label(key) {
  if (KPI_LABEL[key]) return KPI_LABEL[key];
  return key.replace(/_/g, " ");
}

function digits(key) {
  return KPI_DIGITS[key] ?? 1;
}

export class CosimPanel {
  constructor(el, cosim) {
    this.el = el;
    this.cosim = cosim;
    this._built = false;
  }

  /* Bind the controls once. Re-binding on every render would leak listeners
   * at 10 Hz. */
  init() {
    this.el.addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-act]");
      if (!btn) return;
      const act = btn.dataset.act;
      if (act === "start") this._start();
      else if (act === "stop") this.cosim.stop();
      else if (act === "inject") this.cosim.inject(btn.dataset.fault);
    });
  }

  _start() {
    // Match the live run when there is one, so the ghosts are honestly
    // comparable. Otherwise fall back to the default demo configuration
    // (rush_50, seed 11, fleet 8).
    const ticks = Number(this.el.querySelector("#cosim-ticks")?.value || 1800);
    this.cosim.start({
      scenario: store.scenario || "rush_50",
      seed: store.seed != null ? Number(store.seed) : 11,
      fleet_size: store.hasData ? store.robots.size : 8,
      ticks,
      speed: 4.0,
    });
  }

  render() {
    const c = this.cosim;
    if (!this._built) {
      this.el.innerHTML = this._shell();
      this._built = true;
    }
    this._paint(c);
  }

  _shell() {
    const opts = FAULTS.map(
      ([k, t]) => `<button class="btn" data-act="inject" data-fault="${k}">${t}</button>`
    ).join("");
    return `
      <h2 class="panel__title">Compare</h2>
      <p class="field__hint">
        Two identical warehouses, same seed, same tasks. One arbitrated by
        SwarmOS, one by stop-and-wait. Both are replayable from their hash.
      </p>
      <p class="field__hint">
        Live illustration, one seed. Both arms are built by the same product
        factory as the Lab run; the configuration each arm actually runs is
        read back from the server and shown below. C2 benchmark (simulation,
        frozen protocol v3, product default vs textbook stop-and-wait + F1 +
        F6, overlap_batch, 40 seeds): +48.9% capped time reduction, 95% CI
        [+35.3%, +62.5%]; finished 40/40 vs 21/40; where both finished
        +17.5% [+1.4%, +33.6%]. On the open floor SwarmOS is slower when both
        finish. Source: docs/C2_V3_PRODUCT_RESULT.md.
      </p>

      <div class="field">
        <label class="field__label" for="cosim-ticks">Horizon (ticks)</label>
        <input class="field__control num" id="cosim-ticks" type="number"
               min="1" max="3000" step="100" value="1800" />
        <div class="field__hint">
          1800 ticks = 180 s. Below about 900 the fleet is still filling up, so
          throughput numbers mean nothing.
        </div>
      </div>

      <div class="btn-row">
        <button class="btn btn--primary" data-act="start">Run comparison</button>
        <button class="btn" data-act="stop">Stop</button>
      </div>

      <div class="cosim-status" id="cosim-status"></div>
      <div id="cosim-config"></div>
      <div id="cosim-delta"></div>

      <h3 class="panel__title" style="margin-top: var(--space-5)">Inject into both arms</h3>
      <p class="field__hint">
        A fault always lands on both arms at the same tick. Injecting into one
        would decide the result in advance.
      </p>
      <div class="btn-row btn-row--wrap">${opts}</div>

      <div id="cosim-hashes"></div>`;
  }

  _paint(c) {
    const status = this.el.querySelector("#cosim-status");
    const deltaEl = this.el.querySelector("#cosim-delta");
    const hashEl = this.el.querySelector("#cosim-hashes");
    const cfgEl = this.el.querySelector("#cosim-config");
    if (!status || !deltaEl || !hashEl) return;

    status.innerHTML = this._statusHtml(c);
    if (cfgEl) cfgEl.innerHTML = this._configHtml(c);
    deltaEl.innerHTML = this._deltaHtml(c);
    hashEl.innerHTML = this._hashHtml(c);
  }

  /* The configuration each arm really runs, as the server read it back from
   * the built policy objects. Nothing here is assumed client side: before the
   * server reports it, the rows render as DASH. */
  _configHtml(c) {
    const cfg = c.policyConfig;
    const row = (label, arm) => {
      const a = cfg ? cfg[arm] : null;
      if (!a) {
        return `<div class="kv"><span class="kv__k">${label}</span>
          <span class="kv__v">${DASH}</span></div>`;
      }
      const fixes = (a.fixes && a.fixes.length) ? a.fixes.join(" + ") : "none";
      const adv = Array.isArray(a.advanced) && a.advanced.length
        ? ` | advanced: ${a.advanced.join(", ")}` : "";
      const what = a.reference ? `reference ${a.reference}` : `${a.name || a.class}`;
      return `<div class="kv"><span class="kv__k">${label}</span>
        <span class="kv__v" data-cosim-config="${arm}">${what} | fixes: ${fixes}${adv}</span></div>`;
    };
    return `
      <h3 class="panel__title" style="margin-top: var(--space-4)">Active configuration</h3>
      ${row("SwarmOS arm", ARM_TREATMENT)}
      ${row("Reference arm", ARM_BASELINE)}`;
  }

  _statusHtml(c) {
    if (c.error) {
      return `<div class="cosim-note" data-tone="bad">${c.error}</div>`;
    }
    const tick = c.tick == null ? DASH : int(c.tick);
    const horizon = c.horizonTicks == null ? DASH : int(c.horizonTicks);
    const state = c.running ? "Running" : (c.summary ? "Complete" : "Idle");

    let lock = "";
    if (c.running && c.lockstep === false) {
      // Lockstep is the guarantee that both arms saw the same sim time. If it
      // is lost the comparison is void and must say so.
      lock = `<div class="cosim-note" data-tone="bad">
        Arms are out of lockstep, so this comparison is not valid. Stop and
        re-run it.</div>`;
    }

    const div = c.divergenceTick == null
      ? `<div class="kv"><span class="kv__k">Diverged at</span>
           <span class="kv__v num">${DASH}</span></div>`
      : `<div class="kv"><span class="kv__k">Diverged at</span>
           <span class="kv__v num">tick ${int(c.divergenceTick)}</span></div>`;

    return `
      <div class="kv"><span class="kv__k">State</span>
        <span class="kv__v">${state}</span></div>
      <div class="kv"><span class="kv__k">Tick</span>
        <span class="kv__v num">${tick} / ${horizon}</span></div>
      ${div}
      ${lock}`;
  }

  _deltaHtml(c) {
    if (!c.delta || !c.delta.length) {
      if (c.running) {
        return `<div class="empty">
          <div class="empty__cause">No metric has separated the two arms yet.</div>
          <div class="empty__action">Both arms are still warming up; rows appear as soon as a KPI differs.</div>
        </div>`;
      }
      return `<div class="empty">
        <div class="empty__cause">No comparison has been run.</div>
        <div class="empty__action">Press Run comparison to simulate both policies over the same tasks.</div>
      </div>`;
    }

    const rows = c.delta.map((d) => this._row(d)).join("");
    return `
      <div class="delta">
        <div class="delta__head">
          <span class="delta__metric">Metric</span>
          <span class="delta__val">SwarmOS</span>
          <span class="delta__val">Baseline</span>
          <span class="delta__val">Delta</span>
        </div>
        ${rows}
      </div>`;
  }

  _row(d) {
    const dg = digits(d.key);
    // better is an arm name from the server: "swarmos", "baseline" or "tie".
    // It is NOT a boolean, and the sign of delta is raw, so a negative delta
    // can perfectly well be a win.
    const won = d.better === ARM_TREATMENT ? "swarmos"
      : d.better === ARM_BASELINE ? "baseline" : "tie";

    let deltaTxt = DASH;
    if (d.delta != null && !Number.isNaN(d.delta)) {
      const sign = d.delta > 0 ? "+" : "";
      deltaTxt = `${sign}${num(d.delta, dg)}`;
      if (d.pct != null) deltaTxt += ` (${d.pct > 0 ? "+" : ""}${num(d.pct, 1)}%)`;
    }

    return `
      <div class="delta__row" data-won="${won}">
        <span class="delta__metric">${label(d.key)}</span>
        <span class="delta__val num">${num(d.treatment, dg)}</span>
        <span class="delta__val num delta__val--base">${num(d.baseline, dg)}</span>
        <span class="delta__val num delta__delta">${deltaTxt}</span>
      </div>`;
  }

  _hashHtml(c) {
    const t = c.hashes[ARM_TREATMENT];
    const b = c.hashes[ARM_BASELINE];
    if (!t && !b) return "";
    // Two different hashes is the expected, healthy result: two policies that
    // produced the same trace would mean one of them never ran.
    const distinct = Boolean(t && b && t !== b);
    return `
      <h3 class="panel__title" style="margin-top: var(--space-5)">Replay</h3>
      <div class="hashline" data-match="${String(distinct)}">
        <span class="kv__k">SwarmOS</span>
        <span class="num" title="${t || ""}">${shortHash(t)}</span>
      </div>
      <div class="hashline" data-match="${String(distinct)}">
        <span class="kv__k">Baseline</span>
        <span class="num" title="${b || ""}">${shortHash(b)}</span>
      </div>
      <div class="field__hint">
        Same scenario, same seed, same hash - every time. These two hashes
        differ because the two policies made different decisions.
      </div>`;
  }
}
