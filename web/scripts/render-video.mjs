// Render an f1.h reel frame by frame from the published site's data (no screen recording).
//   node web/scripts/render-video.mjs <result|forecast|sprint> [site url] [outdir] [wide|story]
// Writes <outdir>/frames/f000000.jpg ..., frames/list.txt (an ffmpeg concat list) and frames/cues.json (where the
// soundtrack's effects go) for make-video.sh. Drawn at 2x pixel density: native 4K (3840 x 2160) for the 16:9
// master at 120 fps; the story at 2160 x 3840, 60 fps (Instagram takes up to 60). Frame 0 is the poster.
// Each frame is set by the reel's seek(t) and captured whole, so the frame rate is steady on any machine.
import { createRequire } from "module";
import { execSync } from "child_process";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const require = createRequire(import.meta.url);
const { chromium } = require(path.join(execSync("npm root -g").toString().trim(), "@playwright/cli/node_modules/playwright"));
const HERE = path.dirname(fileURLToPath(import.meta.url)), REEL = path.join(HERE, "video"), ASSETS = path.join(HERE, "..", "assets");
const KIND = process.argv[2] || "result", URL = process.argv[3] || "https://manasjha.online/f1/", OUT = process.argv[4] || "docs/video";
const STORY = process.argv[5] === "story", W = STORY ? 1080 : 1920, H = STORY ? 1920 : 1080;   // layout size; drawn at 2x
const FPS = Number(process.env.REEL_FPS || (STORY ? 60 : 120)), DPR = Number(process.env.REEL_DPR || 2);
const SITE = path.join(HERE, "..");                          // web/: the 3D viewer, three.js and the car models
if (!["result", "forecast", "sprint"].includes(KIND)) { console.error("kind must be result, forecast or sprint"); process.exit(1); }

const site = await (await fetch(new globalThis.URL(`data/v3/site.json?t=${Date.now()}`, URL))).json();
const browser = await chromium.launch({ channel: "chrome", args: ["--hide-scrollbars", "--force-color-profile=srgb", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: DPR });
await ctx.route("http://reel.local/**", (route) => {
  const name = decodeURIComponent(new globalThis.URL(route.request().url()).pathname.slice(1));
  const file = name.startsWith("site/") ? path.join(SITE, path.normalize(name.slice(5)).replace(/^(\.\.[\\/])+/, ""))
    : name === "contours.svg" ? path.join(ASSETS, name) : path.join(REEL, path.basename(name));
  if (!file.startsWith(SITE) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) return route.fulfill({ status: 404, body: "" });
  const type = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml", ".json": "application/json",
                 ".glb": "model/gltf-binary", ".wasm": "application/wasm" }[path.extname(file)] || "application/octet-stream";
  route.fulfill({ status: 200, contentType: type, body: fs.readFileSync(file) });
});
await ctx.addInitScript(([s, k, f]) => { window.__SITE = s; window.__KIND = k; window.__FORMAT = f; }, [site, KIND, STORY ? "story" : "wide"]);
const page = await ctx.newPage();
const errors = []; page.on("pageerror", (e) => errors.push(e.message));
await page.goto("http://reel.local/reel.html", { waitUntil: "load" });
await page.waitForFunction(() => window.reel, null, { timeout: 30000 }).catch(() => {});
if (errors.length || !(await page.evaluate(() => !!window.reel))) { console.error("reel failed to build:", errors.join("; ")); await browser.close(); process.exit(2); }
await page.evaluate(() => window.reel.ready);
const { duration, poster, cues } = await page.evaluate(() => ({ duration: window.reel.duration, poster: window.reel.poster, cues: window.reel.cues }));

if (process.env.REEL_STILLS) {            // check mode: only the listed moments, as stills (no video)
  fs.mkdirSync(OUT, { recursive: true });
  for (const t of process.env.REEL_STILLS.split(",").map(Number)) {
    await page.evaluate((x) => window.reel.seek(x), t);
    await page.screenshot({ path: path.join(OUT, `still-${STORY ? "story" : "wide"}-${t.toFixed(2)}.jpg`), type: "jpeg", quality: 85 });
  }
  console.log(`stills: ${process.env.REEL_STILLS} (duration ${duration.toFixed(2)} s, ${cues.length} sound cues)`);
  await browser.close(); process.exit(0);
}
const FR = path.join(OUT, "frames"); fs.rmSync(FR, { recursive: true, force: true }); fs.mkdirSync(FR, { recursive: true });
const cdp = await ctx.newCDPSession(page);
const n = Math.ceil(duration * FPS), t0 = Date.now(), lines = ["ffconcat version 1.0"];
for (let i = 0; i < n; i++) {
  await page.evaluate((t) => window.reel.seek(t), i / FPS);
  // the clip's scale is what makes the capture full resolution (without it Chrome returns layout-size pixels)
  const { data } = await cdp.send("Page.captureScreenshot", { format: "jpeg", quality: 92, optimizeForSpeed: true, clip: { x: 0, y: 0, width: W, height: H, scale: DPR } });
  const name = `f${String(i).padStart(6, "0")}.jpg`;
  fs.writeFileSync(path.join(FR, name), Buffer.from(data, "base64"));
  lines.push(`file '${name}'`, `duration ${(1 / FPS).toFixed(6)}`);
  if (i % 300 === 0) console.log(`frame ${i}/${n}`);
}
lines.push(`file 'f${String(n - 1).padStart(6, "0")}.jpg'`);
fs.writeFileSync(path.join(FR, "list.txt"), lines.join("\n"));
fs.writeFileSync(path.join(FR, "cues.json"), JSON.stringify({ duration, fps: FPS, cues }, null, 1));
// poster: a settled frame replaces frame 0 (same length, same sync), so every platform's thumbnail shows it
const frame = (i) => path.join(FR, `f${String(i).padStart(6, "0")}.jpg`), pi = Math.min(n - 1, Math.round((poster || 0) * FPS));
if (pi > 0) fs.copyFileSync(frame(pi), frame(0));
fs.copyFileSync(frame(0), path.join(FR, "poster.jpg"));
await browser.close();
// the same summary line the recorder printed: the agent checks the frame rate from it
console.log(`frames: ${n} over ${duration.toFixed(1)} s = ${FPS.toFixed(1)} fps captured (generated in ${((Date.now() - t0) / 1000).toFixed(0)} s) -> ${path.join(FR, "list.txt")}`);
