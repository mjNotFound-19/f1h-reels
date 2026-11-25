// Shared pieces of the f1.h reels: data lookups, the scene heading, number blocks and the end card.
import { tw, h, cue, BEAT } from "./reel-engine.js";
import { scene, letters, slam, sweep, flash } from "./reel-fx.js";

export const S = window.__SITE;
export const pct = (x) => `${Math.round((x || 0) * 100)}%`;
export const color = (team) => (S.team_colors || {})[team] || "#888888";
export const person = (code) => (S.people || {})[code] || {};
export const fullName = (code) => person(code).name || code;
export const lastName = (code) => fullName(code).split(" ").pop();
// photos at 4K-worthy sizes: the site's links are thumbnails; the image service resizes to whatever is asked for
const big = (u, px) => (u ? u.replace(/w_\d+,h_\d+/, `w_${px},h_${px}`) : null);
export const cut = (code) => { const p = person(code); return big(p.cutout, 1600) || p.headshot || big(p.photo, 1600) || null; };
export const face = (code) => { const p = person(code); return big(p.photo, 400) || p.headshot || null; };
export const img = (src, cls) => (src ? h("img", { src, class: cls, alt: "" }) : null);
export const shortTeam = (t) => String(t || "").replace(/ (Racing|F1 Team)$/, "");

// the 3D model's credit (CC BY) joins the credit line at the bottom of every frame
export function carCredit(credits, team) {
  const c = credits.find((x) => String(x.used_for || "").includes(team)) || credits[0];
  const el = document.querySelector(".credit");
  if (c && el) el.textContent += ` · 3D car: ${c.title} by ${c.author}, ${c.licence} (${c.url}), adapted`;
}

// kicker line, then the title in kinetic letters
export function heading(t, kicker, title, cls = "") {
  const k = h("div", { class: "kicker" }, kicker);
  tw(k, t + 0.1, 0.4, { o: 0, x: -40 }, { o: 1, x: 0 });
  return [k, letters(title, t + 0.15, `title ${cls}`)];
}

// a photo that slides in from the side and keeps drifting (parallax against the push-in)
export function photo(code, cls, t0, t1, dx = 200) {
  const p = img(cut(code), cls); if (!p) return null;
  tw(p, t0, 0.7, { o: 0, x: dx, blur: 12 }, { o: 1, x: 0, blur: 0 }, "out5");
  tw(p, t0 + 0.7, Math.max(0.1, t1 - t0 - 0.7), { x: 0 }, { x: -dx * 0.15 }, "lin");
  return p;
}

export function endCard(t0, t1, line) {
  const logo = h("div", { class: "logo", html: "&lt;f1<b>.</b>h&gt;" });
  const url = h("div", { class: "url", html: "manasjha.online<b>/f1</b>" }), l = h("div", { class: "line" }, line);
  scene("end", t0, t1 + 0.6, logo, url, l);
  slam(logo, t0 + 0.05, { from: 0.6 }); tw(url, t0 + BEAT, 0.5, { o: 0, y: 40, blur: 10 }, { o: 1, y: 0, blur: 0 }, "out5");
  tw(l, t0 + 2 * BEAT, 0.5, { o: 0, y: 30 }, { o: 1, y: 0 }); sweep(url, t0 + 3 * BEAT);
  cue(t0, "end");
}
