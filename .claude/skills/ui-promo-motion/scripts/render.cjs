#!/usr/bin/env node
/*
 * Render a timeline-driven HTML page to MP4, one frame at a time.
 *
 * The page must expose (motion-kit's MK.mount does this for a GSAP timeline):
 *   window.__seek(t)   draw the frame at time t (seconds)
 *   window.__duration  length in seconds
 *   window.__size      { w, h } stage size in CSS px (optional; else --width/--height)
 *   window.__ready     optional Promise to await before the first frame (fonts, images)
 *
 * Requests to cdn.jsdelivr.net/npm/<pkg>@<ver>/<file> and unpkg.com/<pkg>@<ver>/<file> are served
 * from a local node_modules when the package is installed, so renders work offline.
 */
const path = require('path');
const fs = require('fs');
const { spawn, execSync } = require('child_process');
const { pathToFileURL } = require('url');

const HELP = `usage: node render.cjs <page.html> <out.mp4> [options]

  --fps <n>        output frame rate (default 30)
  --mb <n>         motion-blur sub-frames blended per frame (default 1 = off; 4 recommended)
  --shutter <f>    shutter fraction of a frame the sub-frames span (default 0.5 = 180°)
  --start <s>      first second to render (default 0)
  --end <s>        last second (default page duration)
  --width <px>     override stage width   --height <px>  override stage height
  --scale <f>      device scale factor, e.g. 2 for supersampled 4K from a 1080p stage (default 1)
  --crf <n>        x264 quality, lower is better (default 18)
  --audio <file>   mux an audio track (trimmed to the video length)
  --jpeg           capture JPEG (q95) instead of PNG: ~2x faster, tiny quality loss
  --frames <dir>   also keep the captured frames in <dir>
  --chromium <p>   path to a Chromium executable
`;

function parseArgs(argv) {
  const pos = [];
  const o = { fps: 30, mb: 1, shutter: 0.5, start: 0, end: null, width: null, height: null, scale: 1, crf: 18, audio: null, frames: null, chromium: null, jpeg: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '-h' || a === '--help') { process.stdout.write(HELP); process.exit(0); }
    if (a.startsWith('--')) {
      const k = a.slice(2);
      if (k === 'jpeg') { o.jpeg = true; continue; }
      if (!(k in o)) throw new Error(`unknown option ${a}`);
      const v = argv[++i];
      o[k] = ['audio', 'frames', 'chromium'].includes(k) ? v : Number(v);
    } else pos.push(a);
  }
  if (pos.length < 2) { process.stderr.write(HELP); process.exit(1); }
  return { page: path.resolve(pos[0]), out: path.resolve(pos[1]), ...o };
}

const searchRoots = (pageDir) => {
  const roots = [pageDir, process.cwd(), path.join(__dirname, '..')];
  try { roots.push(execSync('npm root -g', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim()); } catch {}
  return roots;
};

function requireFrom(name, roots) {
  for (const r of roots) {
    try { return require(require.resolve(name, { paths: [r] })); } catch {}
  }
  throw new Error(`Cannot find "${name}". Install it: npm i -D ${name}`);
}

function packageDir(name, roots) {
  for (const r of roots) {
    try { return path.dirname(require.resolve(`${name}/package.json`, { paths: [r] })); } catch {}
  }
  return null;
}

// https://cdn.jsdelivr.net/npm/@scope/pkg@1.2.3/dist/x.js -> { name: '@scope/pkg', file: 'dist/x.js' }
function cdnPackage(u) {
  let p;
  if (u.hostname === 'cdn.jsdelivr.net' && u.pathname.startsWith('/npm/')) p = u.pathname.slice(5);
  else if (u.hostname === 'unpkg.com') p = u.pathname.slice(1);
  else return null;
  const parts = p.split('/');
  const n = parts[0].startsWith('@') ? 2 : 1;
  const name = parts.slice(0, n).join('/').replace(/(.)@[^/]*$/, '$1');
  return { name, file: parts.slice(n).join('/') };
}

const MIME = { '.js': 'application/javascript', '.mjs': 'application/javascript', '.css': 'text/css', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.glb': 'model/gltf-binary', '.hdr': 'application/octet-stream' };

async function main() {
  const opt = parseArgs(process.argv.slice(2));
  const roots = searchRoots(path.dirname(opt.page));
  const { chromium } = requireFrom('playwright', roots);

  const browser = await chromium.launch({
    executablePath: opt.chromium || undefined,
    args: ['--force-color-profile=srgb', '--hide-scrollbars', '--font-render-hinting=none'],
  });
  const context = await browser.newContext({ viewport: { width: opt.width || 1080, height: opt.height || 1920 }, deviceScaleFactor: opt.scale });
  const page = await context.newPage();
  page.on('pageerror', (e) => console.error('[page error]', e.message));
  page.on('console', (m) => m.type() === 'error' && console.error('[console]', m.text()));

  const served = new Set();
  await page.route('**/*', async (route) => {
    const u = new URL(route.request().url());
    const pkg = cdnPackage(u);
    if (pkg && pkg.file) {
      const dir = packageDir(pkg.name, roots);
      const file = dir && path.join(dir, pkg.file);
      if (file && fs.existsSync(file) && fs.statSync(file).isFile()) {
        if (!served.has(pkg.name)) { served.add(pkg.name); console.log(`  serving ${pkg.name} from ${dir}`); }
        return route.fulfill({ path: file, contentType: MIME[path.extname(file)] || 'application/octet-stream', headers: { 'access-control-allow-origin': '*' } });
      }
    }
    return route.continue();
  });

  const url = pathToFileURL(opt.page).href + '?render=1';
  await page.goto(url, { waitUntil: 'load', timeout: 60000 });
  await page.waitForFunction(() => typeof window.__seek === 'function', null, { timeout: 30000 });
  await page.evaluate(async () => { await window.__ready; });

  const meta = await page.evaluate(() => ({ duration: window.__duration, size: window.__size || null }));
  const w = opt.width || (meta.size && meta.size.w) || 1080;
  const h = opt.height || (meta.size && meta.size.h) || 1920;
  await page.setViewportSize({ width: w, height: h });
  const end = opt.end ?? meta.duration;
  if (!(end > opt.start)) throw new Error(`nothing to render: start ${opt.start}, end ${end}`);

  const frames = Math.round((end - opt.start) * opt.fps);
  const mb = Math.max(1, Math.floor(opt.mb));
  const outW = Math.round(w * opt.scale), outH = Math.round(h * opt.scale);
  console.log(`rendering ${frames} frames (${(end - opt.start).toFixed(2)} s) at ${outW}x${outH}, ${opt.fps} fps${mb > 1 ? `, motion blur x${mb}` : ''}`);

  const vf = [];
  if (mb > 1) vf.push(`tmix=frames=${mb}`, `select='eq(mod(n\\,${mb})\\,${mb - 1})'`, `setpts=N/(${opt.fps}*TB)`);
  vf.push(`scale=trunc(iw/2)*2:trunc(ih/2)*2`);
  const ffArgs = ['-y', '-hide_banner', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(opt.fps * mb), '-c:v', opt.jpeg ? 'mjpeg' : 'png', '-i', '-'];
  if (opt.audio) ffArgs.push('-i', path.resolve(opt.audio));
  ffArgs.push('-vf', vf.join(','), '-r', String(opt.fps), '-c:v', 'libx264', '-preset', 'medium', '-crf', String(opt.crf), '-pix_fmt', 'yuv420p', '-movflags', '+faststart');
  if (opt.audio) ffArgs.push('-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '192k', '-shortest');
  ffArgs.push(opt.out);
  const ff = spawn('ffmpeg', ffArgs, { stdio: ['pipe', 'inherit', 'inherit'] });
  const ffDone = new Promise((res, rej) => ff.on('close', (c) => (c === 0 ? res() : rej(new Error(`ffmpeg exited ${c}`)))));
  const write = (buf) => new Promise((res) => (ff.stdin.write(buf) ? res() : ff.stdin.once('drain', res)));

  if (opt.frames) fs.mkdirSync(opt.frames, { recursive: true });
  // CDP capture with optimizeForSpeed is ~4x faster than page.screenshot() for PNG.
  const cdp = await context.newCDPSession(page);
  const shotOpts = opt.jpeg ? { format: 'jpeg', quality: 95, optimizeForSpeed: true } : { format: 'png', optimizeForSpeed: true };
  const ext = opt.jpeg ? 'jpg' : 'png';
  const t0 = Date.now();
  for (let i = 0; i < frames; i++) {
    for (let k = 0; k < mb; k++) {
      const t = opt.start + (i + (mb > 1 ? (k * opt.shutter) / mb : 0)) / opt.fps;
      // Await only real Promises: GSAP timelines are thenables that resolve on completion and would hang.
      await page.evaluate(async (tt) => { const r = window.__seek(tt); if (r instanceof Promise) await r; }, t);
      const img = Buffer.from((await cdp.send('Page.captureScreenshot', shotOpts)).data, 'base64');
      if (opt.frames && k === mb - 1) fs.writeFileSync(path.join(opt.frames, `f${String(i).padStart(5, '0')}.${ext}`), img);
      await write(img);
    }
    if (i % opt.fps === 0 || i === frames - 1) {
      const pct = (((i + 1) / frames) * 100).toFixed(0);
      process.stdout.write(`\r  frame ${i + 1}/${frames} (${pct}%) ${((Date.now() - t0) / 1000).toFixed(0)} s`);
    }
  }
  process.stdout.write('\n');
  ff.stdin.end();
  await ffDone;
  await browser.close();
  console.log(`wrote ${opt.out}`);
}

main().catch((e) => { console.error(e.message || e); process.exit(1); });
