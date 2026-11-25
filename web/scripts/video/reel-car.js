// The team's 3D car in the reel: the site's own viewer (web/garage3d.js, served at /site/), driven frame by frame.
// carShot() mounts it in a scene; the camera is a pure function of time and each frame is drawn with renderNow(),
// so the shot is the same whatever the machine. It also renders a side view once, for the fly-bys.
import { h } from "./reel-engine.js";

let mod = null;
const SIDE = { az: 0, tilt: 0.03, zoom: 0.95 };          // side on, nose to the right (the viewer's az 0)

// mount the car of `team` in a new host element; resolves to { host, credits, side (image URL), at(t) }
export async function carShot(team, color, cls = "carhost") {
  mod ||= await import("/site/garage3d.js");
  const host = h("div", { class: cls });
  document.getElementById("stage").append(host);              // measured while mounting; moved into its scene after
  const c = await mod.mount(host, {
    teams: [{ team, label: team, color, drivers: [], driver: 0 }],
    manifestUrl: "/site/assets/cars/manifest.json", start: 0, auto: false, quality: "film", debug: true,
    view: { az: 0.6, tilt: 0.14, zoom: 1, sway: 0 },
  });
  await new Promise((r) => setTimeout(r, 300));
  const cv = host.querySelector("canvas");
  const draw = (v) => { c.debug.camera(v.az, v.tilt, v.zoom); c.debug.renderNow(); };
  draw(SIDE);
  const side = cv.toDataURL("image/png");                    // read straight after the draw: the buffer is not kept
  let path = null;                                           // camera keyframes: [{ t, az, tilt, zoom }]
  return {
    host, side, credits: c.credits || [],
    move(keys) { path = keys; },
    at(t) {                                                  // the camera at time t, eased between keyframes
      if (!path) return;
      let a = path[0], b = path[path.length - 1];
      for (let i = 0; i < path.length - 1; i++) if (t >= path[i].t && t <= path[i + 1].t) { a = path[i]; b = path[i + 1]; break; }
      const k = b.t > a.t ? Math.min(1, Math.max(0, (t - a.t) / (b.t - a.t))) : 1, e = k < 0.5 ? 4 * k * k * k : 1 - (-2 * k + 2) ** 3 / 2;
      draw({ az: a.az + (b.az - a.az) * e, tilt: a.tilt + (b.tilt - a.tilt) * e, zoom: a.zoom + (b.zoom - a.zoom) * e });
    },
  };
}
