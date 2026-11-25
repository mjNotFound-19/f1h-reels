// Timing engine for the f1.h reel: every moving value is a track over time, and seek(t) sets them all.
// seek(t) is a pure function of t, so a frame looks the same whatever the machine's speed.
// Tempo: the cut is locked to the soundtrack (126 BPM); cue() records where the sound effects go.
export const BPM = 126, BEAT = 60 / BPM, BAR = 4 * BEAT;
export const ease = {
  out: (k) => 1 - (1 - k) ** 3,
  out5: (k) => 1 - (1 - k) ** 5,
  inOut: (k) => (k < 0.5 ? 4 * k * k * k : 1 - (-2 * k + 2) ** 3 / 2),
  in: (k) => k * k * k,
  back: (k) => { const c = 1.7; return 1 + (c + 1) * (k - 1) ** 3 + c * (k - 1) ** 2; },
  lin: (k) => k,
};
const tracks = new Map();          // element -> prop -> [{ t0, t1, from, to, e }]
export const cues = [];            // [{ t, type, ... }] for soundtrack.py

export function tw(el, t0, dur, from, to, e = "out") {
  if (!el) return;
  if (!tracks.has(el)) tracks.set(el, {});
  const m = tracks.get(el);
  for (const p of Object.keys(to)) (m[p] ||= []).push({ t0, t1: t0 + dur, from: from[p], to: to[p], e: ease[e] });
  for (const p of Object.keys(m)) m[p].sort((a, b) => a.t0 - b.t0);
}
export const cue = (t, type, extra = {}) => cues.push({ t: +t.toFixed(4), type, ...extra });

function valueAt(list, t) {
  let v = list[0].from;
  for (const s of list) {
    if (t < s.t0) break;
    const k = s.t1 > s.t0 ? Math.min(1, (t - s.t0) / (s.t1 - s.t0)) : 1;
    v = s.from + (s.to - s.from) * s.e(k);
  }
  return v;
}

export function seek(t) {
  for (const [el, m] of tracks) {
    const v = {}; for (const p in m) v[p] = valueAt(m[p], t);
    const tf = [];
    if ("x" in v || "y" in v) tf.push(`translate(${(v.x || 0).toFixed(2)}px, ${(v.y || 0).toFixed(2)}px)`);
    if ("rot" in v) tf.push(`rotate(${v.rot.toFixed(3)}deg)`);
    if ("s" in v) tf.push(`scale(${v.s.toFixed(4)})`);
    if ("sx" in v) tf.push(`scaleX(${Math.max(0, v.sx).toFixed(4)})`);
    if ("sy" in v) tf.push(`scaleY(${Math.max(0, v.sy).toFixed(4)})`);
    if (tf.length) el.style.transform = tf.join(" ");
    if ("o" in v) el.style.opacity = Math.max(0, Math.min(1, v.o)).toFixed(3);
    if ("blur" in v || "bright" in v) el.style.filter = `blur(${Math.max(0, v.blur || 0).toFixed(2)}px) brightness(${(v.bright ?? 1).toFixed(3)})`;
    if ("clipL" in v || "clipR" in v) el.style.clipPath = `inset(-20% ${Math.max(0, v.clipR || 0).toFixed(2)}% -20% ${Math.max(0, v.clipL || 0).toFixed(2)}%)`;
    if ("rgb" in v) { const d = v.rgb.toFixed(1); el.style.textShadow = v.rgb > 0.05 ? `${-d}px 0 rgba(255,40,70,.85), ${d}px 0 rgba(40,200,255,.85)` : "none"; }
    if ("dash" in v) el.style.strokeDashoffset = v.dash.toFixed(4);
    if ("n" in v) el.textContent = el.__fmt(v.n);
    if ("along" in v) el.__along(v.along);
  }
}

export const h = (tag, attrs = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) if (v != null) k === "style" ? (e.style.cssText = v) : k === "html" ? (e.innerHTML = v) : e.setAttribute(k, v);
  for (const c of kids.flat()) if (c != null && c !== false) e.append(c.nodeType ? c : document.createTextNode(String(c)));
  return e;
};

// a number counting from `from` to `to` between t0 and t0 + dur, with soft ticks in the soundtrack
export function count(el, t0, dur, to, fmt, from = 0) {
  el.__fmt = fmt; el.textContent = fmt(from); tw(el, t0, dur, { n: from }, { n: to }, "out5");
  for (let k = 0; k < 5; k++) cue(t0 + dur * (1 - (1 - k / 5) ** 2) * 0.8, "tick", { soft: true });
  return el;
}
