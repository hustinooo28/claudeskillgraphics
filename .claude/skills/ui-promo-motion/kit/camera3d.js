/*
 * camera3d.js — a deterministic 3D camera rig in CSS 3D for the "dark glow 3D showcase" style
 * (curved screen walls, floating card clouds, orbit / dolly / fly-into-screen moves).
 * Requires gsap + motion-kit.js. Everything is driven from GSAP time, so it renders frame-exactly.
 *
 *   const rig = C3.rig('#view3d', { fov: 1100 });     // viewport element (position:absolute; inset:0)
 *   rig.add(el, { x, y, z, rx, ry, rz });             // place any element in world space (px, deg)
 *   tl.to(rig.cam, { z: 600, ry: 20, duration: 2, onUpdate: rig.update }, at);
 *
 * World axes: +x right, +y down (CSS), +z toward the viewer. The camera starts at z = fov, where the
 * z = 0 plane renders 1:1. Lower cam.z to dolly in; cam.ry yaws (orbit by also moving x/z), cam.rx pitches.
 * Elements far from cam.focus get depth-of-field blur (cam.dof px per 1000 px of depth error).
 */
(function (global) {
  const gsap = global.gsap;
  const C3 = {};
  const $ = (q) => (typeof q === 'string' ? document.querySelector(q) : q);

  C3.rig = function (viewport, opts = {}) {
    const vp = $(viewport);
    const fov = opts.fov || 1100;
    vp.style.perspective = `${fov}px`;
    vp.style.perspectiveOrigin = '50% 50%';
    vp.style.overflow = 'hidden';
    const world = document.createElement('div');
    world.className = 'c3-world';
    Object.assign(world.style, { position: 'absolute', left: '50%', top: '50%', width: '0', height: '0', transformStyle: 'preserve-3d' });
    vp.appendChild(world);

    const rig = {
      vp, world, fov, objects: [],
      cam: { x: 0, y: 0, z: fov, rx: 0, ry: 0, rz: 0, focus: fov, dof: opts.dof ?? 14, maxBlur: opts.maxBlur ?? 14 },

      // Place an element (or a C3.group) in world space. Its centre sits at (x, y, z).
      add(el, p = {}) {
        el = $(el);
        if (el.parentNode !== world && !p.parent) world.appendChild(el);
        if (p.parent) $(p.parent).appendChild(el);
        const o = { el, x: 0, y: 0, z: 0, rx: 0, ry: 0, rz: 0, s: 1, dofOn: p.dof !== false, ...p };
        el.style.position = 'absolute';
        el.style.transformStyle = 'preserve-3d';
        el.style.backfaceVisibility = p.backface ? 'visible' : 'hidden';
        const w = el.offsetWidth, h = el.offsetHeight;
        el.style.left = `${-w / 2}px`;
        el.style.top = `${-h / 2}px`;
        o.apply = () => (el.style.transform = `translate3d(${o.x}px,${o.y}px,${o.z}px) rotateY(${o.ry}deg) rotateX(${o.rx}deg) rotateZ(${o.rz}deg) scale(${o.s})`);
        o.apply();
        if (!p.parent) rig.objects.push(o);
        return o;
      },

      viewTransform() {
        const c = rig.cam;
        return `translateZ(${rig.fov}px) rotateZ(${-c.rz}deg) rotateX(${-c.rx}deg) rotateY(${-c.ry}deg) translate3d(${-c.x}px,${-c.y}px,${-c.z}px)`;
      },

      // Call from every camera / object tween's onUpdate (or once per frame via rig.drive(tl)).
      update() {
        const vt = rig.viewTransform();
        world.style.transform = vt;
        const m = new DOMMatrix(vt);
        const c = rig.cam;
        for (const o of rig.objects) {
          o.apply();
          const pt = m.transformPoint(new DOMPoint(o.x, o.y, o.z));
          const dist = rig.fov - pt.z; // distance in front of the eye
          o.el.style.visibility = dist < 40 ? 'hidden' : '';
          if (o.dofOn && c.dof > 0) {
            const b = Math.min(c.maxBlur, (Math.abs(dist - c.focus) / 1000) * c.dof);
            o.el.style.filter = b > 0.3 ? `blur(${b.toFixed(2)}px)` : 'none';
          }
        }
      },

      // Orbit the camera around a point: tween an angle and keep the camera aimed at the centre.
      // tl.add(rig.orbit({ cx, cy, cz, radius, from, to, y, duration, ease }), at)
      orbit(p) {
        const { cx = 0, cz = 0, radius = rig.fov, from = 0, to = 30, duration = 2, ease = 'sine.inOut' } = p;
        const a = { v: from };
        const set = () => {
          const r = (a.v * Math.PI) / 180;
          Object.assign(rig.cam, { x: cx + Math.sin(r) * radius, z: cz + Math.cos(r) * radius, ry: a.v, focus: radius });
          if (p.y != null) rig.cam.y = p.y; // otherwise leave cam.y free for a separate crane tween
        };
        return gsap.timeline().to(a, { v: to, duration, ease, onUpdate: set, onStart: set });
      },

      // Camera position that frames object `o` straight on so it fills `fill` of the viewport width.
      frame(o, fill = 1) {
        const w = o.el.offsetWidth * (o.s || 1);
        const d = (w * rig.fov) / (rig.vp.offsetWidth * fill); // a width w at distance d renders w*fov/d px wide
        const ry = o.ry || 0, rx = o.rx || 0;
        const r = (a) => (a * Math.PI) / 180;
        // Offset along the object's facing normal (rotateY then rotateX).
        const nx = Math.sin(r(ry)) * Math.cos(r(rx)), ny = -Math.sin(r(rx)), nz = Math.cos(r(ry)) * Math.cos(r(rx));
        return { x: o.x + nx * d, y: o.y + ny * d, z: o.z + nz * d, ry, rx, rz: 0, focus: d };
      },
    };
    vp.__rig = rig;
    rig.update();
    // Re-apply the camera after every seek / tick, so tweens on rig.cam or on objects show the same frame.
    if (global.MK && global.MK.onFrame) global.MK.onFrame(rig.update);
    return rig;
  };

  // A container that moves several children together (e.g. a curved wall you can spin).
  C3.group = function (rig, p = {}) {
    const g = document.createElement('div');
    g.style.width = '0'; g.style.height = '0';
    rig.world.appendChild(g);
    return rig.add(g, { dof: false, ...p });
  };

  /*
   * Curved screen wall: an image (or several, tiled) mapped onto a convex vertical cylinder, built from
   * thin strips. src can be a URL or a data: URI (see C3.panelSVG). Returns the group; spin it with
   * tl.to(group, { ry: -30, onUpdate: rig.update }) to "pan along the screen".
   */
  C3.curvedWall = function (rig, src, opts = {}) {
    const { width = 1600, height = 900, radius = 1400, strips = 48, x = 0, y = 0, z = 0, border = null, glow = null } = opts;
    // The group sits on the cylinder axis, so spinning it pans along the surface; the front is at z.
    const g = C3.group(rig, { x, y, z: z - radius });
    const sw = width / strips;
    const arc = width / radius; // radians covered
    for (let i = 0; i < strips; i++) {
      const s = document.createElement('div');
      const th = ((i + 0.5) / strips - 0.5) * arc;
      Object.assign(s.style, {
        width: `${sw + 0.8}px`, height: `${height}px`,
        backgroundImage: `url("${src}")`, backgroundSize: `${width}px ${height}px`, backgroundPosition: `${-i * sw}px 0`,
      });
      if (border) { s.style.borderTop = border; s.style.borderBottom = border; }
      if (i === 0 && border) s.style.borderLeft = border;
      if (i === strips - 1 && border) s.style.borderRight = border;
      if (glow) s.style.boxShadow = glow;
      g.el.appendChild(s);
      const o = { el: s, x: Math.sin(th) * radius, y: 0, z: Math.cos(th) * radius, ry: (th * 180) / Math.PI, rx: 0, rz: 0, s: 1 };
      s.style.position = 'absolute';
      s.style.left = `${-sw / 2}px`; s.style.top = `${-height / 2}px`;
      s.style.backfaceVisibility = 'hidden';
      s.style.transform = `translate3d(${o.x}px,0,${o.z}px) rotateY(${o.ry}deg)`;
    }
    g.width = width; g.height = height; g.radius = radius;
    // Rotating the group by `deg` brings content at arc-length radius*deg into the centre.
    g.panTo = (px) => -((px / radius) * 180) / Math.PI; // px offset from centre -> group ry
    return g;
  };

  // Make a UI-mock panel as an SVG data URI (no external assets). blocks: [{x,y,w,h,fill,r,text,size,color,weight}]
  C3.panelSVG = function (w, h, bg, blocks = []) {
    const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
    const parts = blocks.map((b) =>
      b.text != null
        ? `<text x="${b.x}" y="${b.y}" font-family="${b.font || 'Inter, Arial, sans-serif'}" font-size="${b.size || 32}" font-weight="${b.weight || 600}" fill="${b.color || '#111'}" text-anchor="${b.anchor || 'start'}" letter-spacing="${b.ls || 0}">${esc(b.text)}</text>`
        : `<rect x="${b.x}" y="${b.y}" width="${b.w}" height="${b.h}" rx="${b.r || 0}" fill="${b.fill || '#ddd'}" ${b.stroke ? `stroke="${b.stroke}" stroke-width="${b.sw || 2}"` : ''}/>`
    );
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><rect width="${w}" height="${h}" fill="${bg}"/>${parts.join('')}</svg>`;
    return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
  };

  /* ---------- atmosphere ---------- */

  // Glowing sinuous neon tube across the frame. Tween wave.phase / wave.amp with onUpdate: wave.draw.
  C3.neonWave = function (svg, opts = {}) {
    svg = $(svg);
    const { color = '#FF5A1F', width = 1920, height = 1080, y = 540, amp = 40, freq = 3.2, thickness = 10 } = opts;
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    svg.setAttribute('preserveAspectRatio', 'none');
    svg.innerHTML = `
      <defs><filter id="nw-glow" x="-20%" y="-200%" width="140%" height="500%"><feGaussianBlur stdDeviation="${thickness * 2.2}"/></filter>
      <filter id="nw-soft" x="-20%" y="-200%" width="140%" height="500%"><feGaussianBlur stdDeviation="${thickness * 0.5}"/></filter></defs>
      <path class="halo" fill="none" stroke="${color}" stroke-width="${thickness * 5}" opacity=".55" filter="url(#nw-glow)"/>
      <path class="tube" fill="none" stroke="${color}" stroke-width="${thickness * 1.6}" filter="url(#nw-soft)"/>
      <path class="core" fill="none" stroke="#FFE2D2" stroke-width="${thickness * 0.45}" opacity=".9"/>`;
    const paths = [...svg.querySelectorAll('path')];
    const wave = { phase: 0, amp, y, freq };
    wave.draw = () => {
      let d = '';
      for (let i = 0; i <= 96; i++) {
        const x = (i / 96) * (width + 200) - 100;
        const k = (x / width) * Math.PI * 2 * wave.freq;
        const yy = wave.y + Math.sin(k + wave.phase) * wave.amp + Math.sin(k * 0.47 - wave.phase * 0.6) * wave.amp * 0.45;
        d += `${i ? 'L' : 'M'}${x.toFixed(1)} ${yy.toFixed(1)} `;
      }
      paths.forEach((p) => p.setAttribute('d', d));
    };
    wave.draw();
    return wave;
  };

  // Dashed design-tool guide lines that slide in to frame a rectangle (x, y, w, h in stage px).
  C3.guides = function (container, rect, opts = {}) {
    container = $(container);
    const { color = 'rgba(255,255,255,.75)', dash = 10 } = opts;
    const mk = (vertical, pos) => {
      const l = document.createElement('div');
      Object.assign(l.style, {
        position: 'absolute', [vertical ? 'left' : 'top']: `${pos}px`, [vertical ? 'top' : 'left']: '0',
        [vertical ? 'width' : 'height']: '0', [vertical ? 'height' : 'width']: '100%',
        [vertical ? 'borderLeft' : 'borderTop']: `2px dashed ${color}`, opacity: 0,
      });
      l.dataset.vertical = vertical ? '1' : '';
      container.appendChild(l);
      return l;
    };
    const lines = [mk(true, rect.x), mk(true, rect.x + rect.w), mk(false, rect.y), mk(false, rect.y + rect.h)];
    const tl = gsap.timeline();
    lines.forEach((l, i) => {
      const v = l.dataset.vertical;
      tl.fromTo(l, { opacity: 0, [v ? 'x' : 'y']: (i % 2 ? 1 : -1) * 260 }, { opacity: 1, [v ? 'x' : 'y']: 0, duration: 0.55, ease: 'expo.out' }, i * 0.06);
    });
    tl.lines = lines;
    return tl;
  };

  // Text that resolves out of random glyphs (deterministic: depends only on progress).
  C3.scramble = function (el, finalText, opts = {}) {
    el = $(el);
    const { duration = 0.6, chars = 'abcdefghijklmnopqrstuvwxyz#%&*' } = opts;
    const o = { p: 0 };
    const hash = (i, f) => Math.abs(Math.sin(i * 127.1 + f * 311.7) * 43758.5453) % 1;
    return gsap.timeline().to(o, {
      p: 1, duration, ease: 'none',
      onUpdate: () => {
        const n = finalText.length, done = Math.floor(o.p * n), f = Math.floor(o.p * 24);
        el.textContent = [...finalText].map((ch, i) => (i < done || ch === ' ' ? ch : chars[Math.floor(hash(i, f) * chars.length)])).join('');
      },
      onComplete: () => (el.textContent = finalText),
    });
  };

  // One- or two-frame colour-invert flash on a hard cut (the reference does this on every big cut).
  C3.invertFlash = function (tl, target, at, frames = 2, fps = 30) {
    tl.set($(target), { filter: 'invert(1) hue-rotate(180deg)' }, at);
    tl.set($(target), { filter: 'none' }, at + frames / fps);
  };

  // Whip pan: translate hard with blur; cut on the blurriest frame.
  C3.whip = function (el, opts = {}) {
    const { x = -1400, duration = 0.32, blur = 28 } = opts;
    return gsap.timeline().to($(el), { x, filter: `blur(${blur}px)`, duration, ease: 'power3.in' });
  };

  /* ---------- brand-glow phone reel (references/style-brand-glow-reel.md) ---------- */

  // Big soft brand-colour light blob. Position it with x/y (centre, stage px) and tween x/y/scale/opacity.
  C3.glow = function (el, opts = {}) {
    el = $(el);
    const { color = '#1ED760', size = 1100, blur = 110, x = 960, y = 540, strength = 0.85 } = opts;
    Object.assign(el.style, {
      position: 'absolute', width: `${size}px`, height: `${size}px`, left: `${-size / 2}px`, top: `${-size / 2}px`, borderRadius: '50%',
      background: `radial-gradient(circle, ${color} 0%, ${color}cc 22%, ${color}55 48%, transparent 70%)`, filter: `blur(${blur}px)`, opacity: strength, pointerEvents: 'none',
    });
    gsap.set(el, { x, y });
    return el;
  };

  // Quick brightness swell on a hit (logo land, notification).
  C3.pulse = function (el, opts = {}) {
    const { scale = 1.18, duration = 0.6 } = opts;
    return gsap.timeline().to($(el), { scale: `*=${scale}`, duration: duration * 0.3, ease: 'power2.out' }).to($(el), { scale: `/=${scale}`, duration: duration * 0.7, ease: 'power2.inOut' });
  };

  /*
   * A 3D phone: an extruded rounded slab (stacked layers give real thickness when it turns) with any
   * element as its live screen. Returns the rig object (tween x/y/z/rx/ry/rz/s on it).
   */
  C3.phone = function (rig, opts = {}) {
    const { w = 390, h = 844, depth = 30, radius = 62, layers = 16, bezel = 13, screen = null,
      frame = ['#8E9BAE', '#3B4250'], ...pos } = opts;
    const g = C3.group(rig, pos);
    for (let i = layers - 1; i >= 0; i--) {
      const L = document.createElement('div');
      const t = i / (layers - 1); // 0 = front face, 1 = back
      const edge = i === 0 || i === layers - 1;
      Object.assign(L.style, {
        position: 'absolute', left: `${-w / 2}px`, top: `${-h / 2}px`, width: `${w}px`, height: `${h}px`, borderRadius: `${radius}px`,
        background: edge ? '#05060a' : `linear-gradient(135deg, ${frame[0]}, ${frame[1]} 55%, ${frame[0]})`,
        transform: `translateZ(${-t * depth}px)`, backfaceVisibility: 'visible',
        boxShadow: edge ? `inset 0 0 0 3px ${frame[0]}` : 'none',
      });
      if (i === layers - 1) L.style.background = `linear-gradient(160deg, #1b1f27, #0b0d12 60%, #232833)`;
      g.el.appendChild(L);
      if (i === 0 && screen) {
        const s = $(screen);
        Object.assign(s.style, { position: 'absolute', left: `${bezel}px`, top: `${bezel}px`, width: `${w - bezel * 2}px`, height: `${h - bezel * 2}px`,
          borderRadius: `${radius - bezel}px`, overflow: 'hidden', transform: 'translateZ(0.5px)' });
        L.appendChild(s);
        const island = document.createElement('div');
        Object.assign(island.style, { position: 'absolute', left: '50%', top: `${bezel + 12}px`, width: '118px', height: '34px', marginLeft: '-59px', borderRadius: '20px', background: '#000', transform: 'translateZ(1px)' });
        L.appendChild(island);
        g.island = island;
      }
    }
    g.width = w; g.height = h;
    return g;
  };

  // Warp an element (w x h) into a quadrilateral, e.g. a mockup PNG's screen corners from mockups.json.
  // quad = { tl:[x,y], tr:[x,y], br:[x,y], bl:[x,y] } in the element's parent coordinates.
  C3.fitQuad = function (el, w, h, quad) {
    el = $(el);
    const src = [[0, 0], [w, 0], [w, h], [0, h]];
    const dst = [quad.tl, quad.tr, quad.br, quad.bl];
    // Solve the 8 homography coefficients: [a b c d e f g h] with x' = (ax+by+c)/(gx+hy+1), y' = (dx+ey+f)/(gx+hy+1)
    const A = [], B = [];
    for (let i = 0; i < 4; i++) {
      const [x, y] = src[i], [X, Y] = dst[i];
      A.push([x, y, 1, 0, 0, 0, -x * X, -y * X]); B.push(X);
      A.push([0, 0, 0, x, y, 1, -x * Y, -y * Y]); B.push(Y);
    }
    for (let c = 0; c < 8; c++) { // Gaussian elimination with partial pivoting
      let p = c;
      for (let r = c + 1; r < 8; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
      [A[c], A[p]] = [A[p], A[c]]; [B[c], B[p]] = [B[p], B[c]];
      for (let r = c + 1; r < 8; r++) {
        const f = A[r][c] / A[c][c];
        for (let k = c; k < 8; k++) A[r][k] -= f * A[c][k];
        B[r] -= f * B[c];
      }
    }
    const X = new Array(8);
    for (let r = 7; r >= 0; r--) { let s = B[r]; for (let k = r + 1; k < 8; k++) s -= A[r][k] * X[k]; X[r] = s / A[r][r]; }
    const [a, b, c, d, e, f, g, hh] = X;
    Object.assign(el.style, { position: 'absolute', left: '0', top: '0', width: `${w}px`, height: `${h}px`, transformOrigin: '0 0',
      transform: `matrix3d(${a},${d},0,${g},${b},${e},0,${hh},0,0,1,0,${c},${f},0,1)` });
    return el;
  };

  // Logo build: icon pops with a thin ring pulse, then the wordmark slides out from behind it.
  // Markup: <div class="logo"> <img class="icon"> <div class="wclip"><span class="word">Name</span></div> </div>, ring: an empty circle div.
  C3.logoReveal = function (icon, word, ring, opts = {}) {
    icon = $(icon); word = $(word); ring = $(ring);
    const clip = word.parentElement;
    const full = word.scrollWidth + (opts.gap ?? 0);
    gsap.set(clip, { width: 0, overflow: 'hidden', display: 'inline-block', verticalAlign: 'middle' });
    const tl = gsap.timeline();
    tl.fromTo(icon, { scale: 0, opacity: 0, filter: 'blur(10px)' }, { scale: 1, opacity: 1, filter: 'blur(0px)', duration: 0.55, ease: 'back.out(2.2)' }, 0);
    if (ring) tl.fromTo(ring, { scale: 0.6, opacity: 0.9 }, { scale: 2.4, opacity: 0, duration: 0.9, ease: 'power2.out', immediateRender: false }, 0.12);
    tl.to(clip, { width: full, duration: 0.7, ease: 'expo.out' }, opts.wordAt ?? 0.55);
    tl.fromTo(word, { x: -60, filter: 'blur(12px)', opacity: 0 }, { x: 0, filter: 'blur(0px)', opacity: 1, duration: 0.7, ease: 'expo.out' }, opts.wordAt ?? 0.55);
    return tl;
  };

  // Wide-tracked word that tightens (pair with MK.wordsIn on the rest of the line).
  C3.track = function (el, opts = {}) {
    const { from = '0.55em', to = '-0.02em', duration = 0.9 } = opts;
    return gsap.timeline().fromTo($(el), { letterSpacing: from, opacity: 0, filter: 'blur(6px)' }, { letterSpacing: to, opacity: 1, filter: 'blur(0px)', duration, ease: 'expo.out' });
  };

  // A line of text collapses into a glowing horizontal light streak.
  C3.streak = function (text, line, opts = {}) {
    const { duration = 0.35, width = 420 } = opts;
    return gsap.timeline()
      .fromTo($(text), { filter: 'blur(0px) brightness(1)' }, { scaleX: 0.15, scaleY: 0.35, opacity: 0, filter: 'blur(14px) brightness(2)', duration, ease: 'power3.in', immediateRender: false }, 0)
      .fromTo($(line), { width: width * 1.6, opacity: 0, scaleY: 0.5 }, { width, opacity: 1, scaleY: 1, duration, ease: 'power3.in' }, 0);
  };

  // The streak expands vertically into a pill (notification) with a ring flash; the line fades.
  C3.streakToPill = function (line, pill, opts = {}) {
    const { duration = 0.5, ring = null } = opts;
    const tl = gsap.timeline()
      .to($(line), { opacity: 0, scaleX: 1.3, duration: duration * 0.6, ease: 'power2.out' }, 0)
      .fromTo($(pill), { scaleY: 0.06, scaleX: 0.85, opacity: 0, filter: 'blur(6px) brightness(1.6)' }, { scaleY: 1, scaleX: 1, opacity: 1, filter: 'blur(0px) brightness(1)', duration, ease: 'expo.out' }, 0.05);
    if (ring) tl.fromTo($(ring), { scale: 0.7, opacity: 0.9 }, { scale: 1.5, opacity: 0, duration: 0.8, ease: 'power2.out', immediateRender: false }, 0.05);
    return tl;
  };

  // App-open: the tapped icon grows to fill the frame, then the app UI fades in over it.
  C3.appOpen = function (icon, ui, opts = {}) {
    icon = $(icon);
    const { duration = 0.55, stageW = 1920, stageH = 1080 } = opts;
    const r = icon.getBoundingClientRect();
    const k = MKscale();
    const cover = (Math.hypot(stageW, stageH) / (r.width / k)) * 1.05;
    return gsap.timeline()
      .to(icon, { scale: cover, borderRadius: '6px', duration, ease: 'power3.in' }, 0)
      .fromTo($(ui), { opacity: 0, scale: 1.08, filter: 'blur(12px)' }, { opacity: 1, scale: 1, filter: 'blur(0px)', duration: 0.6, ease: 'expo.out' }, duration * 0.8);
  };
  const MKscale = () => (global.MK && global.MK.stageScale ? global.MK.stageScale() : 1);

  // Logo-mask wipe: reveal `scene` through a logo-shaped matte that grows from logo size to beyond the frame.
  // maskUrl: an image with alpha (PNG/SVG). Set the scene visible before calling.
  C3.maskWipe = function (scene, maskUrl, opts = {}) {
    scene = $(scene);
    const { from = 140, to = 9000, duration = 0.8, cx = '50%', cy = '50%', ease = 'power3.in' } = opts;
    const o = { s: from };
    const set = () => {
      const v = `${o.s}px ${o.s}px`;
      scene.style.webkitMaskSize = v; scene.style.maskSize = v;
    };
    Object.assign(scene.style, { webkitMaskImage: `url("${maskUrl}")`, maskImage: `url("${maskUrl}")`, webkitMaskRepeat: 'no-repeat', maskRepeat: 'no-repeat',
      webkitMaskPosition: `${cx} ${cy}`, maskPosition: `${cx} ${cy}` });
    set();
    return gsap.timeline().to(o, { s: to, duration, ease, onUpdate: set, onStart: set,
      onComplete: () => { scene.style.webkitMaskImage = 'none'; scene.style.maskImage = 'none'; } });
  };

  global.C3 = C3;
})(window);
