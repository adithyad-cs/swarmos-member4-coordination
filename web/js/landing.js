// ---------------------------------------------------------------------------
// landing.js  STATE 1 behaviour for the ROBONEX landing page.
//
// Scope, deliberately narrow:
//   1. report server reachability and run state honestly (no invented values);
//   2. on ENTER SWARMOS, start the real simulation and navigate to the real
//      dashboard at index.html.
//
// It imports nothing from the dashboard and the dashboard imports nothing from
// here, so the simulation product cannot be affected by this file.
// ---------------------------------------------------------------------------

"use strict";

// Entry configuration. Kept identical to the demo defaults in run.sh so the
// landing button and the scripted demo enter the same simulation.
const ENTRY = Object.freeze({
  scenario: "rush_50",
  seed: 11,
  fleet_size: 8,
  policy: "swarmos",
  speed: 1.0,
});

const DASH = "--";
const DASHBOARD_URL = "index.html";
const TRANSITION_MS = 180;
const STATUS_POLL_MS = 4000;

const els = {
  body: document.body,
  fleetRow: document.getElementById("lp-status-fleet"),
  fleetVal: document.getElementById("lp-status-fleet-value"),
  netRow: document.getElementById("lp-status-net"),
  netVal: document.getElementById("lp-status-net-value"),
  enter: document.getElementById("lp-enter"),
  note: document.getElementById("lp-cta-note"),
};

// --------------------------------------------------------------------- status

function setRow(row, valueEl, dotState, text) {
  if (!row || !valueEl) return;
  const dot = row.querySelector(".lp-dot");
  if (dot) dot.setAttribute("data-state", dotState);
  row.setAttribute("data-state", dotState);
  valueEl.textContent = text;
}

// Reachability is the only thing this page can honestly assert about the
// network, so that is exactly what the AMR NETWORK row reports.
function renderUnreachable() {
  setRow(els.fleetRow, els.fleetVal, "unknown", DASH);
  setRow(els.netRow, els.netVal, "down", "UNREACHABLE");
}

function renderStatus(status) {
  setRow(els.netRow, els.netVal, "ok", "ONLINE");

  if (!status || typeof status !== "object") {
    setRow(els.fleetRow, els.fleetVal, "unknown", DASH);
    return;
  }
  if (status.running === true) {
    setRow(els.fleetRow, els.fleetVal, "ok", "LIVE");
  } else if (status.has_run === true) {
    setRow(els.fleetRow, els.fleetVal, "warn", "PAUSED");
  } else {
    setRow(els.fleetRow, els.fleetVal, "ok", "READY");
  }
}

async function pollStatus() {
  try {
    const res = await fetch("api/status", { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const body = await res.json();
    renderStatus(body && body.status);
  } catch (err) {
    renderUnreachable();
  }
}

// ------------------------------------------------------------------ cta entry

function note(text, state) {
  if (!els.note) return;
  els.note.textContent = text || "";
  if (state) els.note.setAttribute("data-state", state);
  else els.note.removeAttribute("data-state");
}

function reducedMotion() {
  return (
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

function navigate() {
  if (reducedMotion()) {
    window.location.href = DASHBOARD_URL;
    return;
  }
  els.body.setAttribute("data-state", "entering");
  window.setTimeout(function () {
    window.location.href = DASHBOARD_URL;
  }, TRANSITION_MS);
}

async function enterSwarmos() {
  if (!els.enter || els.enter.disabled) return;
  els.enter.disabled = true;
  note("STARTING SIMULATION");

  try {
    const res = await fetch("api/sim/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(ENTRY),
    });
    const body = await res.json().catch(function () {
      return null;
    });
    if (!res.ok || !body || body.ok !== true) {
      const why = (body && (body.error || body.detail)) || "HTTP " + res.status;
      note("COULD NOT START: " + String(why).toUpperCase(), "error");
      els.enter.disabled = false;
      return;
    }
  } catch (err) {
    // The dashboard is still reachable and can start a run itself, but saying
    // so falsely would be worse than reporting the failure we actually saw.
    note("SERVER UNREACHABLE", "error");
    els.enter.disabled = false;
    return;
  }

  note("ENTERING");
  navigate();
}

// ---------------------------------------------------------------------- wiring

if (els.enter) {
  els.enter.addEventListener("click", enterSwarmos);
}

// Keyboard-first: Enter anywhere on the page enters the product, unless the
// user is focused on something else interactive.
document.addEventListener("keydown", function (ev) {
  if (ev.key !== "Enter" || ev.metaKey || ev.ctrlKey || ev.altKey) return;
  const active = document.activeElement;
  if (active && active !== document.body && active !== els.enter) return;
  ev.preventDefault();
  enterSwarmos();
});

pollStatus();
window.setInterval(pollStatus, STATUS_POLL_MS);
