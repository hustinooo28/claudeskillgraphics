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
  return { C, F, dims, el, split, svg, line, dot, ring, draw, live };
})();
