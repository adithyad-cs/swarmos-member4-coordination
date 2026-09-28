/* Decision Inspector (X-26).
 *
 * This is the panel that answers "why did that robot stop?", and it is the
 * strongest thing in the product to show a judge, because it makes the Simplex
 * architecture (N5) VISIBLE: the advisory proposal, the binding safety kernel,
 * and the final verdict are rendered as three separate stages. When the kernel
 * overrides the advisory layer the override is stated in words, not implied.
 *
 * Architectural law 3 -- ML is advisory only -- is not a claim here, it is a
 * rendering. If the ML layer ever appeared in the "binding" stage, this panel
 * would show it, which is exactly why it is built this way.
 */
import { store } from "../store.js";
import { metres, secs, pct, int, num, DASH } from "../format.js";

/* Advanced-intelligence records. Every value shown comes from the record the
 * simulation published; an absent value renders as DASH, never as a guess. */
function edgeHtml(d, self) {
  const p = d.prediction || {};
  const out = d.outcome
    ? (d.outcome.result === "conflict_occurred"
      ? `Conflict band reached ${int(d.outcome.after_ticks)} ticks later.`
      : "Prediction cleared without a conflict.")
    : "Episode open.";
  return `
    <div class="panel__section" data-record="edge_ai">
      <div class="kv"><span class="kv__k">${d.id} &middot; tick ${int(d.tick)} &middot; Edge AI</span>
        <span class="kv__v"><span class="chip">p ${num(p.probability, 2)}</span></span></div>
      <div class="chain__note">${d.detected_by} predicts a conflict with ${d.peer}:
        probability ${num(p.probability, 2)}, confidence ${num(p.confidence, 2)},
        time to conflict ${p.ttc_s == null ? DASH : num(p.ttc_s, 1) + " s"},
        horizon ${int(p.horizon_ticks)} ticks. Model ${p.model || DASH}.</div>
      <div class="chain__note">Coordination this tick: ${d.decision ? `${d.decision.kind} - ${d.decision.reason}` : DASH}</div>
      <div class="chain__note">${out}</div>
    </div>`;
}

function proactiveHtml(d, self) {
  const p = d.prediction || {};
  const s = d.safety || {};
  const o = d.outcome;
  const out = o
    ? `${o.result} after ${int(o.held_ticks)} ticks (${o.reason}); conflict during hold: ${o.conflict_during_hold ? "yes" : "no"}.`
    : "Holding.";
  return `
    <div class="panel__section" data-record="proactive">
      <div class="kv"><span class="kv__k">${d.id} &middot; tick ${int(d.tick)} &middot; Proactive</span>
        <span class="kv__v"><span class="chip">${d.action}</span></span></div>
      <div class="chain__note">Prediction: ${d.held} &harr; ${d.peer}, p ${num(p.probability, 2)},
        confidence ${num(p.confidence, 2)}, time to conflict ${p.ttc_s == null ? DASH : num(p.ttc_s, 1) + " s"}.</div>
      <div class="chain__note">Action: ${d.action} ${d.held}; ${d.peer}: ${d.peer_decision ? `${d.peer_decision.kind} - ${d.peer_decision.reason}` : DASH}.</div>
      <div class="chain__note">Safety kernel: ${s.verdict || DASH} (final ${s.kernel_final || DASH}).</div>
      <div class="chain__note">Result: ${out}</div>
    </div>`;
}

function allocationHtml(d, self) {
  const bids = (d.bids || []).map((b) => `${b.robot} ${num(b.cost, 2)}`).join(", ") || DASH;
  const f = d.factors || {};
  const lease = d.lease
    ? `${d.lease.status} (owner ${d.lease.owner}, v${int(d.lease.version)}, expires tick ${int(d.lease.expires_tick)})`
    : DASH;
  const out = d.outcome ? `${d.outcome.result}${d.outcome.reason ? " - " + d.outcome.reason : ""}` : "Open.";
  return `
    <div class="panel__section" data-record="allocation">
      <div class="kv"><span class="kv__k">${d.id} &middot; tick ${int(d.tick)} &middot; Allocation</span>
        <span class="kv__v"><span class="chip">${d.status || DASH}</span></span></div>
      <div class="chain__note">Task ${d.task}${d.auction ? ` (auction ${d.auction}, round ${int(d.round)})` : ""}.
        Bids: ${bids}.</div>
      <div class="chain__note">Winner: ${d.winner || DASH}${d.cost != null ? `, cost ${num(d.cost, 2)} s` : ""}${
        d.factors ? ` (travel ${num(f.travel_s, 1)}, congestion ${num(f.congestion_s, 1)}, conflict risk ${num(f.risk_s, 1)}, battery ${num(f.battery_s, 1)})` : ""}.
        ${d.bidders != null ? `Bidders agreeing on the winner: ${int(d.agreeing_bidders)}/${int(d.bidders)}.` : ""}
        ${d.decided_by === "consensus" ? "Decided by the robots' own consensus; the WMS only registered the lease."
          : d.decided_by === "arbitration" ? "Radio consensus was incomplete; the WMS ledger filled it from the robots' own sealed bids." : ""}</div>
      <div class="chain__note">Lease: ${lease}. Outcome: ${out}</div>
    </div>`;
}

/* One decision record as a sentence a judge can read aloud: what was
 * predicted, how severe, what each robot was told and why, what happened. */
function decisionHtml(d, self) {
  if (d.trigger === "edge_ai") return edgeHtml(d, self);
  if (d.trigger === "proactive") return proactiveHtml(d, self);
  if (d.trigger === "allocation") return allocationHtml(d, self);
  const p = d.prediction || {};
  const risk = d.risk || {};
  const peer = (d.robots || []).find((r) => r !== self) || DASH;
  const mine = d.decisions ? d.decisions[self] : null;
  const terms = risk.terms
    ? Object.entries(risk.terms).map(([k, v]) => `${k} ${num(v, 2)}`).join(", ")
    : DASH;
  const out = d.outcome
    ? (d.outcome.result === "conflict_occurred"
      ? `Conflict band reached ${int(d.outcome.after_ticks)} ticks later.`
      : "Predicted window passed without the conflict.")
    : "Outcome pending.";
  return `
    <div class="panel__section">
      <div class="kv"><span class="kv__k">${d.id} &middot; tick ${int(d.tick)}</span>
        <span class="kv__v"><span class="chip">${risk.band || DASH} ${num(risk.score, 2)}</span></span></div>
      <div class="chain__note">Predicted ${p.geometry || "conflict"} with ${peer} in
        ${int(p.lead_ticks)} ticks (min ${metres(p.min_dist_m, 2)} m). Risk terms: ${terms}.</div>
      <div class="chain__note">Decision: ${mine ? `${mine.kind} - ${mine.reason}` : DASH}</div>
      <div class="chain__note">${out}</div>
    </div>`;
}

export class InspectorPanel {
  constructor(el, transport) {
    this.el = el;
    this.transport = transport || null;
    this._explained = null;
  }

  /** On a new selection, pull that robot's decision history once. */
  _seedHistory(id) {
    if (!this.transport || !id || this._explained === id) return;
    this._explained = id;
    this.transport.explain(id).then((res) => {
      if (res && res.ok && res.data && Array.isArray(res.data.decisions)) {
        store.mergeDecisions(res.data.decisions);
      }
    });
  }

  render() {
    const id = store.selectedRobot;
    if (!id) {
      this.el.innerHTML = `
        <h2 class="panel__title">Decision inspector</h2>
        <div class="empty">
          <div class="empty__cause">No robot selected.</div>
          <div class="empty__action">Click a robot on the map, or pick one from the Fleet roster.</div>
        </div>`;
      return;
    }
    this._seedHistory(id);
    const r = store.robot(id);
    if (!r) {
      this.el.innerHTML = `
        <h2 class="panel__title">Decision inspector</h2>
        <div class="empty">
          <div class="empty__cause">${id} is no longer reporting.</div>
          <div class="empty__action">It may have completed its run or been removed. Select another robot.</div>
        </div>`;
      return;
    }

    const ig = store.kpis && store.kpis.integrity ? store.kpis.integrity : null;
    const council = ig && ig.council ? ig.council : null;
    // The most recent council ruling about THIS robot, if any.
    const ruling = council && Array.isArray(council.events)
      ? [...council.events].reverse().find((e) => e.robot_id === id) || null
      : null;
    // Sub-quorum suspicion: accused, but not yet by enough witnesses. Showing
    // this matters - it is the difference between "under suspicion" and
    // "convicted", and collapsing the two would make the quorum meaningless.
    const pending = council && council.pending ? council.pending[id] || null : null;

    const v = store.verdict(id);
    const kind = v ? v.kind : DASH;
    const adv = v && v.advisory ? v.advisory : null;
    const overridden = Boolean(adv && adv.kind && adv.kind !== kind);

    this.el.innerHTML = `
      <h2 class="panel__title">${r.robot_id} &middot; tick ${int(store.tick)}</h2>

      <div class="verdict" data-kind="${kind}">
        <div class="verdict__kind">${kind}</div>
        <div class="verdict__reason">${v && v.reason ? v.reason : "No verdict recorded for this tick."}</div>
      </div>

      <div class="panel__section">
        <h2 class="panel__title">Decision chain</h2>
        <div class="chain">
          <div class="chain__stage">
            <span class="chain__role">Advisory</span>
            <span class="chain__detail">${adv && adv.kind ? adv.kind : "none"}
              <span class="chain__note">${adv && adv.reason ? adv.reason : "ML layer made no proposal this tick. It is never required to."}</span>
            </span>
          </div>
          <div class="chain__stage" data-overridden="${overridden}">
            <span class="chain__role">Binding</span>
            <span class="chain__detail">Safety kernel: ${kind}
              <span class="chain__note">${overridden
                ? `Kernel OVERRODE the advisory ${adv.kind}. The kernel verdict is final.`
                : "Kernel concurred with the proposal. It still had the final word."}</span>
            </span>
          </div>
          <div class="chain__stage">
            <span class="chain__role">Applied</span>
            <span class="chain__detail">speed scale ${v && v.speed_scale != null ? metres(v.speed_scale, 2) : DASH}
              <span class="chain__note">Scale 0 means a full stop was commanded for this tick.</span>
            </span>
          </div>
        </div>
      </div>

      <div class="panel__section">
        <h2 class="panel__title">State</h2>
        <div class="kv"><span class="kv__k">Status</span><span class="kv__v"><span class="chip" data-state="${r.status}">${r.status}</span></span></div>
        <div class="kv"><span class="kv__k">Position</span><span class="kv__v num">${metres(r.position.x)}, ${metres(r.position.y)} m</span></div>
        <div class="kv"><span class="kv__k">Velocity</span><span class="kv__v num">${metres(r.velocity, 2)} m/s</span></div>
        <div class="kv"><span class="kv__k">Battery</span><span class="kv__v num">${pct(r.battery)} %</span></div>
        <div class="kv"><span class="kv__k">Task</span><span class="kv__v">${r.current_task_id || DASH}</span></div>
        <div class="kv"><span class="kv__k">Sim time</span><span class="kv__v num">${secs(store.simTime)} s</span></div>
      </div>

      ${ig ? `
      <div class="panel__section">
        <h2 class="panel__title">Integrity</h2>
        ${ruling ? `
          <div class="kv"><span class="kv__k">Ruling</span><span class="kv__v">
            <span class="chip" data-state="QUARANTINED">${ruling.action === "quarantine" ? "CONTAINED" : "RELEASED"}</span>
          </span></div>
          <div class="kv"><span class="kv__k">Reason</span><span class="kv__v">${ruling.reason || DASH}</span></div>
          <div class="kv"><span class="kv__k">Witnesses</span><span class="kv__v">${(ruling.witnesses || []).join(", ") || DASH}</span></div>
          <div class="kv"><span class="kv__k">At tick</span><span class="kv__v num">${int(ruling.tick)}</span></div>
          <div class="chain__note">${ruling.detail || ""}</div>
        ` : pending ? `
          <div class="kv"><span class="kv__k">Ruling</span><span class="kv__v">Under suspicion, not contained</span></div>
          <div class="chain__note">Accused by ${int(pending)} witness${pending === 1 ? "" : "es"};
            ${int(council.quorum)} are required. One robot's word is never enough.</div>
        ` : `
          <div class="kv"><span class="kv__k">Ruling</span><span class="kv__v">No accusation</span></div>
          <div class="chain__note">Signatures verified; position claims agree with what
            neighbours observed.</div>
        `}
        ${r.claimed ? `
          <div class="kv"><span class="kv__k">Claimed</span><span class="kv__v num">${metres(r.claimed.x)}, ${metres(r.claimed.y)} m</span></div>
          <div class="kv"><span class="kv__k">Actual</span><span class="kv__v num">${metres(r.position.x)}, ${metres(r.position.y)} m</span></div>
        ` : ""}
      </div>` : ""}

      <div class="panel__section">
        <h2 class="panel__title">Predicted conflicts</h2>
        ${(() => {
          const recs = store.decisionsFor(id).slice(-6).reverse();
          return recs.length
            ? recs.map((d) => decisionHtml(d, id)).join("")
            : `<div class="chain__note">No decision record for ${id} yet: predicted
               conflicts, Edge-AI predictions, proactive holds and task auctions appear
               here as they happen.</div>`;
        })()}
      </div>

      <div class="panel__section">
        <h2 class="panel__title">Movement intent</h2>
        ${r.movement_intent ? `
          <div class="kv"><span class="kv__k">Target</span><span class="kv__v num">${metres(r.movement_intent.target.x)}, ${metres(r.movement_intent.target.y)}</span></div>
          <div class="kv"><span class="kv__k">Waypoints</span><span class="kv__v num">${int((r.movement_intent.path || []).length)}</span></div>
          <div class="kv"><span class="kv__k">ETA</span><span class="kv__v num">${secs(r.movement_intent.eta)} s</span></div>
          <div class="kv"><span class="kv__k">Path version</span><span class="kv__v num">${int(r.movement_intent.path_version)}</span></div>
        ` : `<div class="empty"><div class="empty__cause">No movement intent published.</div>
             <div class="empty__action">The robot is idle or awaiting a task assignment.</div></div>`}
      </div>`;
  }
}
