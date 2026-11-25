// f1.h reel: a video built from the site's own data. The renderer (web/scripts/render-video.mjs) sets window.__SITE
// (site.json), window.__KIND ("result", "forecast" or "sprint") and window.__FORMAT ("wide" or "story") first, then
// calls window.reel.seek(t) for every frame and writes window.reel.cues for the soundtrack.
import { seek, h, cues } from "./reel-engine.js";
import { stage } from "./reel-fx.js";
import { resultReel } from "./reel-result.js";
import { forecastReel } from "./reel-forecast.js";

const KIND = window.__KIND || "result";
stage.prepend(h("div", { id: "contours" }), h("div", { id: "glow" }));
stage.append(h("div", { id: "grain" }), h("div", { id: "vignette" }), h("div", { class: "brand", html: "&lt;f1<b>.</b>h&gt;" }),
  h("div", { class: "credit" }, "Driver photos: Formula 1 · Forecast and scoring: the f1.h model · Music: original, made for f1.h"));
const { duration, poster } = await (KIND === "result" ? resultReel() : forecastReel(KIND === "sprint"));
seek(0);
// every picture and font loaded before the first frame (a picture that failed is hidden, never half-drawn)
const ready = Promise.all([document.fonts.ready, ...[...document.images].map((i) => (i.complete ? null : new Promise((r) => { i.onload = i.onerror = r; })))])
  .then(() => { [...document.images].forEach((i) => { if (!i.naturalWidth) i.style.visibility = "hidden"; }); return true; });
window.reel = { duration, poster, seek, ready, cues: cues.slice().sort((a, b) => a.t - b.t) };
