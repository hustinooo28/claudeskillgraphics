/* LK — tiny shared helpers for the launch beats (loaded once by the host, before any beat mounts).
   Everything is deterministic: DOM is built at init from fixed tables, no randomness, no clocks. */
window.LK = (function () {
  const NS = "http://www.w3.org/2000/svg";
  const F = (n) => n / 60; // frames (60 fps) -> seconds
  const dims = (root) => {
    const W = +root.dataset.width, H = +root.dataset.height;
    return { W, H, land: W > H };
  };
  const UNITLESS = new Set(["lineHeight", "fontWeight", "opacity", "zIndex", "flex", "order"]);
  // Absolutely positioned element. s = style object (numbers -> px).
  const el = (parent, tag, cls, s, text) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (s) for (const k in s) e.style[k] = typeof s[k] === "number" && !UNITLESS.has(k) ? s[k] + "px" : s[k];
    if (text != null) e.textContent = text;
    parent.appendChild(e);
    return e;
  };
  // Split text into masked units; returns the inner spans to animate.
  const split = (node, mode) => {
    const t = node.textContent; node.textContent = "";
    const parts = mode === "char" ? [...t] : t.split(" ");
    return parts.map((p, i) => {
      const o = document.createElement("span"); o.className = mode === "char" ? "ch" : "wd";
      const n = document.createElement("span"); n.textContent = p === " " ? " " : p;
      o.appendChild(n); node.appendChild(o);
      if (mode !== "char" && i < parts.length - 1) node.appendChild(document.createTextNode(" "));
      return n;
    });
  };
  // Full-frame SVG layer for construction guides.
  const svg = (parent, W, H) => {
    const s = document.createElementNS(NS, "svg");
    s.setAttribute("width", W); s.setAttribute("height", H); s.setAttribute("viewBox", `0 0 ${W} ${H}`);
    s.style.position = "absolute"; s.style.left = "0"; s.style.top = "0"; s.style.overflow = "visible";
    parent.appendChild(s);
    return s;
  };
  const line = (s, x1, y1, x2, y2, stroke, dash) => {
    const l = document.createElementNS(NS, "line");
    Object.entries({ x1, y1, x2, y2 }).forEach(([k, v]) => l.setAttribute(k, v));
    l.setAttribute("stroke", stroke); l.setAttribute("stroke-width", "1.5");
    if (dash !== false) l.setAttribute("stroke-dasharray", "5 7");
    s.appendChild(l); return l;
  };
  const dot = (s, cx, cy, r, fill) => {
    const c = document.createElementNS(NS, "circle");
    c.setAttribute("cx", cx); c.setAttribute("cy", cy); c.setAttribute("r", r); c.setAttribute("fill", fill);
    s.appendChild(c); return c;
  };
  const ring = (s, cx, cy, r, stroke, dash) => {
    const c = document.createElementNS(NS, "circle");
    c.setAttribute("cx", cx); c.setAttribute("cy", cy); c.setAttribute("r", r);
    c.setAttribute("fill", "none"); c.setAttribute("stroke", stroke); c.setAttribute("stroke-width", "1.5");
    if (dash) c.setAttribute("stroke-dasharray", dash);
    s.appendChild(c); return c;
  };
  // Draw a guide line out from its start point (attr tween on x2/y2).
  const draw = (tl, l, at, dur, ease) => {
    const x1 = +l.getAttribute("x1"), y1 = +l.getAttribute("y1");
    const x2 = +l.getAttribute("x2"), y2 = +l.getAttribute("y2");
    tl.fromTo(l, { attr: { x2: x1, y2: y1 } }, { attr: { x2, y2 }, duration: dur, ease: ease || "expo.out" }, at);
  };
  // Live only inside [a, b) (seek-safe: autoAlpha keeps visibility inherited from the slot).
  const live = (tl, node, a, b) => {
    if (a > 0) tl.set(node, { autoAlpha: 0 }, 0).set(node, { autoAlpha: 1 }, a);
    if (b != null) tl.set(node, { autoAlpha: 0 }, b);
  };
  const C = { ink: "#080d22", paper: "#f4f6fc", brand: "#526ff2", accent: "#d6b05c" }; // = shared.css tokens
  // REF_C entrance: arrives overexposed and blurred, cools into its real look.
  const hot = (tl, els, at, dur, opts) => {
    const o = Object.assign({ b: 14, br: 3.2, stagger: 0 }, opts || {});
    const from = { opacity: 0, filter: `brightness(${o.br}) blur(${o.b}px)` };
    const to = { opacity: 1, filter: "brightness(1) blur(0px)", duration: dur, ease: "expo.out", stagger: o.stagger };
    // only touch transforms that were asked for, so hot() can layer over other moves
    ["x", "y", "scale"].forEach((k) => { if (o[k] != null) { from[k] = o[k]; to[k] = k === "scale" ? 1 : 0; } });
    tl.fromTo(els, from, to, at);
  };
  // REF_C exit: drifts, blurs and dims away into the dark.
  const away = (tl, els, at, dur, opts) => {
    const o = Object.assign({ b: 12, y: -60, x: 0, scale: 1 }, opts || {});
    tl.fromTo(els, { opacity: 1, filter: "blur(0px)" },
      { opacity: 0, filter: `blur(${o.b}px)`, y: `+=${o.y}`, x: `+=${o.x}`, scale: o.scale, duration: dur, ease: "power2.in", immediateRender: false }, at);
  };
  // Typing with REF_C's lit "current word": chars appear at cps; the word being typed glows yellow, then cools to white.
  const type = (tl, node, at, cps, opts) => {
    const o = Object.assign({ lit: "#ffc61a", base: "#f3f6ff", litShadow: "0 0 10px rgba(255,200,40,.85), 0 0 26px rgba(255,170,0,.5)", keep: null }, opts || {});
    const t = node.textContent; node.textContent = "";
    // chars live inside per-word nowrap wrappers so lines only break between words
    const chars = []; let wrap = null;
    [...t].forEach((c) => {
      const s = document.createElement("span"); s.className = "ch"; s.textContent = c;
      if (c === " ") { node.appendChild(s); wrap = null; }
      else { if (!wrap) { wrap = document.createElement("span"); wrap.style.display = "inline-block"; wrap.style.whiteSpace = "nowrap"; node.appendChild(wrap); } wrap.appendChild(s); }
      chars.push(s);
    });
    const words = []; let cur = [];
    chars.forEach((s, i) => { if (t[i] === " ") { if (cur.length) words.push(cur); cur = []; } else cur.push(i); });
    if (cur.length) words.push(cur);
    const tAt = (i) => at + i / cps;
    tl.set(chars, { opacity: 0, color: o.lit, textShadow: o.litShadow }, 0);
    chars.forEach((s, i) => tl.set(s, { opacity: 1 }, tAt(i)));
    words.forEach((w, k) => {
      const cool = k + 1 < words.length ? tAt(words[k + 1][0]) : tAt(chars.length) + 0.35;
      const ws = w.map((i) => chars[i]);
      if (o.keep && o.keep(t.slice(w[0], w[w.length - 1] + 1))) return; // stays lit
      tl.set(ws, { color: o.base, textShadow: "0 0 10px rgba(90,150,255,.45)" }, cool);
    });
    return { chars, end: tAt(chars.length) };
  };
  const svgIcon = (parent, paths, size, stroke) => {
    const s = document.createElementNS(NS, "svg");
    s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("width", size); s.setAttribute("height", size);
    s.setAttribute("fill", "none"); s.setAttribute("stroke", stroke || "currentColor"); s.setAttribute("stroke-width", "2");
    s.setAttribute("stroke-linecap", "round"); s.setAttribute("stroke-linejoin", "round");
    paths.forEach((d) => {
      let e;
      if (d.startsWith("circle:")) { const [cx, cy, r] = d.slice(7).split(","); e = document.createElementNS(NS, "circle"); e.setAttribute("cx", cx); e.setAttribute("cy", cy); e.setAttribute("r", r); }
      else { e = document.createElementNS(NS, "path"); e.setAttribute("d", d); }
      s.appendChild(e);
    });
    parent.appendChild(s); return s;
  };
  const ICON = {
    records: ["M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z", "M14 2v6h6", "M16 13H8", "M16 17H8"],
    transparency: ["M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z", "circle:12,12,3"],
    inquiry: ["M7.9 20A9 9 0 1 0 4 16.1L2 22Z"],
    council: ["M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2", "circle:9,7,4", "M22 21v-2a4 4 0 0 0-3-3.87", "M16 3.13a4 4 0 0 1 0 7.75"],
    updates: ["M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9", "M10.3 21a1.94 1.94 0 0 0 3.4 0"],
    search: ["circle:11,11,8", "m21 21-4.3-4.3"],
    send: ["m5 12 7-7 7 7", "M12 19V5"],
    plus: ["M12 5v14", "M5 12h14"],
  };
  // Pointer cursor (white with a dark outline), tip at (0,0).
  const cursor = (parent) => {
    const s = document.createElementNS(NS, "svg");
    s.setAttribute("viewBox", "0 0 28 40"); s.setAttribute("width", 34); s.setAttribute("height", 48);
    s.style.position = "absolute"; s.style.left = "0"; s.style.top = "0"; s.style.overflow = "visible";
    const p = document.createElementNS(NS, "path");
    p.setAttribute("d", "M2 2 L2 31 L9.5 24 L14.5 36 L19.5 34 L14.6 22.2 L24.5 22.2 Z");
    p.setAttribute("fill", "#ffffff"); p.setAttribute("stroke", "#05060b"); p.setAttribute("stroke-width", "2"); p.setAttribute("stroke-linejoin", "round");
    s.appendChild(p); parent.appendChild(s);
    s.style.filter = "drop-shadow(0 0 8px rgba(120,170,255,.6))";
    return s;
  };
  return { hot, away, type, svgIcon, ICON, cursor, C, F, dims, el, split, svg, line, dot, ring, draw, live };
})();
