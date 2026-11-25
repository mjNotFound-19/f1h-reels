// The result reel, after a race. Cut on the beat (126 BPM): lights, lights out on the winner, the podium, did the
// model call it, the season, the end card. 11 bars.
import { tw, h, count, cue, BEAT, BAR } from "./reel-engine.js";
import { stage, scene, letters, slam, wipe, sweep, lights } from "./reel-fx.js";
import { S, pct, color, fullName, lastName, img, cut, heading, endCard, shortTeam, carCredit } from "./reel-parts.js";
import { carShot } from "./reel-car.js";

export async function resultReel() {
  const L = S.last, R = L.results || [], win = R[0];
  const race = (S.races || []).find((r) => r.year === L.year && r.round === L.round);
  const PD = (race?.predictions?.backtest_post_quali || race?.predictions?.backtest_pre_weekend)?.drivers || [];
  const P = Object.fromEntries(PD.map((d) => [d.Driver, d])), fav = PD.slice().sort((a, b) => b.win - a.win)[0];
  const bench = ((S.benchmarks || {})[String(S.season)]?.per_race || []).filter((r) => r.mode === "post_quali").sort((a, b) => a.round - b.round);
  const thisB = bench.find((r) => r.round === L.round && r.year === L.year);
  const title = L.title || `${L.location} Grand Prix`, tc = color(win.Team);
  stage.style.setProperty("--team", tc);
  const OUT = 6 * BEAT;
  // the winning team's car: the hero of lights out, and the car that flies past at every scene change
  const car = await carShot(win.Team, tc).catch(() => null);
  if (car) { wipe.car = car.side; carCredit(car.credits, win.Team); }

  // lights, then lights out
  {
    const k = letters(`Round ${L.round} · ${title}`, 0.05, "kicker center", { stagger: 0.015, dy: 20 });
    scene("lightsup", 0, OUT, k, lights(0.0, OUT));
  }
  // the winner
  {
    const t1 = 3 * BAR, big = h("div", { class: "bignum" }, String((S.people?.[win.Driver] || {}).number || ""));
    const name = h("div", { class: `slamname${lastName(win.Driver).length > 8 ? " long" : ""}` }, lastName(win.Driver)), wins = h("div", { class: "slamword" }, "wins");
    const facts = h("div", { class: "facts" },
      h("div", {}, h("span", {}, "Started"), h("b", {}, `P${win.grid ?? "–"}`)),
      P[win.Driver] ? h("div", {}, h("span", {}, "Model's win chance"), h("b", {}, pct(P[win.Driver].win))) : null,
      fav ? h("div", {}, h("span", {}, "Model's favourite"), h("b", {}, fav.Driver === win.Driver ? "Yes" : lastName(fav.Driver))) : null);
    scene("winner", OUT, t1, big, car ? car.host : null, h("div", { class: "kicker" }, title), name, wins, facts);
    if (car) {                                    // the camera swings round the car from the front and pushes in
      car.move([{ t: OUT, az: -0.35, tilt: 0.1, zoom: 1.35 }, { t: OUT + 0.9, az: 0.55, tilt: 0.16, zoom: 1.0 }, { t: t1, az: 0.95, tilt: 0.2, zoom: 0.9 }]);
      const cam = h("i"); cam.__along = (v) => car.at(v); tw(cam, OUT, t1 - OUT, { along: OUT }, { along: t1 }, "lin");
      tw(car.host, OUT, 0.5, { o: 0, x: 260 }, { o: 1, x: 0 }, "out5");
    }
    tw(big, OUT, 1.2, { o: 0, s: 1.3 }, { o: 1, s: 1 }, "out5");
    slam(name, OUT); slam(wins, OUT + BEAT, { from: 2.2, flashOn: false });
    [...facts.children].forEach((f, i) => tw(f, OUT + 2 * BEAT + i * BEAT / 2, 0.4, { o: 0, y: 30 }, { o: 1, y: 0 }));
  }
  // the podium
  let t = 3 * BAR;
  {
    const hg = [1, 0.78, 0.62], order = [1, 0, 2];
    wipe(t, tc);
    const steps = order.map((i) => {
      const r = R[i]; if (!r) return null;
      const block = h("div", { class: "block", style: `--c:${color(r.Team)};--h:${hg[i]}` },
        h("div", { class: "p" }, `P${i + 1}`), h("div", { class: "d" }, r.Driver), h("div", { class: "t" }, shortTeam(r.Team)),
        P[r.Driver] ? h("div", { class: "f" }, `model: ${pct(P[r.Driver].podium)} podium`) : null);
      const pic = img(cut(r.Driver)), when = t + (3 - i) * BEAT;
      tw(block, when, 0.45, { sy: 0 }, { sy: 1 }, "back"); if (pic) tw(pic, when + 0.25, 0.45, { o: 0, y: -80, blur: 10 }, { o: 1, y: 0, blur: 0 }, "out5");
      cue(when, i === 0 ? "impact" : "hit");
      return h("div", { class: "step" }, pic, block);
    });
    scene("", t, 5 * BAR, ...heading(t, "The podium", title), h("div", { class: "podium" }, steps));
  }
  // did the model call it?
  t = 5 * BAR;
  {
    wipe(t, "#ff3b3b");
    const podF = PD.slice().sort((a, b) => b.podium - a.podium).slice(0, 3).map((d) => d.Driver);
    const hit = R.slice(0, 3).filter((r) => podF.includes(r.Driver)).length, won = !!fav && fav.Driver === win.Driver;
    const closer = thisB ? 1 - thisB.model_rps / thisB.grid_rps : null;
    const v = [h("b", { class: won ? "ok" : "bad" }, fav ? (won ? "YES" : "NO") : "–"), h("b", {}, "–"), h("b", { class: closer > 0 ? "ok" : "bad" }, "–")];
    const rows = [
      [v[0], "Favourite won", fav ? `${fullName(fav.Driver)}, ${pct(fav.win)}` : "no stored forecast"],
      [v[1], "Podium called", podF.join(" · ")],
      [v[2], closer == null || closer > 0 ? "Closer than the grid" : "Further than the grid", "error on the whole finishing order"],
    ].map(([val, k, x], i) => {
      const row = h("div", { class: "verdict" }, val, h("div", {}, h("div", { class: "vk" }, k), h("div", { class: "vx" }, x)));
      slam(row, t + (i + 1) * BEAT, { from: 1.25, flashOn: false });
      return row;
    });
    if (PD.length) count(v[1], t + 2 * BEAT, 0.6, hit, (n) => `${Math.round(n)}/3`);
    if (closer != null) count(v[2], t + 3 * BEAT, 0.7, Math.abs(closer) * 100, (n) => `${Math.round(n)}%`);
    scene("", t, 7 * BAR, ...heading(t, "Scored in public", "Did the model call it?"), h("div", { class: "verdicts" }, rows));
  }
  // the season
  t = 7 * BAR;
  if (bench.length) {
    wipe(t, tc);
    const diffs = bench.map((r) => r.grid_rps - r.model_rps), m = Math.max(...diffs.map(Math.abs), 1e-6), better = diffs.filter((d) => d > 0).length;
    const cols = bench.map((r, i) => {
      const d = diffs[i], up = d >= 0;
      const bar = h("i", { style: `${up ? "bottom" : "top"}:50%;height:${(Math.abs(d) / m) * 46}%;background:var(--${up ? "ok" : "bad"});transform-origin:50% ${up ? "100%" : "0"}` });
      tw(bar, t + BEAT + i * (BEAT / 4), 0.4, { sy: 0 }, { sy: 1 }, "back");
      return h("div", { class: "col" }, bar, h("span", {}, `R${r.round}`));
    });
    const big = h("div", { class: "bigstat" }, h("b", {}, `${better}/${bench.length}`), h("span", {}, "races closer than the starting grid"));
    slam(big, t + 2 * BEAT, { from: 1.4, flashOn: false }); sweep(big.firstChild, t + 3 * BEAT);
    scene("", t, 9 * BAR, ...heading(t, `${S.season} season · after qualifying`, "The model vs the grid"), big, h("div", { class: "chart" }, h("div", { class: "axis" }), cols));
  }
  endCard(9 * BAR, 11 * BAR, "A forecast before every race. Scored in public after it.");
  return { duration: 11 * BAR + 0.6, poster: OUT + 1.6 };
}
