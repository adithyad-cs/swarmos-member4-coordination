// SWARMOS real-browser UI audit (Chromium via Playwright).
//
//   PYTHONPATH=. python3 -m uvicorn app.api.server:app --port 8791 &   (server)
//   NODE_PATH=$(npm root -g) node tools/audit_browser.mjs http://127.0.0.1:8791
//
// Drives the actual pages and records PASS / FAIL per UI feature, plus every
// console error and uncaught page exception. Exit status 1 on any FAIL.
// ASCII-only comments by project rule.

import { createRequire } from "module";
import { execSync } from "child_process";

// ES modules ignore NODE_PATH, so resolve playwright locally first and then
// from the global npm root.
const require = createRequire(import.meta.url);
let pw;
try {
  pw = require("playwright");
} catch {
  const root = execSync("npm root -g").toString().trim();
  pw = require(root + "/playwright");
}
const { chromium } = pw;

const BASE = process.argv[2] || "http://127.0.0.1:8791";
const results = [];
const consoleErrors = [];
const pageErrors = [];

function record(name, ok, evidence = "") {
  results.push({ name, status: ok ? "PASS" : "FAIL", evidence });
}

async function step(name, fn) {
  try {
    const out = await fn();
    const [ok, ev] = Array.isArray(out) ? out : [Boolean(out), ""];
    record(name, ok, ev);
  } catch (err) {
    record(name, false, "EXCEPTION " + String(err && err.message || err).split("\n")[0]);
  }
}

async function api(path, body) {
  const res = await fetch(BASE + path, body === undefined ? {} : {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

async function canvasInk(page, id) {
  return page.evaluate((cid) => {
    const c = document.getElementById(cid);
    if (!c || !c.width || !c.height) return -1;
    const ctx = c.getContext("2d");
    const d = ctx.getImageData(0, 0, c.width, c.height).data;
    let n = 0;
    for (let i = 3; i < d.length; i += 4 * 7) if (d[i] > 0) n++;
    return n;
  }, id);
}

const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || undefined,
});
const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text()); });
page.on("pageerror", (e) => pageErrors.push(String(e && e.message || e)));

await api("/api/sim/stop", {});

// ---- landing ---------------------------------------------------------------
await step("landing: loads with title, status rows and ENTER button", async () => {
  await page.goto(BASE + "/", { waitUntil: "networkidle" });
  const title = await page.textContent("#lp-title");
  const enter = await page.isVisible("#lp-enter");
  await page.waitForTimeout(1500);
  const net = (await page.textContent("#lp-status-net-value")) || "";
  return [Boolean(title) && enter, `title="${(title || "").trim()}" net="${net.trim()}"`];
});

await step("landing: ENTER SWARMOS starts a run and opens the dashboard", async () => {
  await page.click("#lp-enter");
  await page.waitForURL(/index\.html/, { timeout: 15000 });
  await page.waitForFunction(() => {
    const t = document.getElementById("hdr-tick");
    return t && /\d/.test(t.textContent || "") && t.textContent.trim() !== "--";
  }, null, { timeout: 15000 });
  const st = await api("/api/status");
  return [st.status && st.status.running, `url=${page.url()} running=${st.status && st.status.running}`];
});

// ---- dashboard shell -------------------------------------------------------
await step("topbar: LINK live, scenario, seed, tick advancing", async () => {
  const t1 = Number((await page.textContent("#hdr-tick")).replace(/\D/g, ""));
  await page.waitForTimeout(1200);
  const t2 = Number((await page.textContent("#hdr-tick")).replace(/\D/g, ""));
  const link = (await page.textContent("#link-text")).trim();
  const scen = (await page.textContent("#hdr-scenario")).trim();
  return [t2 > t1 && /live/i.test(link), `tick ${t1}->${t2} link=${link} scenario=${scen}`];
});

await step("map: static layer, paths and robots are drawn (non-blank canvases)", async () => {
  await page.waitForTimeout(800);
  const s = await canvasInk(page, "layer-static");
  const r = await canvasInk(page, "layer-robots");
  const p = await canvasInk(page, "layer-paths");
  return [s > 100 && r > 10, `ink static=${s} robots=${r} paths=${p}`];
});

await step("map: zoom in / out / fit update the ZOOM readout", async () => {
  const z0 = (await page.textContent("#info-zoom")).trim();
  await page.click("#btn-zoom-in");
  await page.waitForTimeout(250);
  const z1 = (await page.textContent("#info-zoom")).trim();
  await page.click("#btn-zoom-fit");
  await page.waitForTimeout(250);
  const z2 = (await page.textContent("#info-zoom")).trim();
  await page.click("#btn-zoom-out");
  return [z1 !== z0 && z2.length > 0, `zoom ${z0} -> ${z1} -> fit ${z2}`];
});

await step("map: cursor readout shows world coordinates", async () => {
  const box = await page.locator("#map").boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.waitForTimeout(200);
  const txt = (await page.textContent("#info-cursor")).trim();
  return [/\d/.test(txt), `cursor="${txt}"`];
});

await step("KPI strip shows live numbers (no fake zeros before data)", async () => {
  const done = (await page.textContent("#kpi-tasks-complete")).trim();
  const col = (await page.textContent("#kpi-collisions")).trim();
  return [done.length > 0 && col.length > 0, `tasks=${done} collisions=${col}`];
});

// ---- tabs ------------------------------------------------------------------
async function openTab(name) {
  const shell = await page.getAttribute("#shell", "data-rail");
  if (shell !== "open") await page.click("#btn-rail-toggle");
  await page.click(`#tab-${name}`);
  await page.waitForTimeout(400);
}

await step("rail: toggle opens and closes the side panel", async () => {
  const a = await page.getAttribute("#shell", "data-rail");
  await page.click("#btn-rail-toggle");
  await page.waitForTimeout(200);
  const b = await page.getAttribute("#shell", "data-rail");
  await page.click("#btn-rail-toggle");
  await page.waitForTimeout(200);
  const c = await page.getAttribute("#shell", "data-rail");
  return [a !== b && a === c, `rail ${a} -> ${b} -> ${c}`];
});

await step("Fleet tab: roster lists robots; clicking selects one", async () => {
  await openTab("fleet");
  const rows = await page.locator("#roster .roster__row").count();
  await page.locator("#roster .roster__row").first().click();
  await page.waitForTimeout(300);
  const sel = await page.evaluate(() => {
    const r = document.querySelector("#roster .roster__row[data-selected='true']");
    return r ? r.dataset.id : null;
  });
  return [rows > 0 && Boolean(sel), `rows=${rows} selected=${sel}`];
});

await step("Inspector tab: verdict, decision chain, state, predicted conflicts", async () => {
  await openTab("inspector");
  await page.waitForTimeout(600);
  const txt = await page.textContent("#panel-inspector");
  const ok = /Decision chain/.test(txt) && /Predicted conflicts/.test(txt) && /Status/.test(txt);
  return [ok, txt.replace(/\s+/g, " ").slice(0, 160)];
});

await step("Analytics tab: safety invariants block + four charts", async () => {
  await openTab("analytics");
  await page.waitForTimeout(1200);
  const txt = await page.textContent("#panel-analytics");
  const charts = await page.locator("#panel-analytics canvas").count();
  const ok = /Safety invariants/.test(txt) && /INV-1/.test(txt) && /PASS|FAIL/.test(txt) && charts >= 4;
  return [ok, `charts=${charts} verdict=${(txt.match(/Verdict\s*(PASS|FAIL|--)/) || [""])[0]}`];
});

// ---- Lab -------------------------------------------------------------------
await step("Lab tab: scenario list includes batch + demo scenarios", async () => {
  await openTab("lab");
  const opts = await page.$$eval("#lab-scenario option", (os) => os.map((o) => o.value));
  const ok = ["rush_50", "overlap_batch", "corridor_demo"].every((s) => opts.includes(s))
    && !opts.some((v) => /object/.test(v));
  return [ok, `options=${opts.join(",")}`];
});

await step("Lab: start corridor_demo, pause, step, resume, stop", async () => {
  await page.selectOption("#lab-scenario", "corridor_demo");
  await page.click("#lab-start");
  await page.waitForTimeout(1500);
  const s1 = await api("/api/status");
  await page.click("#lab-pause");
  await page.waitForTimeout(400);
  const s2 = await api("/api/status");
  const tickA = s2.status.tick;
  await page.click("#lab-step");
  await page.waitForTimeout(400);
  const s3 = await api("/api/status");
  await page.click("#lab-pause");
  await page.waitForTimeout(600);
  const s4 = await api("/api/status");
  const ok = s1.status.running && s1.status.config.scenario === "corridor_demo"
    && !s2.status.running && s3.status.tick === tickA + 1 && s4.status.running;
  return [ok, `running=${s1.status.running} paused=${!s2.status.running} step ${tickA}->${s3.status.tick} resumed=${s4.status.running}`];
});

for (const fault of ["robot_failure", "comm_blackout", "link_impair", "blocked_aisle", "rogue_agent"]) {
  await step(`Lab: inject ${fault} with a robot selected`, async () => {
    await openTab("fleet");
    await page.locator("#roster .roster__row").nth(1).click();
    await openTab("lab");
    await page.selectOption("#lab-fault", fault);
    const before = consoleErrors.length;
    const resp = page.waitForResponse((r) => r.url().includes("/api/sim/inject"), { timeout: 5000 });
    await page.click("#lab-inject");
    const body = await (await resp).json();
    await page.waitForTimeout(300);
    const banner = await page.getAttribute("#banner", "data-visible");
    return [body.ok === true && consoleErrors.length === before && banner !== "true",
      `ok=${body.ok} ${body.error || ""} ignored=${JSON.stringify(body.ignored_params || [])} error_banner=${banner === "true"}`];
  });
}

await step("Lab: determinism receipt (capture + compare) produces hashes", async () => {
  await page.click("#lab-pause");
  await page.waitForTimeout(300);
  await page.click("#lab-capture");
  await page.waitForTimeout(500);
  await page.click("#lab-compare");
  await page.waitForTimeout(500);
  const txt = (await page.textContent("#lab-hashes")) || "";
  return [/[0-9a-f]{6,}/i.test(txt), txt.replace(/\s+/g, " ").slice(0, 120)];
});

await step("Lab: stop ends the run", async () => {
  await page.click("#lab-stop");
  await page.waitForTimeout(600);
  const st = await api("/api/status");
  return [!st.status.running, `running=${st.status.running}`];
});

await step("Lab: advanced intelligence run shows live Edge-AI, pre-hold and auction evidence in Analytics", async () => {
  await openTab("lab");
  await page.selectOption("#lab-scenario", "overlap_batch");
  await page.selectOption("#lab-advanced", "on");
  await page.click("#lab-start");
  await page.waitForTimeout(6000);
  const st = await api("/api/status");
  await openTab("analytics");
  await page.waitForTimeout(1200);
  const txt = ((await page.textContent("#advanced-block")) || "").replace(/\s+/g, " ");
  const calls = Number((txt.match(/Predictions \/ positives\s*(\d+)/) || [0, 0])[1]);
  const auctions = Number((txt.match(/Auctions opened \/ re-auctions\s*(\d+)/) || [0, 0])[1]);
  await openTab("lab");
  await page.click("#lab-stop");
  await page.waitForTimeout(400);
  await page.selectOption("#lab-advanced", "off");
  const ok = st.status.config.advanced === true && /EDGE_AI ON/.test(txt) && /AUCTION ON/.test(txt)
    && /edge-conflict-v1/.test(txt) && /Edge AI status\s*ok/.test(txt) && calls > 0 && auctions > 0;
  return [ok, `advanced=${st.status.config.advanced} calls=${calls} auctions=${auctions} ${txt.slice(0, 140)}`];
});

// ---- Compare ---------------------------------------------------------------
await step("Compare tab: start co-simulation, both arms stream, every fault button works", async () => {
  await openTab("cosim");
  await page.click("#panel-cosim [data-act='start']");
  await page.waitForTimeout(2500);
  const st = await api("/api/cosim/status");
  const buttons = await page.$$eval("#panel-cosim [data-act='inject']", (bs) => bs.map((b) => b.dataset.fault));
  const results2 = [];
  for (const f of buttons) {
    const resp = page.waitForResponse((r) => r.url().includes("/api/cosim/inject"), { timeout: 5000 });
    await page.click(`#panel-cosim [data-act='inject'][data-fault='${f}']`);
    results2.push([f, (await (await resp).json()).ok]);
  }
  await page.click("#panel-cosim [data-act='stop']");
  const ok = st.running && results2.length >= 5 && results2.every(([, o]) => o === true);
  return [ok, `running=${st.running} faults=${JSON.stringify(results2)}`];
});

await step("Compare tab: SwarmOS arm shows the PRODUCT configuration, reference arm the C2 reference", async () => {
  await openTab("cosim");
  await page.click("#panel-cosim [data-act='start']");
  await page.waitForTimeout(2000);
  const st = await api("/api/cosim/status");
  const shownT = await page.textContent("#panel-cosim [data-cosim-config='swarmos']").catch(() => null);
  const shownB = await page.textContent("#panel-cosim [data-cosim-config='baseline']").catch(() => null);
  await page.click("#panel-cosim [data-act='stop']");
  const cfg = st.policy_config || {};
  const fixesT = ((cfg.swarmos || {}).fixes || []).join(" + ");
  const ok = fixesT === "F1 + F3 + F5 + F6"
    && (cfg.baseline || {}).reference === "stop_and_wait+F1+F6"
    && !!shownT && shownT.includes("F1 + F3 + F5 + F6")
    && !!shownB && shownB.includes("stop_and_wait+F1+F6");
  return [ok, `server swarmos=${fixesT} baseline=${(cfg.baseline || {}).reference} | shown: "${shownT}" / "${shownB}"`];
});

// ---- palette + keyboard ----------------------------------------------------
await step("command palette: Ctrl+K opens, lists commands, Esc closes", async () => {
  await page.keyboard.press("Control+k");
  await page.waitForTimeout(300);
  const open = await page.isVisible("#palette-input");
  const items = await page.locator("#palette-list > *").count();
  await page.keyboard.press("Escape");
  await page.waitForTimeout(200);
  const closed = !(await page.isVisible("#palette-input"));
  return [open && items > 0 && closed, `open=${open} items=${items} closed=${closed}`];
});

await step("keyboard: 0 (fit) and R bound without errors", async () => {
  await page.click("#map");
  const before = pageErrors.length;
  await page.keyboard.press("0");
  await page.keyboard.press("r");
  await page.waitForTimeout(300);
  return [pageErrors.length === before, `page errors unchanged (${pageErrors.length})`];
});

// ---- reconnect -------------------------------------------------------------
await step("reconnect: dashboard reload keeps working after stop/start", async () => {
  await api("/api/sim/start", { scenario: "rush_50", seed: 11, fleet_size: 8 });
  await page.reload({ waitUntil: "networkidle" });
  await page.waitForTimeout(2000);
  const link = (await page.textContent("#link-text")).trim();
  const ink = await canvasInk(page, "layer-robots");
  await api("/api/sim/stop", {});
  return [/live/i.test(link) && ink > 10, `link=${link} robot ink=${ink}`];
});

await step("no uncaught page exceptions during the whole session", async () =>
  [pageErrors.length === 0, pageErrors.slice(0, 3).join(" | ")]);
await step("no console errors during the whole session", async () =>
  [consoleErrors.length === 0, consoleErrors.slice(0, 3).join(" | ")]);

await browser.close();

let fails = 0;
for (const r of results) {
  if (r.status === "FAIL") fails++;
  console.log(`${r.status}  ${r.name}  ${r.evidence}`);
}
console.log("-".repeat(78));
console.log(`${results.length - fails} pass, ${fails} FAIL`);
process.exit(fails ? 1 : 0);
