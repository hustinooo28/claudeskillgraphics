# Signature techniques

Each move lists where it appears in the references (A = ride-hailing ad, B = motivational reel, C = "Apple-style" teaser, D = productivity teaser; see `breakdowns.md`), what it does in measured timings, and the `motion-kit.js` call that builds it.

## Typography

### 1. Word-by-word grow-in — `MK.wordsIn(el, { from: 'small', tint })`
A 0.1–1.0 s, C 0.0–0.3 s, D 6.8–7.3 s.
Each word starts **tiny (≈40 %), blurred (≈14 px) and transparent**, then grows into place with `expo.out` over ~0.6 s, stagger 0.12–0.2 s. In A the words begin in the brand green and settle to near-black (`tint`). The finished line is readable by ~1.0 s.
Gotcha: splitting wraps every word in an `inline-block`, and a parent's `text-decoration` (accent underline) does not reach inside inline-blocks. Put the underline class on an inner element and split its wrapper: `<span class="accw"><span class="acc">peso.</span></span>` → `MK.wordsIn('.accw')`.
Variants: `from: 'below'` for sub-lines (they rise 60 px), `from: 'drop'` for C's falling, vertically smeared words.

### 2. Word-by-word exit — `MK.wordsOut(el)`
A 1.5–1.9 s: words leave left to right, drifting left, turning grey, blurring and shrinking, stagger ~0.05 s, `power3.in`, 0.35–0.4 s. Never fade a whole line at once.

### 3. Sub-line trickle — `MK.wordsIn(sub, { from: 'below', stagger: 0.1, blur: 8 })`
C 1.1–1.9 s: a light-grey sub-line ("Apple Style Motion Graphics") appears word by word *under* the landed headline.

### 4. Letter typing — `MK.typeIn(el, { style: 'caret' | 'pop' })`
- `caret`: search fields and UI copy at 12–16 chars/s (A 6.9–7.5 s, "Cari lokasi tujuan").
- `pop`: a wordmark's letters each grow from tiny, 1/16 s apart (A 2.6–3.0 s, "gojek").

### 5. Kinetic push — `MK.pushIn(el, { scale: 1.9 })`
D 7.8–8.9 s: after a line lands, the camera **snaps** in ~2× in 0.3 s (`expo.out`), part of the line leaves frame, then it keeps drifting slowly. The exit is a fast zoom-out with blur.

### 6. Mixed-scale emphasis line (static layout, animated with wordsIn)
B 4.0–4.5 s and 10.5–11.5 s: "here is the **truth**", "that's what builds **success**". The key word is 2–3× bigger, the small words sit on its cap line, sizes alternate across the line.

### 7. Glitch into a dark shot — `MK.glitchText(el)`
D 9.2–9.7 s: a hard cut to near-black with scanlines; the line arrives with an RGB split and settles in 6 steps. Use it once, for the "problem" beat.

## Elements

### 8. Widget drop with settle — `MK.popIn(el)`
C 2.4–2.8 s: the card rises from below the frame, rotated about −10°, scaled ~0.7 and blurred, then settles with a small overshoot in ~0.45 s (`back.out(1.3)`). Its content keeps animating after it lands (a ring timer counting 19:25 → 19:24, done with `MK.counter`).

### 9. List cascade — `MK.cascade(cards)`
A 7.0–7.5 s: cards slide up 50 px from blur, stagger 0.08 s, and keep arriving while the search text types.

### 10. Depth-of-field focus + cursor click — `MK.focus(cards, i)` + `MK.cursorClick(cursor, x, y)`
A 7.7–8.7 s: the list scrolls, the hand cursor reaches the chosen row, the row scales ~1.25× and every other row blurs about 7 px and dims. The click is a quick squash: scale 0.82 then back with `back.out`.

### 11. Design-tool selection box — `MK.selectionBox(el)` + cursor
B 0.3–1.5 s, 6.5–8.0 s: an arrow cursor drags out a dashed bounding box with corner handles around the text, as if in Figma. Text inside reveals word by word as the box grows.

### 12. Radial burst of cards — `MK.burst(cards, { cx, cy })`
D 5.1–5.5 s: website cards explode outward from the app icon at centre, blurred while moving, landing at scattered positions with varied sizes.

### 13. Giant out-of-focus foreground shapes — CSS + `MK.drift`
B throughout: huge black blob/asterisk shapes at 10–20 px blur, partly off-frame, slowly rotating. They give constant parallax depth behind clean type. Animate with a long linear rotation (`MK.drift(el, { rotation: 25, duration: shotLength })`).

### 14. Object drop onto a dot grid
B 1.6–2.5 s: a 3D-looking object (a pill capsule) falls in with heavy motion blur and lands on a faint dot grid, then a dotted orbit circle draws around it (`MK.drawStroke` on a dashed circle). Use a PNG with a transparent background or simple CSS 3D for the object.

## Lines and shapes

### 15. Logo mark stroke draw — `MK.drawStroke(ring)` plus a core `scale` pop
A 2.7–3.1 s and 10.7–11.1 s: a dot appears, then the ring sweeps around it in ~0.4–0.6 s. The same draw is reused for the end card.

### 16. Camera-follow connector line — `MK.drawStroke(path)` + `MK.cameraTo(world, x, y)`
D 3.0–5.0 s: a blue line draws from one app icon to the next. The camera (a large "world" div) pans along with `expo.inOut` and each icon pops as the line reaches it. Lay the icons out on a big canvas and pan to each in turn.

### 17. Swoosh reveal — `MK.swoosh(svg)`
A 6.0–7.0 s: a fat, round-capped brand-coloured brush stroke sweeps diagonally across the frame. It carries the next element inside it: a map card with a blue glow rides the stroke, then morphs into the search bar. The stroke's tail erases after it, so it works as a transition that covers a cut.

## Transitions

### 18. Zoom-through — `MK.zoomThrough(el)` → next shot
A 3.6–4.4 s, C 0.3–0.5 s: scale ×3 with 14 px blur, `power3.in`, 0.5 s. Cut on the blurriest frame. The next shot often enters with `MK.zoomFrom`.

### 19. Pill → circle → full-frame wipe — `MK.pillToWipe(pill)`
A 9.4–10.6 s: the CTA pill ("Order Sekarang →") collapses from the left into a circle (0.35 s). After a beat the circle scales past the frame edges (0.4 s, `power3.in`), so the frame becomes the pill's colour and the end logo starts on it.

### 20. Hard cut to brand colour
A 8.8 s: cut straight from a light UI shot to a full-bleed brand-green frame holding the CTA. This is the only hard cut in A, and it lands on the call to action.

### 21. Shape-masked scene change
C 2.3 s, B 1.6 s: the next scene starts inside a moving card or blob (the widget card becomes the new frame). Build it by animating a `clip-path: inset()` / `circle()` on the incoming shot.

### 22. End card
Every reference ends on a held logo of 1.2–2.5 s, light or dark, with a soft glow (D: white wordmark on black with a blurred white halo, `text-shadow: 0 0 40px rgba(255,255,255,.6)`).
