/* Live Map: layered Canvas 2D renderer.
 *
 * Performance contract: 60 fps with 50 robots, no framework, no build step.
 * How it is met:
 *
 *  - FOUR layers, repainted at different rates. Floor, grid, racks and aisle
 *    labels go on the STATIC layer, painted only when the viewport changes.
 *    Paths and reservations go on the PATHS layer, painted only when a path
 *    version changes. Only the ROBOT layer is painted per frame, and it draws
 *    at most ~50 circles. Redrawing 400 rack rectangles 60 times a second is
 *    the mistake this structure exists to prevent.
 *
 *  - Level of detail. Below 0.6 zoom a robot is a 4 px dot: no heading wedge,
 *    no id label, no footprint ring. At that scale those marks are illegible
 *    anyway, so drawing them costs frames and buys nothing.
 *
 *  - Trails are drawn for the SELECTED robot only. Fifty overlapping trails is
 *    not a visualisation, it is a smear.
 *
 *  - Interpolation between ticks. State arrives at 10 Hz but we paint at 60 Hz,
 *    so positions are interpolated toward the latest state. This is PRESENTATION
 *    ONLY: the store keeps the authoritative value, and every number in the UI
 *    comes from the store, never from an interpolated pixel. Law 1 is intact.
 *
 * Coordinate system: continuous metres, 0 = +X, y grows upward in world space
 * and is flipped on screen so the map reads like a floor plan.
 */

import { store } from "./store.js";

const TICK_MS = 100;              // 10 Hz, frozen convention
const ROBOT_RADIUS_M = 0.35;      // frozen convention
const FOOTPRINT_M = 0.70;         // pair footprint = collision distance
const LOD_ZOOM = 0.6;             // below this, robots are plain dots
const LABEL_ZOOM = 1.1;           // below this, no per-robot id labels
const PULSE_MS = 400;             // one pulse at conflict birth, then static
const TRAIL_MAX = 120;            // 12 s of trail for the selected robot
const GHOST_ALPHA = 0.30;         // baseline arm: present but never competing

function css(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

const STATE_COLOR = {};
function loadColors() {
  STATE_COLOR.MOVING = css("--state-moving");
  STATE_COLOR.BLOCKED = css("--state-blocked");
  STATE_COLOR.WAITING = css("--state-waiting");
  STATE_COLOR.CHARGING = css("--state-charging");
  STATE_COLOR.AVAILABLE = css("--state-available");
  STATE_COLOR.FAILED = css("--state-failed");
  STATE_COLOR.QUARANTINED = css("--state-quarantined");
}

export class MapView {
  constructor(root) {
    this.root = root;
    this.staticCv = root.querySelector("#layer-static");
    this.pathsCv = root.querySelector("#layer-paths");
    this.robotsCv = root.querySelector("#layer-robots");
    this.hitCv = root.querySelector("#layer-hit");

    this.sctx = this.staticCv.getContext("2d");
    this.pctx = this.pathsCv.getContext("2d");
    this.rctx = this.robotsCv.getContext("2d");

    this.dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.w = 0;
    this.h = 0;

    // View transform: world metres -> screen pixels.
    this.zoom = 1.0;         // pixels per metre, scaled by fitScale
    this.fitScale = 20;      // px per metre at zoom 1
    this.panX = 0;
    this.panY = 0;

    this.hidden = new Set();          // states muted via the legend
    this.trail = [];                  // selected robot's recent positions
    this.trailFor = null;
    this.pulses = new Map();          // conflictId -> started-at ms

    /* Baseline ghost overlay (X-12). A function returning
     * {robots, at} or null. Null means draw nothing, which is what an
     * unstarted or non-comparable co-simulation must look like. */
    this.ghostSource = null;

    this.lastFrameTick = -1;
    this.lastFrameAt = 0;
    this.fps = 0;
    this._fpsSamples = [];
    this._rafId = null;
    this._pathsDirty = true;
    this._staticDirty = true;

    loadColors();
    this._bindEvents();
    this.resize();
  }

  /* -------------------------------------------------------- transform ---- */

  scale() {
    return this.fitScale * this.zoom;
  }

  toScreen(x, y) {
    const s = this.scale();
    return [x * s + this.panX, this.h - (y * s + this.panY)];
  }

  toWorld(px, py) {
    const s = this.scale();
    return [(px - this.panX) / s, (this.h - py - this.panY) / s];
  }

  fit() {
    const wh = store.warehouse;
    if (!wh || !wh.width_m || !wh.height_m) return;
    const pad = 24;
    const sx = (this.w - pad * 2) / wh.width_m;
    const sy = (this.h - pad * 2) / wh.height_m;
    this.fitScale = Math.min(sx, sy);
    this.zoom = 1.0;
    this.panX = (this.w - wh.width_m * this.fitScale) / 2;
    this.panY = (this.h - wh.height_m * this.fitScale) / 2;
    this._staticDirty = true;
    this._pathsDirty = true;
  }

  zoomBy(factor, cx, cy) {
    const px = cx ?? this.w / 2;
    const py = cy ?? this.h / 2;
    const [wx, wy] = this.toWorld(px, py);
    this.zoom = Math.max(0.25, Math.min(6, this.zoom * factor));
    // Keep the point under the cursor fixed -- zoom that drifts feels broken.
    const s = this.scale();
    this.panX = px - wx * s;
    this.panY = this.h - py - wy * s;
    this._staticDirty = true;
    this._pathsDirty = true;
  }

  resize() {
    const rect = this.root.getBoundingClientRect();
    this.w = Math.max(1, Math.floor(rect.width));
    this.h = Math.max(1, Math.floor(rect.height));
    for (const cv of [this.staticCv, this.pathsCv, this.robotsCv, this.hitCv]) {
      cv.width = Math.floor(this.w * this.dpr);
      cv.height = Math.floor(this.h * this.dpr);
    }
    for (const ctx of [this.sctx, this.pctx, this.rctx]) {
      ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    }
    if (store.warehouse) this.fit();
    this._staticDirty = true;
    this._pathsDirty = true;
  }

  /* ----------------------------------------------------------- events ---- */

  _bindEvents() {
    let dragging = false;
    let lastX = 0;
    let lastY = 0;

    this.hitCv.addEventListener("mousedown", (e) => {
      dragging = true;
      lastX = e.offsetX;
      lastY = e.offsetY;
    });

    window.addEventListener("mouseup", () => { dragging = false; });

    this.hitCv.addEventListener("mousemove", (e) => {
      if (dragging) {
        this.panX += e.offsetX - lastX;
        this.panY -= e.offsetY - lastY;
        lastX = e.offsetX;
        lastY = e.offsetY;
        this._staticDirty = true;
        this._pathsDirty = true;
      }
      this.cursor = this.toWorld(e.offsetX, e.offsetY);
      this.hover = this._pick(e.offsetX, e.offsetY);
      this.hitCv.style.cursor = this.hover ? "pointer" : (dragging ? "grabbing" : "crosshair");
    });

    this.hitCv.addEventListener("mouseleave", () => {
      this.cursor = null;
      this.hover = null;
    });

    this.hitCv.addEventListener("click", (e) => {
      const hit = this._pick(e.offsetX, e.offsetY);
      // Clicking empty floor clears the selection: an inspector stuck on a
      // robot the operator is no longer looking at is worse than no inspector.
      store.select(hit ? hit.robot_id : null);
    });

    this.hitCv.addEventListener("wheel", (e) => {
      e.preventDefault();
      this.zoomBy(e.deltaY < 0 ? 1.12 : 1 / 1.12, e.offsetX, e.offsetY);
    }, { passive: false });

    // Keyboard panning so the map is usable without a mouse.
    this.hitCv.addEventListener("keydown", (e) => {
      const step = e.shiftKey ? 80 : 24;
      const moves = {
        ArrowLeft: [step, 0], ArrowRight: [-step, 0],
        ArrowUp: [0, -step], ArrowDown: [0, step],
      };
      if (moves[e.key]) {
        e.preventDefault();
        this.panX += moves[e.key][0];
        this.panY += moves[e.key][1];
        this._staticDirty = true;
        this._pathsDirty = true;
      } else if (e.key === "+" || e.key === "=") {
        this.zoomBy(1.2);
      } else if (e.key === "-") {
        this.zoomBy(1 / 1.2);
      } else if (e.key === "0") {
        this.fit();
      }
    });

    window.addEventListener("resize", () => this.resize());
  }

  _pick(px, py) {
    const [wx, wy] = this.toWorld(px, py);
    const tol = Math.max(ROBOT_RADIUS_M, 14 / this.scale());
    let best = null;
    let bestD = Infinity;
    for (const r of store.robots.values()) {
      if (this.hidden.has(r.status)) continue;
      const dx = r.position.x - wx;
      const dy = r.position.y - wy;
      const d = Math.hypot(dx, dy);
      if (d < tol && d < bestD) { best = r; bestD = d; }
    }
    return best;
  }

  toggleState(state) {
    if (this.hidden.has(state)) this.hidden.delete(state);
    else this.hidden.add(state);
    this._pathsDirty = true;
  }

  /* ------------------------------------------------------- static layer -- */

  drawStatic() {
    const ctx = this.sctx;
    const wh = store.warehouse;
    ctx.clearRect(0, 0, this.w, this.h);
    if (!wh) return;

    const s = this.scale();

    // Floor
    const [x0, y0] = this.toScreen(0, wh.height_m);
    ctx.fillStyle = css("--map-floor");
    ctx.fillRect(x0, y0, wh.width_m * s, wh.height_m * s);

    // Grid at the 1 m aisle pitch, with a major line every 5 m. Below 8 px per
    // metre the minor grid becomes moire, so it is dropped.
    if (s >= 8) {
      ctx.lineWidth = 1;
      for (let gx = 0; gx <= wh.width_m; gx += 1) {
        const major = gx % 5 === 0;
        if (!major && s < 14) continue;
        ctx.strokeStyle = major ? css("--map-grid-major") : css("--map-grid");
        const [sx, sy1] = this.toScreen(gx, 0);
        const [, sy2] = this.toScreen(gx, wh.height_m);
        ctx.beginPath();
        ctx.moveTo(Math.round(sx) + 0.5, sy1);
        ctx.lineTo(Math.round(sx) + 0.5, sy2);
        ctx.stroke();
      }
      for (let gy = 0; gy <= wh.height_m; gy += 1) {
        const major = gy % 5 === 0;
        if (!major && s < 14) continue;
        ctx.strokeStyle = major ? css("--map-grid-major") : css("--map-grid");
        const [sx1, sy] = this.toScreen(0, gy);
        const [sx2] = this.toScreen(wh.width_m, gy);
        ctx.beginPath();
        ctx.moveTo(sx1, Math.round(sy) + 0.5);
        ctx.lineTo(sx2, Math.round(sy) + 0.5);
        ctx.stroke();
      }
    }

    // Racks (obstacles). Sent as [x, y, w, h] in metres.
    if (Array.isArray(wh.racks)) {
      ctx.fillStyle = css("--map-rack");
      ctx.strokeStyle = css("--map-rack-edge");
      ctx.lineWidth = 1;
      for (const rk of wh.racks) {
        const [rx, ry, rw, rh] = rk;
        const [sx, sy] = this.toScreen(rx, ry + rh);
        ctx.fillRect(sx, sy, rw * s, rh * s);
        if (s >= 6) ctx.strokeRect(sx, sy, rw * s, rh * s);
      }
    }

    // Charging docks, if the scenario declares them.
    if (Array.isArray(wh.docks) && s >= 10) {
      ctx.strokeStyle = css("--state-charging");
      ctx.lineWidth = 1.5;
      for (const d of wh.docks) {
        const [sx, sy] = this.toScreen(d[0], d[1]);
        ctx.beginPath();
        ctx.arc(sx, sy, 0.45 * s, 0, Math.PI * 2);
        ctx.stroke();
      }
    }

    // Warehouse boundary
    ctx.strokeStyle = css("--line-default");
    ctx.lineWidth = 1;
    ctx.strokeRect(x0, y0, wh.width_m * s, wh.height_m * s);

    this._staticDirty = false;
  }

  /* -------------------------------------------------------- paths layer -- */

  drawPaths() {
    const ctx = this.pctx;
    ctx.clearRect(0, 0, this.w, this.h);
    const s = this.scale();
    if (this.zoom < LOD_ZOOM) { this._pathsDirty = false; return; }

    const sel = store.selectedRobot;

    for (const r of store.robots.values()) {
      if (this.hidden.has(r.status)) continue;
      const mi = r.movement_intent;
      if (!mi || !Array.isArray(mi.path) || mi.path.length < 2) continue;

      const isSel = r.robot_id === sel;
      ctx.strokeStyle = isSel ? css("--map-path-active") : css("--map-path");
      ctx.lineWidth = isSel ? 2 : 1;
      ctx.beginPath();
      for (let i = 0; i < mi.path.length; i += 1) {
        const p = mi.path[i];
        const [sx, sy] = this.toScreen(p.x ?? p[0], p.y ?? p[1]);
        if (i === 0) ctx.moveTo(sx, sy);
        else ctx.lineTo(sx, sy);
      }
      ctx.stroke();

      // Goal marker, drawn only for the selected robot to keep the map calm.
      if (isSel && mi.target) {
        const [gx, gy] = this.toScreen(mi.target.x, mi.target.y);
        ctx.strokeStyle = css("--map-goal");
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(gx - 5, gy); ctx.lineTo(gx + 5, gy);
        ctx.moveTo(gx, gy - 5); ctx.lineTo(gx, gy + 5);
        ctx.stroke();
      }
    }

    // Trail for the selected robot only.
    if (this.trail.length > 1) {
      ctx.strokeStyle = css("--map-trail");
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let i = 0; i < this.trail.length; i += 1) {
        const [sx, sy] = this.toScreen(this.trail[i][0], this.trail[i][1]);
        if (i === 0) ctx.moveTo(sx, sy);
        else ctx.lineTo(sx, sy);
      }
      ctx.stroke();
    }

    this._pathsDirty = false;
  }

  /* ------------------------------------------------------- robots layer -- */

  /* Baseline ghosts (X-12). Drawn FIRST so the real fleet is always on top,
   * and drawn in tertiary ink at low alpha so they read as "the other world"
   * rather than as robots. No state colour, no labels, no selection ring: the
   * ghosts are context, not subjects. */
  _drawGhosts(ctx, now, s) {
    if (!this.ghostSource) return;
    const src = this.ghostSource();
    if (!src || !src.robots || !src.robots.length) return;

    const age = now - (src.at || 0);
    const t = Math.max(0, Math.min(1, age / TICK_MS));
    const lod = this.zoom < LOD_ZOOM;
    const rpx = Math.max(2, ROBOT_RADIUS_M * s);

    ctx.save();
    ctx.globalAlpha = GHOST_ALPHA;
    ctx.strokeStyle = css("--ink-tertiary");
    ctx.fillStyle = css("--ink-tertiary");
    ctx.lineWidth = 1;

    for (const r of src.robots) {
      const prev = r.prevPosition || r.position;
      const ix = prev.x + (r.position.x - prev.x) * t;
      const iy = prev.y + (r.position.y - prev.y) * t;
      const [sx, sy] = this.toScreen(ix, iy);
      if (sx < -20 || sy < -20 || sx > this.w + 20 || sy > this.h + 20) continue;

      ctx.beginPath();
      ctx.arc(sx, sy, lod ? 2 : rpx, 0, Math.PI * 2);
      if (lod) ctx.fill();
      else ctx.stroke();
    }

    ctx.restore();
  }

  drawRobots(now) {
    const ctx = this.rctx;
    ctx.clearRect(0, 0, this.w, this.h);
    const s = this.scale();
    const lod = this.zoom < LOD_ZOOM;

    // Ghosts first: the counterfactual never occludes the real fleet.
    this._drawGhosts(ctx, now, s);

    // Interpolation factor. PRESENTATION ONLY -- see the file header.
    const age = now - this.lastFrameAt;
    const t = Math.max(0, Math.min(1, age / TICK_MS));

    const sel = store.selectedRobot;

    for (const r of store.robots.values()) {
      if (this.hidden.has(r.status)) continue;

      const prev = r.prevPosition || r.position;
      const ix = prev.x + (r.position.x - prev.x) * t;
      const iy = prev.y + (r.position.y - prev.y) * t;
      const [sx, sy] = this.toScreen(ix, iy);

      // Cull offscreen robots: at high zoom most of the fleet is not visible.
      if (sx < -20 || sy < -20 || sx > this.w + 20 || sy > this.h + 20) continue;

      const color = STATE_COLOR[r.status] || STATE_COLOR.MOVING;

      if (lod) {
        // Level of detail: a 4 px dot, nothing else.
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(sx, sy, 2, 0, Math.PI * 2);
        ctx.fill();
        continue;
      }

      const rpx = Math.max(3, ROBOT_RADIUS_M * s);

      // Safety footprint ring, only for states where separation is the story.
      if (r.status === "BLOCKED" || r.status === "WAITING") {
        ctx.strokeStyle = color;
        ctx.globalAlpha = 0.28;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(sx, sy, (FOOTPRINT_M / 2) * s, 0, Math.PI * 2);
        ctx.stroke();
        ctx.globalAlpha = 1;
      }

      // Body. AVAILABLE is outline-only: an idle robot should not draw the eye.
      ctx.beginPath();
      ctx.arc(sx, sy, rpx, 0, Math.PI * 2);
      if (r.status === "AVAILABLE") {
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      } else {
        ctx.fillStyle = color;
        ctx.fill();
      }

      // The lie, drawn. A rogue robot's claimed position is shown as a
      // hollow ring tied to its real body by a dashed line: the gap IS the
      // evidence, and its length is the error the quorum voted on.
      if (r.claimed) {
        const [cx, cy] = this.toScreen(r.claimed.x, r.claimed.y);
        ctx.strokeStyle = STATE_COLOR.QUARANTINED || color;
        ctx.globalAlpha = 0.75;
        ctx.setLineDash([3, 3]);
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.lineTo(cx, cy);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.beginPath();
        ctx.arc(cx, cy, rpx, 0, Math.PI * 2);
        ctx.stroke();
        ctx.globalAlpha = 1;
      }

      // Heading wedge. Only when moving -- a heading on a stopped robot is
      // noise, and FAILED robots have no meaningful heading at all.
      if (r.status !== "FAILED" && r.velocity > 0.01 && rpx >= 4) {
        const hx = sx + Math.cos(r.heading) * rpx * 1.9;
        const hy = sy - Math.sin(r.heading) * rpx * 1.9;
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.lineTo(hx, hy);
        ctx.stroke();
      }

      // Selection ring
      if (r.robot_id === sel) {
        ctx.strokeStyle = css("--ink-primary");
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(sx, sy, rpx + 4, 0, Math.PI * 2);
        ctx.stroke();
      }

      // Id label, only when there is room to read it.
      if (this.zoom >= LABEL_ZOOM) {
        ctx.fillStyle = css("--ink-tertiary");
        ctx.font = `10px ${css("--font-mono") || "monospace"}`;
        ctx.textAlign = "center";
        ctx.fillText(r.robot_id, sx, sy - rpx - 5);
      }
    }

    this._drawConflicts(ctx, now, s);
    this._drawHover(ctx);
  }

  /* A conflict pulses ONCE at birth for 400 ms, then holds a static 2 px ring.
   * Continuous animation trains the eye to ignore the map. */
  _drawConflicts(ctx, now, s) {
    const live = new Set();
    for (const c of store.conflicts) {
      const id = c.conflict_id || `${c.a}-${c.b}`;
      live.add(id);
      if (!this.pulses.has(id)) this.pulses.set(id, now);

      const at = c.at || c.position;
      if (!at) continue;
      const [sx, sy] = this.toScreen(at.x, at.y);
      const elapsed = now - this.pulses.get(id);

      ctx.strokeStyle = css("--map-conflict-ring");
      if (elapsed < PULSE_MS) {
        const k = elapsed / PULSE_MS;
        ctx.globalAlpha = 1 - k;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(sx, sy, (0.4 + k * 1.4) * s, 0, Math.PI * 2);
        ctx.stroke();
        ctx.globalAlpha = 1;
      }
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(sx, sy, 0.55 * s, 0, Math.PI * 2);
      ctx.stroke();
    }
    // Forget resolved conflicts so a long run cannot leak this map.
    for (const id of [...this.pulses.keys()]) {
      if (!live.has(id)) this.pulses.delete(id);
    }
  }

  _drawHover(ctx) {
    if (!this.hover) return;
    const r = store.robot(this.hover.robot_id);
    if (!r) return;
    const [sx, sy] = this.toScreen(r.position.x, r.position.y);
    ctx.strokeStyle = css("--ink-secondary");
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(sx, sy, Math.max(6, ROBOT_RADIUS_M * this.scale() + 7), 0, Math.PI * 2);
    ctx.stroke();
  }

  /* ------------------------------------------------------------- loop ---- */

  onFrame() {
    // Called by main.js when a new tick lands.
    if (store.tick !== this.lastFrameTick) {
      this.lastFrameTick = store.tick;
      this.lastFrameAt = performance.now();
    }
    if (!store.warehouse) return;
    if (this._staticDirty) this.drawStatic();

    const sel = store.selectedRobot;
    if (sel !== this.trailFor) {
      this.trail = [];
      this.trailFor = sel;
    }
    if (sel) {
      const r = store.robot(sel);
      if (r) {
        this.trail.push([r.position.x, r.position.y]);
        if (this.trail.length > TRAIL_MAX) this.trail.shift();
      }
    }
    this._pathsDirty = true;
  }

  start() {
    const loop = () => {
      const now = performance.now();
      if (this._staticDirty) this.drawStatic();
      if (this._pathsDirty) this.drawPaths();
      this.drawRobots(now);
      this._sampleFps(now);
      this._rafId = requestAnimationFrame(loop);
    };
    this._rafId = requestAnimationFrame(loop);
  }

  stop() {
    if (this._rafId) cancelAnimationFrame(this._rafId);
    this._rafId = null;
  }

  _sampleFps(now) {
    this._fpsSamples.push(now);
    while (this._fpsSamples.length && now - this._fpsSamples[0] > 1000) {
      this._fpsSamples.shift();
    }
    this.fps = this._fpsSamples.length;
  }
}
