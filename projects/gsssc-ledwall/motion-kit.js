/*
 * motion-kit.js — reusable beats for the ui-promo-motion style.
 * Requires a global `gsap` (3.12+). Every helper returns a gsap.timeline()
 * so it can be placed on the master timeline: master.add(MK.wordsIn(el), 1.2)
 */
(function (global) {
  const gsap = global.gsap;
  const MK = {};

  MK.EASE = {
    out: 'expo.out',
    in: 'power3.in',
    inOut: 'expo.inOut',
    pop: 'back.out(1.6)',
    settle: 'back.out(1.3)',
    soft: 'power2.out',
  };

  const $ = (q, root = document) => (typeof q === 'string' ? root.querySelector(q) : q);
  const $$ = (q, root = document) =>
    typeof q === 'string' ? [...root.querySelectorAll(q)] : Array.isArray(q) ? q : q instanceof NodeList ? [...q] : [q];

  MK.$ = $;
  MK.$$ = $$;

  /* ---------- text splitting ---------- */

  // Wrap each word in <span class="w">. Child elements (e.g. <b class="accent">) count as one word each.
  MK.splitWords = function (el) {
    el = $(el);
    if (el.dataset.mkSplit === 'w') return [...el.querySelectorAll(':scope .w')];
    const frag = document.createDocumentFragment();
    [...el.childNodes].forEach((node) => {
      if (node.nodeType === 3) {
        node.textContent.split(/(\s+)/).forEach((part) => {
          if (!part) return;
          if (/^\s+$/.test(part)) frag.appendChild(document.createTextNode(' '));
          else {
            const s = document.createElement('span');
            s.className = 'w';
            s.textContent = part;
            frag.appendChild(s);
          }
        });
      } else {
        node.classList.add('w');
        frag.appendChild(node);
      }
    });
    el.innerHTML = '';
    el.appendChild(frag);
    el.dataset.mkSplit = 'w';
    return [...el.querySelectorAll(':scope .w')];
  };

  // Wrap each character in <span class="c">.
  MK.splitChars = function (el) {
    el = $(el);
    if (el.dataset.mkSplit === 'c') return [...el.querySelectorAll('.c')];
    const text = el.textContent;
    el.innerHTML = '';
    [...text].forEach((ch) => {
      const s = document.createElement('span');
      s.className = 'c';
      s.textContent = ch === ' ' ? ' ' : ch;
      el.appendChild(s);
    });
    el.dataset.mkSplit = 'c';
    return [...el.querySelectorAll('.c')];
  };

  /* ---------- typography ---------- */

  // Words grow out of blur, one by one. Measured: stagger 0.1–0.2, each ~0.6 s, expo.out.
  // opts.from: 'small' (scale up from ~0.4), 'below' (rise), 'drop' (fall with vertical blur)
  // opts.tint: start colour that settles to the element's own colour (ride-app ad: green → black).
  MK.wordsIn = function (el, opts = {}) {
    const { stagger = 0.14, duration = 0.65, from = 'small', blur = 14, tint = null } = opts;
    const words = MK.splitWords(el);
    const tl = gsap.timeline();
    gsap.set($(el), { opacity: 1 });
    const start = { opacity: 0, filter: `blur(${blur}px)` };
    if (from === 'small') Object.assign(start, { scale: 0.4, y: 10 });
    if (from === 'below') Object.assign(start, { y: 60 });
    if (from === 'drop') Object.assign(start, { y: -70, scaleY: 1.4 });
    words.forEach((w) => gsap.set(w, { display: 'inline-block', transformOrigin: '50% 70%' }));
    tl.fromTo(
      words,
      start,
      { opacity: 1, filter: 'blur(0px)', scale: 1, scaleY: 1, y: 0, duration, ease: MK.EASE.out, stagger },
      0
    );
    if (tint) {
      words.forEach((w, i) => {
        const final = getComputedStyle(w).color;
        tl.fromTo(w, { color: tint }, { color: final, duration: duration * 1.3, ease: 'power1.inOut' }, i * stagger);
      });
    }
    return tl;
  };

  // Words leave in sequence: drift, shrink, blur, fade.
  MK.wordsOut = function (el, opts = {}) {
    const { stagger = 0.05, duration = 0.4, x = -40, blur = 10 } = opts;
    const words = MK.splitWords(el);
    return gsap.timeline().to(words, {
      opacity: 0,
      x,
      scale: 0.9,
      filter: `blur(${blur}px)`,
      color: '#A1A1A6',
      duration,
      ease: MK.EASE.in,
      stagger,
    });
  };

  // Typing. style 'caret' = instant letters at cps; style 'pop' = letters grow from tiny (logo wordmark).
  MK.typeIn = function (el, opts = {}) {
    const { cps = 14, style = 'caret' } = opts;
    const chars = MK.splitChars(el);
    gsap.set($(el), { opacity: 1 });
    const tl = gsap.timeline();
    if (style === 'pop') {
      chars.forEach((c) => gsap.set(c, { display: 'inline-block', transformOrigin: '50% 80%' }));
      tl.fromTo(
        chars,
        { opacity: 0, scale: 0.2, filter: 'blur(6px)' },
        { opacity: 1, scale: 1, filter: 'blur(0px)', duration: 0.35, ease: MK.EASE.out, stagger: 1 / cps }
      );
    } else {
      tl.fromTo(chars, { opacity: 0 }, { opacity: 1, duration: 0.001, stagger: 1 / cps });
    }
    return tl;
  };

  // Kinetic push: snap-zoom into a line, then drift slowly (productivity teaser "progress slows").
  MK.pushIn = function (el, opts = {}) {
    const { scale = 1.9, duration = 0.35, drift = 0.08, hold = 1.0, x = 0 } = opts;
    return gsap
      .timeline()
      .to($(el), { scale, x, duration, ease: MK.EASE.out })
      .to($(el), { scale: scale * (1 + drift), x: x * 1.1, duration: hold, ease: 'none' });
  };

  // Count a number (timer widget "19:25 → 19:24", stats).
  MK.counter = function (el, from, to, opts = {}) {
    const { duration = 1, format = (v) => Math.round(v).toString() } = opts;
    const o = { v: from };
    el = $(el);
    return gsap.timeline().to(o, {
      v: to,
      duration,
      ease: 'power1.inOut',
      onUpdate: () => (el.textContent = format(o.v)),
    });
  };

  // Dark-shot glitch: RGB split + scanline jitter, settles to clean text.
  MK.glitchText = function (el, opts = {}) {
    const { duration = 0.5 } = opts;
    el = $(el);
    return gsap
      .timeline()
      .fromTo(
        el,
        { opacity: 0, x: -14, textShadow: '6px 0 rgba(255,0,80,.8), -6px 0 rgba(0,220,255,.8)', filter: 'blur(4px)' },
        {
          opacity: 1,
          x: 0,
          textShadow: '0px 0 rgba(255,0,80,0), 0px 0 rgba(0,220,255,0)',
          filter: 'blur(0px)',
          duration,
          ease: 'steps(6)',
        }
      );
  };

  /* ---------- elements ---------- */

  // Card/widget drops in rotated and blurred, settles with overshoot (tutorial-teaser timer widget).
  MK.popIn = function (el, opts = {}) {
    const { y = 260, rotation = -10, scale = 0.7, blur = 16, duration = 0.7, ease = MK.EASE.settle } = opts;
    return gsap
      .timeline()
      .fromTo($$(el), { opacity: 0, y, rotation, scale }, { opacity: 1, y: 0, rotation: 0, scale: 1, duration, ease, stagger: opts.stagger || 0 }, 0)
      .fromTo($$(el), { filter: `blur(${blur}px)` }, { filter: 'blur(0px)', duration: duration * 0.6, ease: 'power2.out', stagger: opts.stagger || 0 }, 0);
  };

  // List/cards cascade up into place.
  MK.cascade = function (els, opts = {}) {
    const { y = 50, stagger = 0.08, duration = 0.6, blur = 8 } = opts;
    return gsap.timeline().fromTo(
      $$(els),
      { opacity: 0, y, filter: `blur(${blur}px)` },
      { opacity: 1, y: 0, filter: 'blur(0px)', duration, ease: MK.EASE.out, stagger }
    );
  };

  // Cards burst outward from a centre point to their resting places (app-cloud shot).
  MK.burst = function (els, opts = {}) {
    const { cx = 0, cy = 0, stagger = 0.04, duration = 0.9, blur = 18 } = opts;
    const items = $$(els);
    const tl = gsap.timeline();
    items.forEach((it, i) => {
      const r = it.getBoundingClientRect();
      const stage = it.offsetParent ? it.offsetParent.getBoundingClientRect() : { left: 0, top: 0 };
      const k = MK.stageScale();
      const dx = cx - ((r.left - stage.left) / k + r.width / k / 2);
      const dy = cy - ((r.top - stage.top) / k + r.height / k / 2);
      tl.fromTo(
        it,
        { x: dx, y: dy, scale: 0.3, opacity: 0, filter: `blur(${blur}px)` },
        { x: 0, y: 0, scale: 1, opacity: 1, filter: 'blur(0px)', duration, ease: MK.EASE.out },
        i * stagger
      );
    });
    return tl;
  };

  // Depth-of-field focus: chosen item scales up, the rest blur and dim.
  MK.focus = function (els, index, opts = {}) {
    const { scale = 1.25, blur = 7, dim = 0.45, duration = 0.6 } = opts;
    const items = $$(els);
    const tl = gsap.timeline();
    items.forEach((it, i) => {
      if (i === index) tl.to(it, { scale, filter: 'blur(0px)', opacity: 1, zIndex: 5, duration, ease: MK.EASE.out }, 0);
      else tl.to(it, { scale: 0.96, filter: `blur(${blur}px)`, opacity: dim, duration, ease: MK.EASE.out }, 0);
    });
    return tl;
  };

  // Move a cursor element to (x, y) in stage px and click.
  MK.cursorClick = function (cursor, x, y, opts = {}) {
    const { duration = 0.6, click = true } = opts;
    const tl = gsap.timeline().to($(cursor), { x, y, duration, ease: 'power3.inOut' });
    if (click) tl.to($(cursor), { scale: 0.82, duration: 0.08, ease: 'power2.in' }).to($(cursor), { scale: 1, duration: 0.18, ease: MK.EASE.pop });
    return tl;
  };

  // Design-tool selection box drawn around an element (motivational reel): dashed frame + corner handles.
  MK.selectionBox = function (el, opts = {}) {
    const { pad = 18, duration = 0.45 } = opts;
    el = $(el);
    let box = el.querySelector(':scope > .mk-select');
    if (!box) {
      box = document.createElement('div');
      box.className = 'mk-select';
      box.innerHTML = '<i></i><i></i><i></i><i></i>';
      el.style.position = el.style.position || 'relative';
      el.appendChild(box);
    }
    gsap.set(box, { inset: -pad });
    return gsap
      .timeline()
      .fromTo(box, { clipPath: 'inset(0% 100% 100% 0%)', opacity: 1 }, { clipPath: 'inset(0% 0% 0% 0%)', duration, ease: 'power3.out' });
  };

  /* ---------- shapes & lines ---------- */

  // Draw an SVG stroke (path, circle, line). Set the path's stroke in markup.
  MK.drawStroke = function (path, opts = {}) {
    const { duration = 0.7, ease = 'power2.inOut', from = 0, to = 1 } = opts;
    path = $(path);
    const len = path.getTotalLength();
    gsap.set(path, { strokeDasharray: len, strokeDashoffset: len * (1 - from) });
    return gsap.timeline().to(path, { strokeDashoffset: len * (1 - to), duration, ease });
  };

  // Erase a drawn stroke from its start (the tail chases the head) — combine with drawStroke for a sweep.
  MK.eraseStroke = function (path, opts = {}) {
    const { duration = 0.5, ease = 'power2.in' } = opts;
    path = $(path);
    const len = path.getTotalLength();
    return gsap.timeline().to(path, { strokeDashoffset: -len, duration, ease });
  };

  // Brush swoosh transition: a fat round-capped stroke sweeps across the frame and out.
  // Needs an <svg class="mk-swoosh"><path/></svg> covering the stage; colour via CSS stroke.
  MK.swoosh = function (svg, opts = {}) {
    const { inDur = 0.35, hold = 0.35, outDur = 0.4 } = opts;
    const path = $('path', $(svg));
    return gsap
      .timeline()
      .set($(svg), { opacity: 1 })
      .add(MK.drawStroke(path, { duration: inDur, ease: 'power3.out' }))
      .add(MK.eraseStroke(path, { duration: outDur, ease: 'power3.in' }), `+=${hold}`);
  };

  /* ---------- transitions ---------- */

  // Exit a shot by flying through it.
  MK.zoomThrough = function (el, opts = {}) {
    const { scale = 3, blur = 14, duration = 0.5, origin = '50% 50%' } = opts;
    return gsap
      .timeline()
      .set($(el), { transformOrigin: origin })
      .to($(el), { scale, filter: `blur(${blur}px)`, duration, ease: MK.EASE.in })
      .to($(el), { opacity: 0, duration: duration * 0.35, ease: 'none' }, `-=${duration * 0.35}`);
  };

  // Enter a shot from far away.
  MK.zoomFrom = function (el, opts = {}) {
    const { scale = 0.4, blur = 14, duration = 0.75 } = opts;
    return gsap
      .timeline()
      .fromTo($(el), { scale, opacity: 0, filter: `blur(${blur}px)` }, { scale: 1, opacity: 1, filter: 'blur(0px)', duration, ease: MK.EASE.out });
  };

  // CTA pill collapses into a circle around its icon (label clipped away), then the circle grows to fill
  // the frame in the pill's own colour — the wipe into the next shot (ride-app ad, 9.4–10.6 s).
  // Markup: <div class="pill"><span class="label">Order now</span><span class="dot">→</span></div>
  MK.pillToWipe = function (pill, opts = {}) {
    const { collapse = 0.35, hold = 0.2, wipe = 0.4 } = opts;
    pill = $(pill);
    const dot = $('.dot', pill);
    const label = $('.label', pill);
    const h = pill.offsetHeight;
    const s = MK.stage();
    const cover = (Math.hypot(s.w, s.h) / h) * 1.15;
    return gsap
      .timeline()
      .to(label, { opacity: 0, x: -30, filter: 'blur(6px)', duration: collapse * 0.7, ease: MK.EASE.in }, 0)
      .to(pill, { width: h, paddingLeft: 0, paddingRight: 0, justifyContent: 'center', duration: collapse, ease: 'power3.inOut' }, 0)
      .to(dot, { scale: 0.5, opacity: 0, duration: wipe * 0.6, ease: MK.EASE.in }, `+=${hold}`)
      .to(pill, { scale: cover, duration: wipe, ease: MK.EASE.in }, '<');
  };

  // Pan a large "world" container so that (x, y) in world px sits at stage centre.
  MK.cameraTo = function (world, x, y, opts = {}) {
    const { duration = 0.8, scale = 1, ease = MK.EASE.inOut } = opts;
    const s = MK.stage();
    return gsap.timeline().to($(world), { x: s.w / 2 - x * scale, y: s.h / 2 - y * scale, scale, transformOrigin: '0 0', duration, ease });
  };

  // Slow life during holds.
  MK.drift = function (el, opts = {}) {
    const { scale = 1.04, rotation = 0, duration = 2 } = opts;
    return gsap.timeline().to($$(el), { scale, rotation: `+=${rotation}`, duration, ease: 'none' });
  };

  /* ---------- stage, preview and render plumbing ---------- */

  // Functions run after every seek (render) and every tick (preview), e.g. a 3D camera rig's update.
  MK._frameHooks = [];
  MK.onFrame = function (fn) {
    MK._frameHooks.push(fn);
  };
  const runHooks = (t) => MK._frameHooks.forEach((fn) => fn(t));

  MK.stage = function () {
    const st = $('#stage');
    return { el: st, w: st.offsetWidth, h: st.offsetHeight };
  };

  MK.stageScale = function () {
    const st = $('#stage');
    return st.getBoundingClientRect().width / st.offsetWidth;
  };

  // Show exactly one shot. Shots are absolutely positioned .shot elements inside #stage.
  MK.cut = function (tl, shot, at) {
    // Zero-duration sets revert correctly when seeking backwards in preview.
    tl.set($$('.shot'), { visibility: 'hidden' }, at).set($(shot), { visibility: 'visible' }, at);
  };

  // Register the master timeline. In render mode (?render) it stays paused for the renderer;
  // in preview it loops with keyboard scrubbing.
  MK.mount = function (tl) {
    const params = new URLSearchParams(location.search);
    const rendering = params.has('render');
    const st = $('#stage');
    tl.pause(0);
    global.__tl = tl;
    global.__duration = tl.duration();
    global.__size = { w: st.offsetWidth, h: st.offsetHeight };
    global.__seek = (t) => { tl.seek(t, false); runHooks(t); };
    global.__ready = document.fonts ? document.fonts.ready : Promise.resolve();
    if (rendering) {
      document.documentElement.classList.add('rendering');
      return;
    }
    const fit = () => {
      const k = Math.min(innerWidth / st.offsetWidth, innerHeight / st.offsetHeight);
      st.style.transform = `scale(${k})`;
      st.style.transformOrigin = '0 0';
      st.style.left = `${(innerWidth - st.offsetWidth * k) / 2}px`;
      st.style.top = `${(innerHeight - st.offsetHeight * k) / 2}px`;
    };
    fit();
    addEventListener('resize', fit);
    gsap.ticker.add(() => runHooks(tl.time()));
    global.__ready.then(() => {
      tl.seek(parseFloat(params.get('t')) || 0, false);
      tl.repeat(-1).repeatDelay(0.8).play();
    });
    addEventListener('keydown', (e) => {
      if (e.code === 'Space') tl.paused(!tl.paused());
      if (e.code === 'ArrowRight') tl.pause().seek(tl.time() + (e.shiftKey ? 1 : 1 / 30), false);
      if (e.code === 'ArrowLeft') tl.pause().seek(Math.max(0, tl.time() - (e.shiftKey ? 1 : 1 / 30)), false);
    });
  };

  global.MK = MK;
})(window);
