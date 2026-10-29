// Render every on-screen text layer (Cinzel) as a full-frame 1920x1080 transparent PNG at 2x.
// Usage: node titles.js build/titles.json   (written by titles.py)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const items = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const W = 1920, H = 1080, SS = 2;
  const html = path.resolve('build/titles.html');
  const fonts = [400, 600, 700, 900].map(w => `@font-face{font-family:C;src:url(../assets/fonts/cinzel${w}.woff2);font-weight:${w}}`).join('');
  fs.writeFileSync(html, `<html><head><style>${fonts}</style></head><body style="margin:0"><canvas id=c></canvas>` +
    [400, 600, 700, 900].map(w => `<span style="font-family:C;font-weight:${w}">a</span>`).join('') + `</body></html>`);
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + html); await p.evaluate(() => document.fonts.ready);
  for (const it of items) {
    const data = await p.evaluate(([it, W, H, SS]) => {
      const c = document.getElementById('c'); c.width = W * SS; c.height = H * SS;
      const g = c.getContext('2d'); g.clearRect(0, 0, c.width, c.height);
      g.font = `${it.weight} ${it.size * SS}px C`; g.letterSpacing = `${(it.track || 0) * SS}px`;
      const m = g.measureText(it.text);
      const w = m.actualBoundingBoxLeft + m.actualBoundingBoxRight, capH = m.actualBoundingBoxAscent;
      let x = it.x * SS;
      if (it.align === 'center') x = x - w / 2 + m.actualBoundingBoxLeft;
      const y = it.cy * SS + capH / 2;
      if (it.shadow !== false) {
        g.shadowColor = 'rgba(0,0,0,0.75)'; g.shadowBlur = 10 * SS; g.shadowOffsetY = 2 * SS;
      }
      if (it.style === 'silver') {
        const gr = g.createLinearGradient(0, y - capH, 0, y);
        gr.addColorStop(0, '#ffffff'); gr.addColorStop(0.42, '#dfe4e8'); gr.addColorStop(0.52, '#9aa3aa');
        gr.addColorStop(0.58, '#d8dde1'); gr.addColorStop(1, '#b4bcc2');
        g.fillStyle = gr;
      } else if (it.style === 'gold') {
        const gr = g.createLinearGradient(0, y - capH, 0, y);
        gr.addColorStop(0, '#fff2cc'); gr.addColorStop(0.45, '#e6b65e'); gr.addColorStop(0.56, '#a56f24'); gr.addColorStop(1, '#f2cb77');
        g.fillStyle = gr;
      } else g.fillStyle = it.color || '#ffffff';
      g.fillText(it.text, x, y);
      return c.toDataURL('image/png');
    }, [it, W, H, SS]);
    fs.writeFileSync(it.out, Buffer.from(data.split(',')[1], 'base64'));
  }
  await b.close();
  console.log('rendered', items.length);
})();
