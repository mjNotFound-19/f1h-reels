// The forecast reel, before a race (or a sprint). Cut on the beat (126 BPM): lights, the question, the favourite,
// the top five, the circuit, the plan, the end card. 11 bars.
import { tw, h, count, cue, BEAT, BAR } from "./reel-engine.js";
import { stage, scene, letters, slam, wipe, sweep, lights } from "./reel-fx.js";
import { S, pct, color, lastName, face, heading, endCard, shortTeam, carCredit } from "./reel-parts.js";
import { carShot } from "./reel-car.js";

const MODE = { pre_weekend: "Pre-weekend forecast", post_quali: "After qualifying", post_sprint: "After the sprint", post_fp: "After practice" };
const TYRE = { S: "#ff3b3b", M: "#ffd75e", H: "#f2f4f7", I: "#3ddc97", W: "#4aa8ff" };

export async function forecastReel(sprint) {
  const N = S.next, M = N.meta, src = sprint && N.sprint?.drivers ? N.sprint : N;
  const all = src.drivers || [], D = all.slice().sort((a, b) => b.win - a.win), fav = D[0];
  const label = sprint && N.sprint ? "Sprint forecast" : MODE[M.mode] || "Forecast", title = M.event || `${M.location} Grand Prix`;
  const place = (M.location || title).replace(/ Grand Prix$/, ""), tc = color(fav.Team);
  stage.style.setProperty("--team", tc);
  const OUT = 6 * BEAT;
  // the favourite's car: the hero of its scene, and the car that flies past at every scene change
  const car = await carShot(fav.Team, tc).catch(() => null);
  if (car) { wipe.car = car.side; carCredit(car.credits, fav.Team); }

  // lights, then the question
  scene("lightsup", 0, OUT, letters(`Round ${M.round} · ${title} · ${label}`, 0.05, "kicker center", { stagger: 0.012, dy: 20 }), lights(0.0, OUT));
  {
    const q = h("div", { class: "slamname center" }, "Who wins"), w = h("div", { class: "slamword center" }, `${(M.country || place)}?`);
    scene("question", OUT, 2 * BAR, q, w);
    slam(q, OUT); slam(w, OUT + BEAT, { from: 2.2, flashOn: false });
  }
  // the favourite
  let t = 2 * BAR;
  {
    wipe(t, tc);
    const num = h("b", {}); count(num, t + BEAT, 1.0, fav.win * 100, (x) => `${Math.round(x)}%`);
    const stat = h("div", { class: "bigstat left" }, num, h("span", {}, `chance to win · ${(M.n_sims || 0).toLocaleString("en")} simulated races`));
    const name = h("div", { class: `slamname${lastName(fav.Driver).length > 8 ? " long" : ""}` }, lastName(fav.Driver));
    scene("winner", t, 4 * BAR, h("div", { class: "bignum" }, String((S.people?.[fav.Driver] || {}).number || "")), car ? car.host : null,
      h("div", { class: "kicker" }, "The model's favourite"), name, stat);
    if (car) {                                    // the camera swings round the car and pushes in
      car.move([{ t, az: 1.6, tilt: 0.08, zoom: 1.3 }, { t: t + 1.0, az: 0.8, tilt: 0.15, zoom: 1.0 }, { t: 4 * BAR, az: 0.45, tilt: 0.2, zoom: 0.92 }]);
      const cam = h("i"); cam.__along = (v) => car.at(v); tw(cam, t, 4 * BAR - t, { along: t }, { along: 4 * BAR }, "lin");
      tw(car.host, t, 0.5, { o: 0, x: 260 }, { o: 1, x: 0 }, "out5");
    }
    slam(name, t + 0.05, { flashOn: false }); tw(stat, t + BEAT, 0.4, { o: 0, y: 40 }, { o: 1, y: 0 }); sweep(num, t + 3 * BEAT);
  }
  // the top five
  t = 4 * BAR;
  {
    wipe(t, "#ff3b3b");
    const five = D.slice(0, 5), max = five[0].win || 1;
    const rows = five.map((d, i) => {
      const fill = h("div", { class: "fill" }), num = h("div", { class: "pct" });
      const row = h("div", { class: "bar", style: `--c:${color(d.Team)}` },
        h("div", { class: "who" }, face(d.Driver) ? h("img", { src: face(d.Driver), alt: "" }) : null, d.Driver, h("small", {}, shortTeam(d.Team))), h("div", { class: "track" }, fill), num);
      const when = t + BEAT + i * (BEAT / 2);
      tw(row, when, 0.35, { o: 0, x: -80 }, { o: 1, x: 0 }, "out5"); tw(fill, when + 0.1, 1.0, { sx: 0 }, { sx: d.win / max }, "out5");
      count(num, when + 0.1, 1.0, d.win * 100, (x) => `${x < 10 ? x.toFixed(1) : Math.round(x)}%`); cue(when, "hit");
      return row;
    });
    scene("", t, 6 * BAR, ...heading(t, label, "Chance to win"), h("div", { class: "bars" }, rows));
  }
  // the circuit
  t = 6 * BAR;
  const T = N.track;
  if (T?.points?.length) {
    wipe(t, tc);
    const pad = 40, d = "M" + T.points.map((p) => p.join(",")).join(" L") + " Z";
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", `${-pad} ${-pad} ${T.w + 2 * pad} ${T.h + 2 * pad}`);
    svg.innerHTML = `<path d="${d}" fill="none" stroke="rgba(255,255,255,.07)" stroke-width="34" stroke-linejoin="round"/>
      <path class="ln" d="${d}" pathLength="1" fill="none" stroke="var(--team)" stroke-width="12" stroke-linejoin="round" stroke-linecap="round" stroke-dasharray="1 1" stroke-dashoffset="1" style="filter:drop-shadow(0 0 14px var(--team))"/>
      <circle class="dot" r="20" fill="#fff" stroke="#ff3b3b" stroke-width="8"/>`;
    const ln = svg.querySelector(".ln"), dot = svg.querySelector(".dot");
    dot.__along = (k) => { const p = ln.getPointAtLength((((k % 1) + 1) % 1) * ln.getTotalLength()); dot.setAttribute("cx", p.x); dot.setAttribute("cy", p.y); };
    const C = N.circuit || {};
    const facts = [["Laps", C.n_laps], ["Lap", T.length_m && `${(T.length_m / 1000).toFixed(2)} km`], ["Safety car", M.p_sc != null && pct(M.p_sc)]]
      .filter(([, v]) => v).map(([a, b], i) => { const f = h("div", {}, h("span", {}, a), h("b", {}, String(b))); tw(f, t + (i + 2) * BEAT, 0.35, { o: 0, y: 30 }, { o: 1, y: 0 }); cue(t + (i + 2) * BEAT, "tick"); return f; });
    scene("circuit", t, 7.5 * BAR, ...heading(t, title, place), h("div", { class: "facts" }, facts), svg);
    tw(ln, t + 0.2, 1.6, { dash: 1 }, { dash: 0 }, "inOut");
    tw(dot, t + 0.2, 0.3, { o: 0 }, { o: 1 }); tw(dot, t + 0.2, 1.5 * BAR, { along: 0 }, { along: 1.2 }, "lin");
  }
  // the plan
  t = 7.5 * BAR;
  {
    wipe(t, "#ff3b3b");
    const plan = String(fav.strategy || "").split("-").filter(Boolean);
    const tyres = plan.flatMap((c, i) => {
      const ty = h("span", { class: "tyre", style: `--tc:${TYRE[c] || "#888"}` }, c), when = t + (i + 1) * (BEAT / 2);
      tw(ty, when, 0.35, { o: 0, s: 0.2, rot: -120 }, { o: 1, s: 1, rot: 0 }, "back"); cue(when, "hit");
      return [i ? h("span", { class: "arrow" }, "→") : null, ty];
    });
    const lap = fav.first_stop_p50 ? h("div", { class: "sub" }, `${lastName(fav.Driver)}'s likeliest plan · first stop around lap ${Math.round(fav.first_stop_p50)}`) : null;
    if (lap) tw(lap, t + 2 * BEAT, 0.4, { o: 0, y: 20 }, { o: 1, y: 0 });
    scene("plan", t, 9 * BAR, ...heading(t, "Strategy", "The plan"), h("div", { class: "plan" }, tyres), lap);
  }
  endCard(9 * BAR, 11 * BAR, "The full forecast, every driver, before the lights go out.");
  return { duration: 11 * BAR + 0.6, poster: 2 * BAR + 2.2 };
}
