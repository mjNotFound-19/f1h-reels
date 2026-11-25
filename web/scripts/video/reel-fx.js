// The f1.h reel's effects: start lights, slams, kinetic letters, team-colour wipes, speed streaks, light sweeps,
// and scenes with a slow camera push. Each one also drops its cue for the soundtrack.
import { tw, cue, h, BEAT } from "./reel-engine.js";

export const stage = document.getElementById("stage");
const fx = h("div", { class: "fxlayer" });                 // above every scene: flashes, wipes, streaks
stage.append(fx);

// a scene from t0 to t1: hard cut in (a small scale-and-blur settle), a slow push-in while it holds, cut out
export function scene(cls, t0, t1, ...kids) {
  const cam = h("div", { class: "cam" }, ...kids), s = h("section", { class: `scene ${cls}` }, cam);
  stage.insertBefore(s, fx);
  tw(s, t0, 0.001, { o: 0 }, { o: 1 }); tw(s, t1, 0.001, { o: 1 }, { o: 0 });
  tw(cam, t0, 0.4, { s: 1.06, blur: 10 }, { s: 1.0, blur: 0 }, "out5");
  tw(cam, t0 + 0.4, t1 - t0 - 0.4, { s: 1.0 }, { s: 1.045 }, "lin");
  return s;
}

// kinetic type: the letters rise and sharpen one after another
export function letters(text, t0, cls = "", { stagger = 0.028, dy = 70, d = 0.5 } = {}) {
  const el = h("div", { class: `letters ${cls}` });
  [...text].forEach((c, i) => {
    const sp = h("span", {}, c === " " ? " " : c);
    el.append(sp);
    tw(sp, t0 + i * stagger, d, { o: 0, y: dy, blur: 14 }, { o: 1, y: 0, blur: 0 }, "out5");
  });
  return el;
}

// a word or block that lands hard: oversized and blurred to settled, with a colour split and a flash
export function slam(el, t, { from = 1.7, flashOn = true } = {}) {
  tw(el, t, 0.32, { o: 0, s: from, blur: 16, rgb: 18 }, { o: 1, s: 1, blur: 0, rgb: 0 }, "out5");
  tw(el, t + 0.32, 0.5, { rgb: 4 }, { rgb: 0 });
  if (flashOn) flash(t, "#ffffff", 0.55);
  cue(t, "impact");
  return el;
}

export function flash(t, color = "#ffffff", peak = 0.7) {
  const f = h("div", { class: "flash", style: `background:${color}` }); fx.append(f);
  tw(f, t, 0.04, { o: 0 }, { o: peak }); tw(f, t + 0.04, 0.32, { o: peak }, { o: 0 }, "out");
}

// scene change: a team-colour panel sweeps across with speed streaks, the cut happens under it
export function wipe(t, color) {
  const p = h("div", { class: "wipe", style: `--c:${color}` }); fx.append(p);
  tw(p, t - 0.28, 0.28, { x: -2400 }, { x: -400 }, "in"); tw(p, t, 0.3, { x: -400 }, { x: 2400 }, "out");
  for (let i = 0; i < 9; i++) {
    const s = h("i", { class: "streak", style: `top:${8 + i * 10.5}%;width:${300 + ((i * 377) % 500)}px` }); fx.append(s);
    const d = (i % 3) * 0.04;
    tw(s, t - 0.3 + d, 0.55, { x: -900, o: 0.9 }, { x: 2600, o: 0 }, "inOut");
  }
  cue(t, "cut");                                // the music builds into the cut and crashes on it
  if (!wipe.car) cue(t - 0.3, "whoosh");        // with a car to fly past, the pass-by is the sound
  flyby(t, wipe.car);
}
wipe.car = null;                                // set to the car's side view once it is rendered

// camera shake on an impact: a decaying jitter (fixed pseudo-random steps, so every render is the same)
export function shake(el, t, amp = 18, dur = 0.5) {
  const n = 9, step = dur / n;
  for (let i = 0; i < n; i++) {
    const k = 1 - i / n, x = Math.sin(i * 12.9898) * amp * k, y = Math.cos(i * 78.233) * amp * 0.6 * k;
    tw(el, t + i * step, step, { x: i ? Math.sin((i - 1) * 12.9898) * amp * (1 - (i - 1) / n) : 0, y: i ? Math.cos((i - 1) * 78.233) * amp * 0.6 * (1 - (i - 1) / n) : 0 }, { x, y }, "lin");
  }
  tw(el, t + dur, 0.08, { x: 0, y: 0 }, { x: 0, y: 0 });
}

// the car flies past: its side view streaks across the screen, blurred by its speed; the sound is a Doppler pass-by
export function flyby(t, src, dir = 1) {
  if (!src) return;
  const car = h("img", { class: "flyby", src, alt: "", style: dir < 0 ? "transform: scaleX(-1)" : "" }); fx.append(car);
  const from = dir > 0 ? -2600 : 2600, to = -from;
  tw(car, t - 0.32, 0.64, { x: from, o: 1, blur: 10 }, { x: to, o: 1, blur: 10 }, "inOut");
  cue(t - 0.32, "passby", { dir });
}

// a band of light passing over an element (the big numbers)
export function sweep(el, t) {
  const b = h("i", { class: "sweep" }); el.append(b);
  tw(b, t, 0.7, { x: -400, o: 1 }, { x: 1400, o: 0.6 }, "inOut");
}

// the five red start lights: one on per beat from t0, all out at `out`
export function lights(t0, out) {
  const row = h("div", { class: "lights" });
  for (let i = 0; i < 5; i++) {
    const g = h("div", { class: "gantry" }, h("b", { class: "lamp" }), h("b", { class: "lamp" }));
    row.append(g);
    const on = t0 + i * BEAT;
    g.querySelectorAll(".lamp").forEach((l) => { tw(l, on, 0.08, { bright: 0.18 }, { bright: 1.25 }); tw(l, out, 0.06, { bright: 1.25 }, { bright: 0.12 }); });
    cue(on, "light", { n: i });
    cue(on + 0.02, "blip", { n: i });             // the engine revs with each light
  }
  tw(row, t0 - 0.2, 0.35, { o: 0, y: -40 }, { o: 1, y: 0 }); tw(row, out, 0.35, { o: 1, y: 0 }, { o: 0, y: -60 }, "in");
  cue(out, "lightsout");
  cue(out, "launch");                            // and launches, changing up on the beats
  shake(stage, out, 22, 0.6);
  return row;
}
